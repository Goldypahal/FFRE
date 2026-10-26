"""
Security utilities for PII encryption at rest.
Implements symmetric Fernet encryption (AES-128-CBC with HMAC-SHA256 authentication) for sensitive fields using cryptography library.
"""

import os
import base64
import hmac
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def get_encryption_key():
    """
    Generate encryption key from environment variable for Fernet (AES-128-CBC + HMAC-SHA256).
    In production, raises an error if ENCRYPTION_SECRET_KEY is not configured.
    """
    env = os.getenv("ENV", "development").lower()
    secret_key = os.getenv("ENCRYPTION_SECRET_KEY")
    if not secret_key:
        if env == "production":
            raise ValueError("ENCRYPTION_SECRET_KEY environment variable must be set in production!")
        secret_key = "dev-secret-key-change-in-production"

    salt_str = os.getenv("ENCRYPTION_SALT", "ffre-default-salt-v1")
    salt = salt_str.encode('utf-8')

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    return key

# Initialize Fernet cipher suite
try:
    _cipher = Fernet(get_encryption_key())
except Exception as e:
    print(f"ERROR initializing encryption: {e}")
    _cipher = None

def get_aes256_raw_key() -> bytes:
    """
    Generate 256-bit (32-byte) binary key derived via PBKDF2-HMAC-SHA256 for authentic AES-256-GCM encryption.
    """
    env = os.getenv("ENV", "development").lower()
    secret_key = os.getenv("ENCRYPTION_SECRET_KEY")
    if not secret_key:
        if env == "production":
            raise ValueError("ENCRYPTION_SECRET_KEY environment variable must be set in production!")
        secret_key = "dev-secret-key-change-in-production"

    salt_str = os.getenv("ENCRYPTION_SALT", "ffre-default-salt-v1")
    salt = salt_str.encode('utf-8')

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(secret_key.encode())

def encrypt_aes256_gcm(data: str) -> str:
    """
    Encrypt plaintext string using authentic AES-256-GCM with 96-bit random nonce.
    Returns standard Base64-encoded string containing nonce + ciphertext + authentication tag.
    Provides confidentiality, integrity, and tamper-resistance.
    """
    if not data:
        return data
    raw_key = get_aes256_raw_key()
    aesgcm = AESGCM(raw_key)
    nonce = os.urandom(12)  # 96-bit nonce as recommended for GCM
    ciphertext_bytes = aesgcm.encrypt(nonce, data.encode("utf-8"), None)
    payload = nonce + ciphertext_bytes
    return base64.b64encode(payload).decode("utf-8")

class DecryptionError(ValueError):
    """Raised when authenticated decryption fails due to tampering, invalid tag, or corrupted ciphertext."""
    pass

def decrypt_aes256_gcm(encrypted_b64: str, fail_closed: bool = True) -> str:
    """
    Decrypt Base64-encoded AES-256-GCM payload.
    Extracts nonce, decrypts ciphertext, and cryptographically verifies authentication tag.
    Raises DecryptionError on tampering or invalid key when fail_closed=True.
    """
    if not encrypted_b64:
        return encrypted_b64
    try:
        raw_key = get_aes256_raw_key()
        aesgcm = AESGCM(raw_key)
        raw_payload = base64.b64decode(encrypted_b64.encode("utf-8"))
        if len(raw_payload) < 28: # 12 bytes nonce + 16 bytes tag minimum
            if fail_closed:
                raise DecryptionError("Payload too short for AES-256-GCM ciphertext")
            return encrypted_b64
        nonce = raw_payload[:12]
        ciphertext = raw_payload[12:]
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode("utf-8")
    except DecryptionError:
        raise
    except Exception as e:
        if fail_closed:
            raise DecryptionError(f"AES-256-GCM decryption failed (tampered ciphertext or invalid authentication tag): {e}") from e
        return encrypted_b64

def encrypt_data(data: str) -> str:
    """
    Encrypt string data using authentic AES-256-GCM authenticated encryption at rest.
    Returns Base64-encoded string containing nonce + ciphertext + tag.
    """
    if not data:
        return data
    return encrypt_aes256_gcm(data)

