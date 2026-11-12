"""
FFIRE Twilio Communication & Identity Assurance Service.
Provides enterprise SMS Multi-Factor Authentication (MFA/2FA) and
real-time SMS incident alerting for critical fraud escalations.
"""

import os
import sys
import json
import time
import hmac
import hashlib
import secrets
import logging
from typing import Optional, Dict, Any, Tuple, List
import httpx

logger = logging.getLogger("ffire.twilio")

# In-memory OTP storage fallback if Redis is unavailable: {key: {"hash": str, "expires": float, "attempts": int}}
_MFA_STORE: Dict[str, Dict[str, Any]] = {}
_MFA_EXPIRY_SECONDS = 300  # 5 minutes
_MAX_MFA_ATTEMPTS = 3


def _get_redis_client():
    """Attempt to connect to Redis for distributed OTP and ticket storage."""
    if os.getenv("PYTEST_CURRENT_TEST"):
        return None
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.Redis.from_url(redis_url, socket_timeout=1)
        client.ping()
        return client
    except Exception as exc:
        if os.getenv("STRICT_ENTERPRISE_MODE", "false").lower() == "true":
            raise RuntimeError(f"STRICT_ENTERPRISE_MODE: Redis outage detected: {exc}")
        return None


class TwilioService:
    """
    Twilio REST API client for SMS delivery, MFA token management,
    and high-risk AML compliance escalation alerting.
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
        alert_phone: Optional[str] = None,
    ):
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.getenv("TWILIO_FROM_PHONE_NUMBER", "+15005550006")
        self.alert_phone = alert_phone or os.getenv("TWILIO_ALERT_RECIPIENT_PHONE")
        self.api_base_url = "https://api.twilio.com/2010-04-01"

    def is_configured(self) -> bool:
        """Check if production Twilio credentials are configured."""
        return bool(
            self.account_sid
            and self.auth_token
            and not self.account_sid.startswith("REPLACE_")
            and not self.auth_token.startswith("REPLACE_")
        )

    def send_sms(self, to_number: str, body: str) -> Dict[str, Any]:
        """
        Dispatches an SMS via Twilio REST API.
        Falls back safely to simulated mode during offline test execution.
        """
        if not to_number:
            raise ValueError("Target phone number is required to send SMS.")

        clean_to = to_number.strip()
        clean_body = body.strip()

        # Simulation: under tests, when mock mode is switched on, or (outside production only) for
        # the reserved fictional number ranges. In production a +1555 number is sent like any other,
        # so nobody can enrol one to get a code that is never really delivered.
        import security
        production = security.is_production()
        is_test_number = clean_to.startswith("+1555") or clean_to.startswith("+1500555")
        if (
            os.getenv("PYTEST_CURRENT_TEST")
            or os.getenv("TWILIO_MOCK_MODE", "false").lower() == "true"
            or (is_test_number and not production)
        ):
            return self._simulated(clean_to, clean_body, production)

        # If configured with credentials, attempt live HTTP transmission
        if self.is_configured():
            endpoint = f"{self.api_base_url}/Accounts/{self.account_sid}/Messages.json"
            payload = {
                "From": self.from_number,
                "To": clean_to,
                "Body": clean_body,
            }
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(
                        endpoint,
                        auth=(self.account_sid, self.auth_token),
                        data=payload,
                    )
                    if resp.status_code in (200, 201):
                        data = resp.json()
                        logger.info(f"Twilio SMS dispatched to {clean_to} (SID: {data.get('sid')})")
                        return {
                            "status": "delivered",
                            "sid": data.get("sid"),
                            "to": clean_to,
                            "simulated": False,
                        }
                    else:
                        logger.warning(f"Twilio API error ({resp.status_code}): {resp.text}")
                        return {
                            "status": "failed",
                            "error": resp.text,
                            "status_code": resp.status_code,
                            "simulated": False,
                        }
            except Exception as exc:
                logger.error(f"Failed to communicate with Twilio API: {exc}")
                return {"status": "error", "error": str(exc), "simulated": False}

        # Simulated fallback mode if not configured
        if production:
            raise RuntimeError("STRICT_ENTERPRISE_MODE: Twilio API credentials not configured.")
        return self._simulated(clean_to, clean_body, production)

    @staticmethod
    def _simulated(clean_to: str, clean_body: str, production: bool) -> Dict[str, Any]:
        """
        Pretend to send. The message text can contain a one-time code, so it is written to the log
        and returned only outside production, where a developer has no other way to read it.
        """
        sim_sid = f"SM_sim_{secrets.token_hex(16)}"
        result = {"status": "delivered", "sid": sim_sid, "to": clean_to, "simulated": True}
        if production:
            logger.info(f"[SIMULATED TWILIO SMS] To: {clean_to} | SID: {sim_sid}")
        else:
            logger.info(f"[SIMULATED TWILIO SMS] To: {clean_to} | Body: {clean_body}")
            result["body"] = clean_body
        return result

    # -------------------------------------------------------------------------
    # Multi-Factor Authentication (MFA) OTP Lifecycle
    # -------------------------------------------------------------------------

    def generate_and_send_mfa_code(self, user_id: str, phone_number: str) -> Tuple[str, str]:
        """
        Generates a 6-digit cryptographic OTP, hashes it, stores with TTL,
        and transmits it via Twilio SMS.
        Returns: (masked_phone, mfa_ticket)
        """
        code = f"{secrets.randbelow(900000) + 100000:06d}"
        code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
        now = time.time()
        expires_at = now + _MFA_EXPIRY_SECONDS

        # 1. Store code in Redis or in-memory fallback
        r = _get_redis_client()
        if r is not None:
            r.set(
                f"ffre:mfa:code:{user_id}",
                json.dumps({"hash": code_hash, "attempts": 0}),
                ex=_MFA_EXPIRY_SECONDS,
            )
        else:
            _MFA_STORE[user_id] = {
                "hash": code_hash,
                "expires": expires_at,
                "attempts": 0,
            }

        # 2. Transmit SMS
        sms_body = f"Your FFIRE verification code is: {code}. Valid for 5 minutes. Do not share this code."
        dispatch_res = self.send_sms(phone_number, sms_body)

        # Fail closed if delivery failed
        if dispatch_res.get("status") in ("failed", "error"):
            if r is not None:
                r.delete(f"ffre:mfa:code:{user_id}")
            _MFA_STORE.pop(user_id, None)
            raise RuntimeError(f"SMS MFA delivery failed: {dispatch_res.get('error', 'Carrier error')}")

        # 3. Create single-use MFA login ticket
        ticket_token = secrets.token_hex(24)
        if r is not None:
            r.set(f"ffre:mfa:ticket:{ticket_token}", user_id, ex=_MFA_EXPIRY_SECONDS)
        else:
            _MFA_STORE[f"ticket:{ticket_token}"] = {
                "user_id": user_id,
                "expires": expires_at,
            }

        # Mask phone number for security display (e.g., +1•••••1234)
        clean = phone_number.strip()
        if len(clean) > 4:
            masked = clean[:2] + "•" * (len(clean) - 6) + clean[-4:]
        else:
            masked = "••••"

        return masked, ticket_token

    def verify_mfa_ticket(self, ticket_token: str) -> Optional[str]:
        """Validates an MFA login ticket and returns the associated user_id."""
        if not ticket_token:
            return None

        r = _get_redis_client()
        if r is not None:
            uid = r.get(f"ffre:mfa:ticket:{ticket_token}")
            if uid:
                return uid.decode("utf-8") if isinstance(uid, bytes) else str(uid)
            return None
        else:
            item = _MFA_STORE.get(f"ticket:{ticket_token}")
            if item and item.get("expires", 0) > time.time():
                return item.get("user_id")
            return None

    def consume_mfa_ticket(self, ticket_token: str) -> bool:
        """Consumes (deletes) a single-use MFA login ticket upon successful verification."""
        if not ticket_token:
            return False
        r = _get_redis_client()
        if r is not None:
            r.delete(f"ffre:mfa:ticket:{ticket_token}")
        _MFA_STORE.pop(f"ticket:{ticket_token}", None)
        return True

    def verify_mfa_code(self, user_id: str, code: str) -> bool:
        """
        Validates the user's submitted OTP code with atomic rate-limiting and timing-safe comparison.
        """
        if not user_id or not code:
            return False

        clean_code = code.strip()
        candidate_hash = hashlib.sha256(clean_code.encode("utf-8")).hexdigest()

        r = _get_redis_client()
        if r is not None:
            lua_script = """
            local key = KEYS[1]
            local cand_hash = ARGV[1]
            local max_att = tonumber(ARGV[2])
            local raw = redis.call('GET', key)
            if not raw then
                return -1
            end
            local data = cjson.decode(raw)
            local att = (data.attempts or 0) + 1
            if att > max_att then
                redis.call('DEL', key)
                return -2
            end
            if data.hash == cand_hash then
                redis.call('DEL', key)
                return 1
            else
                data.attempts = att
                local ttl = redis.call('TTL', key)
                if ttl > 0 then
                    redis.call('SET', key, cjson.encode(data), 'EX', ttl)
                else
                    redis.call('SET', key, cjson.encode(data), 'EX', 300)
                end
                return 0
            end
            """
            try:
                res = r.eval(lua_script, 1, f"ffre:mfa:code:{user_id}", candidate_hash, _MAX_MFA_ATTEMPTS)
                return res == 1
            except Exception as e:
                logger.warning(f"Redis Lua script execution error: {e}")
                if os.getenv("STRICT_ENTERPRISE_MODE", "false").lower() == "true":
                    raise RuntimeError(f"Strict mode: Redis failure during MFA verification: {e}")

        # In-memory fallback
        item = _MFA_STORE.get(user_id)
        if not item:
            return False
        if item.get("expires", 0) < time.time():
            _MFA_STORE.pop(user_id, None)
            return False

        item["attempts"] = item.get("attempts", 0) + 1
        if item["attempts"] > _MAX_MFA_ATTEMPTS:
            _MFA_STORE.pop(user_id, None)
            return False

        is_valid = hmac.compare_digest(candidate_hash, item.get("hash", ""))
        if is_valid:
            _MFA_STORE.pop(user_id, None)
            return True
        return False

    # -------------------------------------------------------------------------
    # Critical Fraud Escalation Incident Alerting
    # -------------------------------------------------------------------------

    def send_critical_escalation_alert(
        self,
        investigation_id: str,
        risk_score: float,
        triggers: List[str],
        tenant_id: str = "default_tenant",
        recipient_phone: Optional[str] = None,
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches an executive SMS alert to the compliance / risk officer team
        when an investigation is escalated or exhibits severe typology alerts.
        """
        target_phone = recipient_phone or self.alert_phone or os.getenv("TWILIO_ALERT_RECIPIENT_PHONE")
        if not target_phone and (os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TWILIO_MOCK_MODE", "false").lower() == "true"):
            target_phone = "+15005550006"

        if not target_phone:
            logger.info("No recipient phone configured; skipping critical escalation SMS alert.")
            if db is not None:
                try:
                    import models
                    models.AuditLog.create_chained_entry(
                        db=db,
                        tenant_id=tenant_id,
                        investigation_id=investigation_id,
                        action="SMS_ALERT_SKIPPED",
                        details="No recipient phone configured for critical escalation alert.",
                    )
                except Exception as exc:
                    logger.warning(f"Could not write SMS alert skip to audit log: {exc}")
            return {"status": "skipped", "reason": "No recipient phone configured"}

        trigger_summary = "; ".join(triggers[:2]) if triggers else "Autonomous threshold breach"
        alert_msg = (
            f"[FFIRE CRITICAL ALERT] Case {investigation_id} ESCALATED! "
            f"Risk Score: {risk_score:.2f}. Tenant: {tenant_id}. "
            f"Triggers: {trigger_summary}. Immediate investigator review required."
        )

        res = self.send_sms(target_phone, alert_msg)
        is_simulated = res.get("simulated", False)
        status_val = res.get("status", "unknown")

        if is_simulated:
            action_name = "SMS_ALERT_SIMULATED"
        elif status_val == "delivered":
            action_name = "SMS_ALERT_DISPATCHED"
        else:
            action_name = "SMS_ALERT_FAILED"

        # Record event in immutable audit log if db session provided
        if db is not None:
            try:
                import models
                models.AuditLog.create_chained_entry(
                    db=db,
                    tenant_id=tenant_id,
                    investigation_id=investigation_id,
                    action=action_name,
                    details=f"Twilio SMS to {target_phone}; provider_status: {status_val}; SID: {res.get('sid')}; simulated: {is_simulated}",
                )
            except Exception as exc:
                logger.error(f"Critical: could not write SMS alert to audit chain: {exc}")
                try:
                    import models
                    models.AuditLog.create_chained_entry(
                        db=db,
                        tenant_id=tenant_id,
                        investigation_id=investigation_id,
                        action="SMS_ALERT_AUDIT_WRITE_FAILED",
                        details=f"Audit chain write error: {exc}",
                    )
                except Exception:
                    pass

        return res


# Singleton instance
twilio_service = TwilioService()
