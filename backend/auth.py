from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
import random
import string
from config import settings
from database import get_db
import models
import schemas
from email_service import send_otp_email

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# ---------- Password helpers ----------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

# ---------- Token helpers ----------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with longer expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> schemas.TokenData:
    """Decode and validate a JWT token, returning token data."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        is_verified: bool = payload.get("is_verified", False)
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return schemas.TokenData(email=email, role=role, is_verified=is_verified)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# ---------- OTP helpers ----------
def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of given length."""
    return ''.join(random.choices(string.digits, k=length))

def create_otp(db: Session, email: str, purpose: str, expiry_minutes: int = None) -> str:
    """Generate and store an OTP, returning the plain OTP."""
    if expiry_minutes is None:
        expiry_minutes = settings.OTP_EXPIRE_MINUTES
    otp_code = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)

    # Invalidate any previous unused OTPs for this email/purpose
    db.query(models.OTP).filter(
        models.OTP.email == email,
        models.OTP.purpose == purpose,
        models.OTP.used == False
    ).update({"used": True})

    otp_entry = models.OTP(
        email=email,
        otp_code=otp_code,
        purpose=purpose,
        expires_at=expires_at
    )
    db.add(otp_entry)
    db.commit()
    db.refresh(otp_entry)
    return otp_code

def verify_otp(db: Session, email: str, otp: str, purpose: str) -> bool:
    """Verify OTP for given email and purpose. Returns True if valid and marks as used."""
    otp_entry = db.query(models.OTP).filter(
        models.OTP.email == email,
        models.OTP.purpose == purpose,
        models.OTP.used == False,
        models.OTP.expires_at > datetime.now(timezone.utc)
    ).order_by(models.OTP.created_at.desc()).first()

    if not otp_entry or otp_entry.otp_code != otp:
        return False

    otp_entry.used = True
    db.commit()
    return True

# ---------- Password reset token helpers ----------
def create_password_reset_token(email: str) -> str:
    """Generate a JWT token for password reset (valid for a short time)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire, "type": "password_reset"}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def verify_password_reset_token(token: str) -> Optional[str]:
    """Return email if token valid, else None."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None

# ---------- User dependency ----------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """Get the current authenticated user from the JWT token."""
    token = credentials.credentials
    token_data = decode_token(token)
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def require_roles(allowed_roles: List[str]):
    """Dependency to restrict access to users with specific roles."""
    def role_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker

def require_verified_user(current_user: models.User = Depends(get_current_user)):
    """Dependency to ensure the user's email is verified."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user