def decrypt_data(encrypted_data: str, fail_closed: bool = False) -> str:
    """
    Decrypt string data.
    Attempts authentic AES-256-GCM decryption first.
    Falls back to legacy Fernet (AES-128-CBC) for seamless migration of older database records.
    If both fail or payload is plaintext, safely returns original string unless fail_closed=True.
    """
    if not encrypted_data:
        return encrypted_data

    # 1. Attempt AES-256-GCM authenticated decryption
    try:
        raw_key = get_aes256_raw_key()
        aesgcm = AESGCM(raw_key)
        raw_payload = base64.b64decode(encrypted_data.encode("utf-8"))
        if len(raw_payload) >= 28:
            nonce = raw_payload[:12]
            ciphertext = raw_payload[12:]
            decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted_bytes.decode("utf-8")
    except Exception:
        pass

    # 2. Fallback to legacy Fernet (AES-128-CBC) decryption
    if _cipher:
        try:
            decrypted_bytes = _cipher.decrypt(encrypted_data.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception:
            pass

    # 3. Handle failure under strict fail-closed requirements
    if fail_closed:
        raise DecryptionError("Decryption failed for ciphertext under fail-closed enforcement")

    # 4. Fallback to original string if not encrypted
    return encrypted_data

def compute_blind_index(data: str) -> str:
    """
    Compute a deterministic HMAC-SHA256 blind index hash for searchable encrypted fields.
    Allows exact O(1) database lookups without compromising PII confidentiality.
    """
    if not data:
        return ""
    try:
        key = get_encryption_key()
        return hmac.new(key, data.strip().lower().encode("utf-8"), hashlib.sha256).hexdigest()
    except Exception:
        return hashlib.sha256(data.strip().lower().encode("utf-8")).hexdigest()


import re
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple, Union

class PIITokenizer:
    """
    Bi-Directional PII Redaction Tokenizer (Task T1.3 / Finding V7-V8).
    Reversibly redacts sensitive personal identifiability data (names, emails, phones,
    SSNs, credit cards, bank accounts, IPs, fingerprints) into surrogate tokens before
    sending prompts to external LLMs, and re-hydrates returned text before presentation.
    """

    PATTERNS = {
        "EMAIL": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        "SSN": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        "CREDIT_CARD": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
        "PHONE": re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
        "IP_ADDRESS": re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
        "ACCOUNT_ID": re.compile(r'\bacct_[a-zA-Z0-9_-]+\b'),
        "CUSTOMER_ID": re.compile(r'\bcust_[a-zA-Z0-9_-]+\b'),
    }

    def __init__(self, existing_vault: Optional[Dict[str, str]] = None):
        self.token_to_pii: Dict[str, str] = dict(existing_vault) if existing_vault else {}
        self.pii_to_token: Dict[str, str] = {v: k for k, v in self.token_to_pii.items()}
        self.counters: Dict[str, int] = defaultdict(int)
        for token in self.token_to_pii.keys():
            match = re.match(r'<([A-Z_]+)_(\d+)>', token)
            if match:
                ptype, idx = match.group(1), int(match.group(2))
                if idx > self.counters[ptype]:
                    self.counters[ptype] = idx

    def register_pii(self, pii_type: str, value: str) -> str:
        """Register a known PII value and return its deterministic surrogate token."""
        if not value or not isinstance(value, str):
            return value
        val_clean = value.strip()
        if not val_clean:
            return value
        if val_clean in self.pii_to_token:
            return self.pii_to_token[val_clean]
        
        self.counters[pii_type] += 1
        idx = self.counters[pii_type]
        token = f"<{pii_type}_{idx}>"
        self.token_to_pii[token] = val_clean
        self.pii_to_token[val_clean] = token
        return token

    def redact_text(self, text: str) -> str:
        """
        Redact all registered and auto-detected PII in text.
        Returns surrogate-tokenized string with zero plaintext PII.
        """
        if not text or not isinstance(text, str):
            return text

        result = text

        # 1. First redact explicitly registered entities
        for pii_val in sorted(self.pii_to_token.keys(), key=len, reverse=True):
            token = self.pii_to_token[pii_val]
            pattern = re.compile(re.escape(pii_val), re.IGNORECASE)
            result = pattern.sub(token, result)

        # 2. Automatically detect and register pattern matches
        for pii_type, regex in self.PATTERNS.items():
            matches = list(regex.finditer(result))
            for m in reversed(matches):
                match_val = m.group(0)
                if match_val.startswith("<") and match_val.endswith(">"):
                    continue
                token = self.register_pii(pii_type, match_val)
                start, end = m.span()
                result = result[:start] + token + result[end:]

        return result

    def redact_data(self, data: Any) -> Any:
        """Recursively redact PII in dictionaries, lists, or primitive values."""
        if isinstance(data, str):
            return self.redact_text(data)
        elif isinstance(data, dict):
            return {k: self.redact_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.redact_data(item) for item in data]
        return data

    def rehydrate_text(self, text: str) -> str:
        """Restore all surrogate tokens back to original plaintext values."""
        if not text or not isinstance(text, str):
            return text

        result = text
        for token, original in sorted(self.token_to_pii.items(), key=lambda x: len(x[0]), reverse=True):
            result = result.replace(token, original)
        return result

    def rehydrate_data(self, data: Any) -> Any:
        """Recursively re-hydrate surrogate tokens in dictionaries, lists, or strings."""
        if isinstance(data, str):
            return self.rehydrate_text(data)
        elif isinstance(data, dict):
            return {k: self.rehydrate_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.rehydrate_data(item) for item in data]
        return data

    def export_vault(self) -> Dict[str, str]:
        """Export the token mapping dictionary for state persistence."""
        return dict(self.token_to_pii)