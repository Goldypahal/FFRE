from datetime import datetime, timedelta
import timeutil
from typing import Optional
from jose import JWTError, jwt
import bcrypt
import time
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models
import security
import os
from sqlalchemy import func

def is_strict_mode() -> bool:
    return security.is_production()

ENV = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).lower()
SECRET_KEY = security.validate_production_secret("SECRET_KEY", os.environ.get("SECRET_KEY"), min_length=32)
if SECRET_KEY == "dev-secret-key-change-in-production":
    if ENV == "production" or is_strict_mode():
        raise RuntimeError("CRITICAL SECURITY VIOLATION: Default development SECRET_KEY is strictly forbidden in production!")
    print("WARNING: Using default development SECRET_KEY. Set SECRET_KEY in production!")

ALGORITHM = "HS256"
# Finding 10: Access token lifetime read from env (defaults to 15m in production/strict, 60m in dev)
_default_expire = 15 if (is_strict_mode() or ENV == "production") else 60
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(_default_expire)))

# "platform_admin" is the only role that may cross tenant boundaries. It cannot be granted through
# invitations or the admin API; it is set at bootstrap (BOOTSTRAP_PLATFORM_ADMIN=true) or in the database.
PLATFORM_ADMIN_ROLE = "platform_admin"
TENANT_ADMIN_ROLES = {"admin", "administrator"}
ADMIN_ROLES = TENANT_ADMIN_ROLES | {PLATFORM_ADMIN_ROLE}
VALID_ROLES = {"admin", "administrator", "investigator", "analyst", "compliance_officer", "viewer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def is_admin(user) -> bool:
    """Tenant administrator (or platform administrator). Scoped to the user's own tenant."""
    return getattr(user, "role", "") in ADMIN_ROLES


def is_platform_admin(user) -> bool:
    """May act across tenants."""
    return getattr(user, "role", "") == PLATFORM_ADMIN_ROLE


def require_admin(user) -> None:
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Administrator role required")


def require_role(user, *roles: str) -> None:
    """Allow the listed roles, plus administrators."""
    if getattr(user, "role", "") not in roles and not is_admin(user):
        raise HTTPException(status_code=403, detail="Not enough privileges")


def _password_bytes(password) -> bytes:
    if isinstance(password, str):
        password = password.encode("utf-8")
    return password[:72]  # bcrypt reads at most 72 bytes


def verify_password(plain_password, hashed_password) -> bool:
    if not plain_password or not hashed_password:
        return False
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(_password_bytes(plain_password), hashed_password)
    except (ValueError, TypeError):
        return False


def get_password_hash(password) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")

REFRESH_TOKEN_EXPIRE_DAYS = 7  # also bounds how long a logout marker is kept

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = timeutil.utcnow() + expires_delta
    else:
        expire = timeutil.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access", "jti": uuid.uuid4().hex, "ist": time.time()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate cryptographically signed JWT refresh token (Chapter 47)."""
    to_encode = data.copy()
    if expires_delta:
        expire = timeutil.utcnow() + expires_delta
    else:
        expire = timeutil.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": uuid.uuid4().hex, "ist": time.time()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_refresh_token(token: str) -> dict:
    """Decode and validate a refresh token. Rejects tokens revoked by logout or rotation."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: expected refresh token"
            )
        if is_token_revoked(token) or is_session_revoked(payload.get("sub"), payload.get("ist")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    if not email:
        return None
    normalized_email = email.strip().lower()
    email_idx = security.compute_blind_index(normalized_email)
    
    # 1. Primary path: O(1) indexed lookup via deterministic blind index
    usr = db.query(models.User).filter(models.User.email_hash == email_idx).first()
    if usr:
        return usr

    # 2. Fallback for legacy rows that have no blind index yet. Only those rows are scanned, so an
    #    unknown email costs nothing once every user has been backfilled.
    for user in db.query(models.User).filter(models.User.email_hash.is_(None)).all():
        if user.email and user.email.strip().lower() == normalized_email:
            try:
                user.email_hash = email_idx
                db.commit()
            except Exception:
                db.rollback()
            return user
    return None


_REVOKED_TOKENS = set()
_SESSIONS_REVOKED_AT: dict = {}
_REVOCATION_REDIS = None
_REVOCATION_REDIS_RETRY_AT = 0.0
_REDIS_RETRY_SECONDS = 30.0

def _get_revocation_redis():
    """Shared Redis client. A failed connection is retried after a short delay, never cached for good."""
    global _REVOCATION_REDIS, _REVOCATION_REDIS_RETRY_AT
    if _REVOCATION_REDIS is None or _REVOCATION_REDIS is False:
        if _REVOCATION_REDIS is False and time.monotonic() < _REVOCATION_REDIS_RETRY_AT:
            return None
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            client = redis.Redis.from_url(redis_url, socket_timeout=1)
            client.ping()
            _REVOCATION_REDIS = client
        except Exception:
            _REVOCATION_REDIS = False
            _REVOCATION_REDIS_RETRY_AT = time.monotonic() + _REDIS_RETRY_SECONDS
    return _REVOCATION_REDIS if _REVOCATION_REDIS is not False else None


def _session_key(subject: str) -> str:
    return "ffre:sessions_revoked_at:" + security.compute_blind_index(subject.strip().lower())


def revoke_user_sessions(subject: Optional[str], ttl_seconds: int = REFRESH_TOKEN_EXPIRE_DAYS * 86400) -> None:
    """Invalidate every access and refresh token issued to this user up to now (used by logout)."""
    if not subject:
        return
    now = time.time()
    _SESSIONS_REVOKED_AT[subject.strip().lower()] = now
    r = _get_revocation_redis()
    if r is not None:
        try:
            r.set(_session_key(subject), repr(now), ex=ttl_seconds)
        except Exception as exc:
            if is_strict_mode():
                raise RuntimeError(f"STRICT_ENTERPRISE_MODE: Failed to record session revocation: {exc}")


def is_session_revoked(subject: Optional[str], issued_at) -> bool:
    """True when the token was issued at or before the user's last logout."""
    if not subject or issued_at is None:
        return False
    try:
        issued = float(issued_at)
    except (TypeError, ValueError):
        return False
    revoked_at = _SESSIONS_REVOKED_AT.get(subject.strip().lower())
    r = _get_revocation_redis()
    if r is not None:
        try:
            raw = r.get(_session_key(subject))
            if raw is not None:
                shared = float(raw.decode() if isinstance(raw, bytes) else raw)
                revoked_at = max(revoked_at or 0.0, shared)
        except Exception:
            pass
    return revoked_at is not None and issued <= revoked_at

def revoke_token(token: str, ttl_seconds: int = 86400) -> None:
    """Revoke a JWT token by adding it to Redis shared blocklist (accessible to all worker processes) with memory fallback."""
    if not token:
        return
    token = token.strip()
    r = _get_revocation_redis()
    if r is not None:
        try:
            r.set(f"ffre:revoked_token:{token}", "revoked", ex=ttl_seconds)
        except Exception as exc:
            if is_strict_mode():
                raise RuntimeError(f"STRICT_ENTERPRISE_MODE: Failed to record token revocation in distributed registry: {exc}")
    else:
        if is_strict_mode():
            raise RuntimeError("STRICT_ENTERPRISE_MODE: Distributed token revocation registry (Redis) is unreachable.")
    _REVOKED_TOKENS.add(token)

def is_token_revoked(token: str) -> bool:
    """Check if token is revoked in Redis shared blocklist or local fallback. Fails closed in strict mode."""
    if not token:
        return False
    token = token.strip()
    r = _get_revocation_redis()
    if r is not None:
        try:
            if r.exists(f"ffre:revoked_token:{token}"):
                return True
        except Exception as exc:
            if is_strict_mode():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Authentication service unavailable: Token revocation registry unreachable ({exc})"
                )
    else:
        if is_strict_mode():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable: Distributed token revocation registry is offline (fail-closed)"
            )
    return token in _REVOKED_TOKENS

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        if email is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    if is_session_revoked(email, payload.get("ist")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    if not is_active_user(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")
    return user


def is_active_user(user) -> bool:
    return (getattr(user, "status", None) or "active").strip().lower() == "active"


def check_permissions(required_role: str, required_scope: Optional[str] = None):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        user_role = getattr(current_user, "role", "")
        if user_role != required_role and not is_admin(current_user):
            raise HTTPException(status_code=403, detail="Not enough privileges")
        return current_user
    return role_checker
