from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models
import security
import os
from sqlalchemy import func

ENV = os.getenv("ENV", "development").lower()
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if ENV == "production":
        raise ValueError("SECRET_KEY environment variable must be set in production!")
    SECRET_KEY = "dev-secret-key-change-in-production"
    print("WARNING: Using default development SECRET_KEY. Set SECRET_KEY in production!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day for dev

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        import bcrypt
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')[:72]
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)

def get_password_hash(password):
    try:
        return pwd_context.hash(password)
    except Exception:
        import bcrypt
        if isinstance(password, str):
            password = password.encode('utf-8')[:72]
        return bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate cryptographically signed JWT refresh token (Chapter 47)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_refresh_token(token: str) -> dict:
    """Decode and validate a refresh token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: expected refresh token"
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

    # 2. Resilient fallback for unmigrated legacy database records
    for user in db.query(models.User).all():
        if user.email and user.email.strip().lower() == normalized_email:
            try:
                user.email_hash = email_idx
                db.commit()
            except Exception:
                db.rollback()
            return user
    return None


_REVOKED_TOKENS = set()
_REVOCATION_REDIS = None

def is_strict_mode() -> bool:
    return (
        os.getenv("STRICT_ENTERPRISE_MODE", "false").lower() == "true" or
        os.getenv("ENV", "").lower() == "production" or
        os.getenv("ENVIRONMENT", "").lower() == "production"
    )

def _get_revocation_redis():
    global _REVOCATION_REDIS
    if _REVOCATION_REDIS is None:
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            client = redis.Redis.from_url(redis_url, socket_timeout=1)
            client.ping()
            _REVOCATION_REDIS = client
        except Exception:
            _REVOCATION_REDIS = False
    return _REVOCATION_REDIS if _REVOCATION_REDIS is not False else None

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
        
    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user

def check_permissions(required_role: str, required_scope: Optional[str] = None):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        user_role = getattr(current_user, "role", "")
        is_admin = user_role in ("admin", "administrator")
        if user_role != required_role and not is_admin:
            raise HTTPException(status_code=403, detail="Not enough privileges")
        return current_user
    return role_checker
