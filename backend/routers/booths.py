from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/api/booths", tags=["Booths"])

@router.post("/", response_model=schemas.BoothResponse)
async def create_booth(
    booth_data: schemas.BoothCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin", "StateAdmin", "ConstituencyManager"]))
):
    new_booth = models.Booth(**booth_data.model_dump())
    db.add(new_booth)
    db.commit()
    db.refresh(new_booth)
    return new_booth

@router.get("/", response_model=List[schemas.BoothResponse])
async def get_booths(constituency_id: int = None, db: Session = Depends(get_db)):
    query = db.query(models.Booth)
    if constituency_id:
        query = query.filter(models.Booth.constituency_id == constituency_id)
    booths = query.all()
    return booths

@router.get("/{booth_id}", response_model=schemas.BoothResponse)
async def get_booth(booth_id: int, db: Session = Depends(get_db)):
    booth = db.query(models.Booth).filter(models.Booth.id == booth_id).first()
    if not booth:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booth not found")
    return booth