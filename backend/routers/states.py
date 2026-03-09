from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models
import schemas
import auth

router = APIRouter(prefix="/api/states", tags=["States"])


# ---------- Create State ----------
@router.post("/", response_model=schemas.StateResponse, status_code=status.HTTP_201_CREATED)
async def create_state(
    state_data: schemas.StateCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin", "StateAdmin"]))
):
    """
    Create a new state.
    Allowed for SuperAdmin and StateAdmin.
    """
    # Check for duplicate state code
    existing = db.query(models.State).filter(models.State.code == state_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State with this code already exists"
        )

    new_state = models.State(**state_data.model_dump())
    db.add(new_state)
    db.commit()
    db.refresh(new_state)
    return new_state


# ---------- List States ----------
@router.get("/", response_model=List[schemas.StateResponse])
async def get_states(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """
    Get a paginated list of all states.
    Requires a verified user.
    """
    states = db.query(models.State).offset(skip).limit(limit).all()
    return states


# ---------- Get State by ID ----------
@router.get("/{state_id}", response_model=schemas.StateResponse)
async def get_state(
    state_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """
    Get details of a specific state by ID.
    Requires a verified user.
    """
    state = db.query(models.State).filter(models.State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found")
    return state


# ---------- Update State ----------
@router.put("/{state_id}", response_model=schemas.StateResponse)
async def update_state(
    state_id: int,
    state_data: schemas.StateCreate,  # reuse create schema; all fields required
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin", "StateAdmin"]))
):
    """
    Update an existing state (full update).
    Allowed for SuperAdmin and StateAdmin.
    """
    state = db.query(models.State).filter(models.State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found")

    # If code is being changed, ensure it's unique
    if state_data.code != state.code:
        existing = db.query(models.State).filter(models.State.code == state_data.code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State code already in use"
            )

    for key, value in state_data.model_dump().items():
        setattr(state, key, value)

    db.commit()
    db.refresh(state)
    return state


# ---------- Delete State ----------
@router.delete("/{state_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_state(
    state_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin"]))
):
    """
    Delete a state. Only SuperAdmin can delete.
    Checks for existing constituencies before deletion.
    """
    state = db.query(models.State).filter(models.State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found")

    # Check if there are constituencies linked
    constituencies_count = db.query(models.Constituency).filter(
        models.Constituency.state_id == state_id
    ).count()
    if constituencies_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete state with existing constituencies. Delete or reassign them first."
        )

    db.delete(state)
    db.commit()
    return None  # 204 No Content