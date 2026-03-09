from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models
import schemas
import auth

router = APIRouter(prefix="/api/citizens", tags=["Citizens"])

# ---------- Helper: verify booth and street ----------
def _verify_booth_and_street(db: Session, booth_id: int, street_id: Optional[int] = None):
    """Raise HTTPException if booth not found or street not found/not in booth."""
    booth = db.query(models.Booth).filter(models.Booth.id == booth_id).first()
    if not booth:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booth not found")
    if street_id:
        street = db.query(models.Street).filter(models.Street.id == street_id).first()
        if not street:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Street not found")
        if street.booth_id != booth_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Street does not belong to the specified booth")
    return booth

# ---------- Create Citizen ----------
@router.post("/", response_model=schemas.CitizenResponse, status_code=status.HTTP_201_CREATED)
async def create_citizen(
    citizen_data: schemas.CitizenCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin", "StateAdmin", "ConstituencyManager", "BoothOfficer"]))
):
    """
    Create a new citizen.
    Allowed roles: SuperAdmin, StateAdmin, ConstituencyManager, BoothOfficer.
    """
    # Verify booth and street (if provided)
    _verify_booth_and_street(db, citizen_data.booth_id, citizen_data.street_id)

    # Optionally check for duplicate phone (if phone is unique in your system)
    if citizen_data.phone:
        existing = db.query(models.Citizen).filter(models.Citizen.phone == citizen_data.phone).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already registered")

    new_citizen = models.Citizen(**citizen_data.model_dump())
    db.add(new_citizen)
    db.commit()
    db.refresh(new_citizen)
    return new_citizen


# ---------- List Citizens ----------
@router.get("/", response_model=List[schemas.CitizenResponse])
async def get_citizens(
    booth_id: Optional[int] = None,
    search: Optional[str] = Query(None, description="Search by name or phone"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """
    Get all citizens, optionally filtered by booth_id and/or search term.
    Supports pagination.
    """
    query = db.query(models.Citizen)
    if booth_id:
        query = query.filter(models.Citizen.booth_id == booth_id)
    if search:
        # Search in name or phone (case‑insensitive)
        search_pattern = f"%{search}%"
        query = query.filter(
            (models.Citizen.name.ilike(search_pattern)) |
            (models.Citizen.phone.ilike(search_pattern))
        )
    citizens = query.offset(skip).limit(limit).all()
    return citizens


# ---------- Get Citizen by ID ----------
@router.get("/{citizen_id}", response_model=schemas.CitizenResponse)
async def get_citizen(
    citizen_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """
    Get details of a specific citizen by ID.
    """
    citizen = db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
    if not citizen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citizen not found")
    return citizen


# ---------- Update Citizen ----------
@router.put("/{citizen_id}", response_model=schemas.CitizenResponse)
async def update_citizen(
    citizen_id: int,
    citizen_data: schemas.CitizenCreate,  # reuse create schema; all fields required
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin", "StateAdmin", "ConstituencyManager", "BoothOfficer"]))
):
    """
    Update an existing citizen (full update). All fields must be provided.
    Allowed roles: SuperAdmin, StateAdmin, ConstituencyManager, BoothOfficer.
    """
    citizen = db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
    if not citizen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citizen not found")

    # Verify booth and street
    _verify_booth_and_street(db, citizen_data.booth_id, citizen_data.street_id)

    # If phone changed, check uniqueness
    if citizen_data.phone and citizen_data.phone != citizen.phone:
        existing = db.query(models.Citizen).filter(
            models.Citizen.phone == citizen_data.phone,
            models.Citizen.id != citizen_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already used by another citizen")

    # Update fields
    for key, value in citizen_data.model_dump().items():
        setattr(citizen, key, value)

    db.commit()
    db.refresh(citizen)
    return citizen


# ---------- Partial Update Citizen (PATCH) ----------
@router.patch("/{citizen_id}", response_model=schemas.CitizenResponse)
async def patch_citizen(
    citizen_id: int,
    citizen_data: schemas.CitizenPatch,  # we need to define this schema
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin", "StateAdmin", "ConstituencyManager", "BoothOfficer"]))
):
    """
    Partially update an existing citizen. Only provided fields are updated.
    Allowed roles: SuperAdmin, StateAdmin, ConstituencyManager, BoothOfficer.
    """
    citizen = db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
    if not citizen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citizen not found")

    # If booth_id or street_id are provided, verify them
    if citizen_data.booth_id is not None or citizen_data.street_id is not None:
        booth_id = citizen_data.booth_id if citizen_data.booth_id is not None else citizen.booth_id
        street_id = citizen_data.street_id if citizen_data.street_id is not None else citizen.street_id
        _verify_booth_and_street(db, booth_id, street_id)

    # If phone provided and changed, check uniqueness
    if citizen_data.phone is not None and citizen_data.phone != citizen.phone:
        existing = db.query(models.Citizen).filter(
            models.Citizen.phone == citizen_data.phone,
            models.Citizen.id != citizen_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already used")

    # Update only provided fields
    update_data = citizen_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(citizen, key, value)

    db.commit()
    db.refresh(citizen)
    return citizen


# ---------- Delete Citizen ----------
@router.delete("/{citizen_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_citizen(
    citizen_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin"]))
):
    """
    Delete a citizen. Only SuperAdmin can delete.
    Before deletion, checks if citizen has related records (issues, beneficiaries, etc.).
    """
    citizen = db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
    if not citizen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citizen not found")

    # Check for related records to avoid orphaned data
    related_issues = db.query(models.Issue).filter(models.Issue.citizen_id == citizen_id).count()
    if related_issues > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete citizen with existing issues. Reassign or delete issues first."
        )

    related_beneficiaries = db.query(models.Beneficiary).filter(models.Beneficiary.citizen_id == citizen_id).count()
    if related_beneficiaries > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete citizen with existing scheme enrollments."
        )

    related_sentiments = db.query(models.SentimentLog).filter(models.SentimentLog.citizen_id == citizen_id).count()
    if related_sentiments > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete citizen with existing sentiment logs."
        )

    # If no related records, proceed
    db.delete(citizen)
    db.commit()
    return None  # 204 No Content