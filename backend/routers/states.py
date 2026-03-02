from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/api/states", tags=["States"])

@router.post("/", response_model=schemas.StateResponse)
async def create_state(
    state_data: schemas.StateCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin", "StateAdmin"]))
):
    new_state = models.State(**state_data.model_dump())
    db.add(new_state)
    db.commit()
    db.refresh(new_state)
    return new_state

@router.get("/", response_model=List[schemas.StateResponse])
async def get_states(db: Session = Depends(get_db)):
    states = db.query(models.State).all()
    return states

@router.get("/{state_id}", response_model=schemas.StateResponse)
async def get_state(state_id: int, db: Session = Depends(get_db)):
    state = db.query(models.State).filter(models.State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found")
    return state