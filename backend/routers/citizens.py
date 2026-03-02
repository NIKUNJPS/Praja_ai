from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/api/citizens", tags=["Citizens"])

@router.post("/", response_model=schemas.CitizenResponse)
async def create_citizen(
    citizen_data: schemas.CitizenCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin", "StateAdmin", "ConstituencyManager", "BoothOfficer"]))
):
    new_citizen = models.Citizen(**citizen_data.model_dump())
    db.add(new_citizen)
    db.commit()
    db.refresh(new_citizen)
    return new_citizen

@router.get("/", response_model=List[schemas.CitizenResponse])
async def get_citizens(booth_id: int = None, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(models.Citizen)
    if booth_id:
        query = query.filter(models.Citizen.booth_id == booth_id)
    citizens = query.limit(limit).all()
    return citizens

@router.get("/{citizen_id}", response_model=schemas.CitizenResponse)
async def get_citizen(citizen_id: int, db: Session = Depends(get_db)):
    citizen = db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
    if not citizen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citizen not found")
    return citizen