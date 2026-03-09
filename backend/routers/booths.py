from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models
import schemas
import auth

router = APIRouter(prefix="/api/booths", tags=["Booths"])

# ---------- Create Booth ----------
@router.post("/", response_model=schemas.BoothResponse, status_code=status.HTTP_201_CREATED)
async def create_booth(
    booth_data: schemas.BoothCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin", "StateAdmin", "ConstituencyManager"]))
):
    """
    Create a new booth.
    Allowed for SuperAdmin, StateAdmin, and ConstituencyManager.
    """
    # Verify constituency exists
    constituency = db.query(models.Constituency).filter(models.Constituency.id == booth_data.constituency_id).first()
    if not constituency:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Constituency not found")

    # Check if booth code is unique
    existing = db.query(models.Booth).filter(models.Booth.code == booth_data.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booth code already exists")

    new_booth = models.Booth(**booth_data.model_dump())
    db.add(new_booth)
    db.commit()
    db.refresh(new_booth)
    return new_booth


# ---------- List Booths ----------
@router.get("/", response_model=List[schemas.BoothResponse])
async def get_booths(
    constituency_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """
    Get all booths, optionally filtered by constituency.
    Supports pagination.
    """
    query = db.query(models.Booth)
    if constituency_id:
        query = query.filter(models.Booth.constituency_id == constituency_id)
    booths = query.offset(skip).limit(limit).all()
    return booths


# ---------- Get Single Booth ----------
@router.get("/{booth_id}", response_model=schemas.BoothResponse)
async def get_booth(
    booth_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """
    Get details of a specific booth by ID.
    """
    booth = db.query(models.Booth).filter(models.Booth.id == booth_id).first()
    if not booth:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booth not found")
    return booth


# ---------- Update Booth ----------
@router.put("/{booth_id}", response_model=schemas.BoothResponse)
async def update_booth(
    booth_id: int,
    booth_data: schemas.BoothCreate,  # reuse create schema, but can be a partial update schema if needed
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin", "StateAdmin", "ConstituencyManager"]))
):
    """
    Update an existing booth.
    Allowed for SuperAdmin, StateAdmin, and ConstituencyManager.
    """
    booth = db.query(models.Booth).filter(models.Booth.id == booth_id).first()
    if not booth:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booth not found")

    # If code is being changed, ensure it's unique
    if booth_data.code != booth.code:
        existing = db.query(models.Booth).filter(models.Booth.code == booth_data.code).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booth code already exists")

    # Update fields
    for key, value in booth_data.model_dump().items():
        setattr(booth, key, value)

    db.commit()
    db.refresh(booth)
    return booth


# ---------- Delete Booth ----------
@router.delete("/{booth_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booth(
    booth_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin"]))
):
    """
    Delete a booth. Only SuperAdmin can delete.
    """
    booth = db.query(models.Booth).filter(models.Booth.id == booth_id).first()
    if not booth:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booth not found")

    # Optional: check if booth has related records (citizens, etc.) and decide to cascade or forbid
    citizens_count = db.query(models.Citizen).filter(models.Citizen.booth_id == booth_id).count()
    if citizens_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete booth with existing citizens. Reassign or remove them first."
        )

    db.delete(booth)
    db.commit()
    return None  # 204 No Content