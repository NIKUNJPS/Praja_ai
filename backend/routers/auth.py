from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
import auth
from email_service import send_otp_email, send_welcome_email
from config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# ---------- Helper: get or create super user ----------
def _get_or_create_super_user(db: Session) -> models.User:
    """Return existing super user or create one with predefined credentials."""
    super_email = settings.SUPER_USER_EMAIL
    user = db.query(models.User).filter(models.User.email == super_email).first()
    if not user:
        # Create super user with a random password (unused for super key login)
        from auth import get_password_hash
        import secrets
        random_password = secrets.token_urlsafe(16)
        user = models.User(
            email=super_email,
            password_hash=get_password_hash(random_password),
            name="Super Admin",
            role=models.UserRole.SUPER_ADMIN,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# ---------- Registration ----------
@router.post("/register", response_model=schemas.UserResponse)
async def register(
    user_data: schemas.UserRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        if existing.is_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        else:
            # Delete unverified user to allow re-registration
            db.delete(existing)
            db.commit()
    
    # Map role string to enum
    role_map = {
        "SUPERADMIN": models.UserRole.SUPER_ADMIN,
        "STATEADMIN": models.UserRole.STATE_ADMIN,
        "CONSTITUENCYMANAGER": models.UserRole.CONSTITUENCY_MANAGER,
        "BOOTHOFFICER": models.UserRole.BOOTH_OFFICER,
        "ANALYST": models.UserRole.ANALYST,
        "PUBLICVIEWER": models.UserRole.PUBLIC_VIEWER
    }
    user_role = role_map.get(user_data.role.upper().replace(" ", "").replace("_", ""), models.UserRole.PUBLIC_VIEWER)
    
    # Create user (unverified)
    hashed_password = auth.get_password_hash(user_data.password)
    new_user = models.User(
        email=user_data.email,
        password_hash=hashed_password,
        name=user_data.name,
        role=user_role,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate and send OTP
    otp = auth.create_otp(db, user_data.email, "registration")
    background_tasks.add_task(send_otp_email, user_data.email, otp, "registration")
    
    return new_user

# ---------- Verify OTP ----------
@router.post("/verify-otp")
async def verify_otp(
    data: schemas.OTPVerify,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Verify OTP
    valid = auth.verify_otp(db, data.email, data.otp, data.purpose)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    
    if data.purpose == "registration":
        # Mark user as verified
        user = db.query(models.User).filter(models.User.email == data.email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.is_verified = True
        db.commit()
        background_tasks.add_task(send_welcome_email, user.email, user.name)
        return {"message": "Email verified successfully"}
    
    elif data.purpose == "password_reset":
        reset_token = auth.create_password_reset_token(data.email)
        return {"reset_token": reset_token}
    
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid purpose")

# ---------- Resend OTP ----------
@router.post("/resend-otp")
async def resend_otp(
    data: schemas.OTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    if data.purpose == "registration":
        user = db.query(models.User).filter(models.User.email == data.email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user.is_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified")
    
    otp = auth.create_otp(db, data.email, data.purpose)
    background_tasks.add_task(send_otp_email, data.email, otp, data.purpose)
    return {"message": "OTP sent"}

# ---------- Login (email + password) ----------
@router.post("/login", response_model=schemas.Token)
async def login(
    user_data: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user or not auth.verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    
    access_token = auth.create_access_token(data={"sub": user.email, "role": user.role.value, "is_verified": user.is_verified})
    refresh_token = auth.create_refresh_token(data={"sub": user.email, "role": user.role.value, "is_verified": user.is_verified})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# ---------- Super Key Login (bypasses normal auth) ----------
class SuperLoginRequest(BaseModel):
    super_key: str
    email: Optional[str] = None   # optional, defaults to configured super email

@router.post("/super-login", response_model=schemas.Token)
async def super_login(
    request: SuperLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate using a predefined super key (from .env). 
    Returns tokens for the super user account (SuperAdmin).
    """
    if request.super_key != settings.SUPER_USER_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid super key")
    
    email = request.email or settings.SUPER_USER_EMAIL
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        # Create super user if it doesn't exist
        from auth import get_password_hash
        import secrets
        random_password = secrets.token_urlsafe(16)
        user = models.User(
            email=email,
            password_hash=get_password_hash(random_password),
            name="Super Admin",
            role=models.UserRole.SUPER_ADMIN,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif user.role != models.UserRole.SUPER_ADMIN:
        # Optionally upgrade role? We'll just forbid.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a super admin")
    
    # Ensure verified
    if not user.is_verified:
        user.is_verified = True
        db.commit()
    
    access_token = auth.create_access_token(data={"sub": user.email, "role": user.role.value, "is_verified": user.is_verified})
    refresh_token = auth.create_refresh_token(data={"sub": user.email, "role": user.role.value, "is_verified": user.is_verified})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# ---------- Forgot Password ----------
@router.post("/forgot-password")
async def forgot_password(
    data: schemas.PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        return {"message": "If the email exists, an OTP has been sent"}
    
    otp = auth.create_otp(db, data.email, "password_reset")
    background_tasks.add_task(send_otp_email, data.email, otp, "password_reset")
    return {"message": "If the email exists, an OTP has been sent"}

# ---------- Reset Password (with OTP) ----------
@router.post("/reset-password")
async def reset_password(
    data: schemas.PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    valid = auth.verify_otp(db, data.email, data.otp, "password_reset")
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.password_hash = auth.get_password_hash(data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

# ---------- Set Password with token (alternative after OTP) ----------
@router.post("/set-password")
async def set_password(
    data: schemas.SetNewPassword,
    db: Session = Depends(get_db)
):
    email = auth.verify_password_reset_token(data.token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.password_hash = auth.get_password_hash(data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

# ---------- Refresh Token ----------
@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    token_data = auth.decode_token(refresh_token)
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    access_token = auth.create_access_token(data={"sub": user.email, "role": user.role.value, "is_verified": user.is_verified})
    new_refresh_token = auth.create_refresh_token(data={"sub": user.email, "role": user.role.value, "is_verified": user.is_verified})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

# ---------- Get current user ----------
@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(current_user: models.User = Depends(auth.require_verified_user)):
    return current_user