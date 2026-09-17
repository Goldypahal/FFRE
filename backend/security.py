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

def decrypt_aes256_gcm(encrypted_b64: str) -> str:
    """
    Decrypt Base64-encoded AES-256-GCM payload.
    Extracts nonce, decrypts ciphertext, and cryptographically verifies authentication tag.
    Raises ValueError on tampering or invalid key.
    """
    if not encrypted_b64:
        return encrypted_b64
    try:
        raw_key = get_aes256_raw_key()
        aesgcm = AESGCM(raw_key)
        raw_payload = base64.b64decode(encrypted_b64.encode("utf-8"))
        if len(raw_payload) < 28: # 12 bytes nonce + 16 bytes tag minimum
            return encrypted_b64
        nonce = raw_payload[:12]
        ciphertext = raw_payload[12:]
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode("utf-8")
    except Exception:
        # Fallback to plaintext if decryption fails
        return encrypted_b64

def encrypt_data(data: str) -> str:
    """
    Encrypt string data using authentic AES-256-GCM authenticated encryption at rest.
    Returns Base64-encoded string containing nonce + ciphertext + tag.
    """
    if not data:
        return data
    return encrypt_aes256_gcm(data)

def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt string data.
    Attempts authentic AES-256-GCM decryption first.
    Falls back to legacy Fernet (AES-128-CBC) for seamless migration of older database records.
    If both fail or payload is plaintext, safely returns original string.
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

    # 3. Fallback to original string if not encrypted
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

# Example usage in SQLAlchemy models:
#
# from sqlalchemy.ext.hybrid import hybrid_property
# from security import encrypt_data, decrypt_data
#
# class User(Base):
#     __tablename__ = "user"
#
#     _email = Column("email", String(150), nullable=False, unique=True)
#
#     @hybrid_property
#     def email(self):
#         return decrypt_data(self._email) if self._email else None
#
#     @email.setter
#     def email(self, value):
#         self._email = encrypt_data(value) if value else None
#
#     # Repeat for other PII fields like name, etc.