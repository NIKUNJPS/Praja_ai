from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.UserResponse)
async def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user_data.password)
    role_map = {
        "SUPERADMIN": models.UserRole.SUPER_ADMIN,
        "STATEADMIN": models.UserRole.STATE_ADMIN,
        "CONSTITUENCYMANAGER": models.UserRole.CONSTITUENCY_MANAGER,
        "BOOTHOFFICER": models.UserRole.BOOTH_OFFICER,
        "ANALYST": models.UserRole.ANALYST,
        "PUBLICVIEWER": models.UserRole.PUBLIC_VIEWER
    }
    user_role = role_map.get(user_data.role.upper().replace(" ", "").replace("_", ""), models.UserRole.PUBLIC_VIEWER)
    
    new_user = models.User(
        email=user_data.email,
        password_hash=hashed_password,
        name=user_data.name,
        role=user_role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
async def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user or not auth.verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = auth.create_access_token(data={"sub": user.email, "role": user.role.value})
    refresh_token = auth.create_refresh_token(data={"sub": user.email, "role": user.role.value})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    token_data = auth.decode_token(refresh_token)
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    access_token = auth.create_access_token(data={"sub": user.email, "role": user.role.value})
    new_refresh_token = auth.create_refresh_token(data={"sub": user.email, "role": user.role.value})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }