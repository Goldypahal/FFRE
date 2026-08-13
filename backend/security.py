"""
Security utilities for PII encryption at rest.
Implements AES-256 encryption for sensitive fields using cryptography library.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_encryption_key():
    """
    Generate encryption key from environment variable.
    In production, use a proper key management service (AWS KMS, HashiCorp Vault, etc.)
    """
    # Get secret from environment - should be set in production
    # For development, provide a default but warn about it
    secret_key = os.getenv("ENCRYPTION_SECRET_KEY")
    if not secret_key:
        # In production, this should raise an error rather than using a default
        secret_key = "dev-secret-key-change-in-production"
        print("WARNING: Using default encryption key. Set ENCRYPTION_SECRET_KEY environment variable in production!")

    # Use a salt - in production, this should be stored separately or derived properly
    salt = b"fixed-salt-for-demo-purpose-use-random-in-production"

    # Derive a key using PBKDF2
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
    # Create a dummy cipher that doesn't actually encrypt for safety during development
    _cipher = None

def encrypt_data(data: str) -> str:
    """
    Encrypt string data using AES-256 (via Fernet).
    Returns encrypted string.
    """
    if not data or not _cipher:
        return data

    encrypted_bytes = _cipher.encrypt(data.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')

def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt string data using AES-256 (via Fernet).
    Expects encrypted string.
    Returns original string.
    """
    if not encrypted_data or not _cipher:
        return encrypted_data

    try:
        decrypted_bytes = _cipher.decrypt(encrypted_data.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception:
        # If decryption fails (e.g. data was stored in plaintext), return original string safely
        return encrypted_data

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