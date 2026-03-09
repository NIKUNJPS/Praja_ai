"""
Civic Works Router
Trigger hyper-local notification engine on civic work creation
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone
from database import get_db
import models
import schemas
import auth
import notification_service
import logging
from websocket import connection_manager as manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/civic-works", tags=["Civic Works"])


# ---------- Create Civic Work ----------
@router.post("/", response_model=schemas.CivicWorkResponse, status_code=status.HTTP_201_CREATED)
async def create_civic_work(
    work_data: schemas.CivicWorkCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin", "StateAdmin", "ConstituencyManager"]))
):
    """
    Create a new civic work and automatically trigger the hyper‑local notification engine.
    Notifications are created in the background.
    """
    # Verify booth exists
    booth = db.query(models.Booth).filter(models.Booth.id == work_data.booth_id).first()
    if not booth:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booth not found")

    # Verify affected streets exist and belong to the booth
    if work_data.affected_streets:
        streets = db.query(models.Street).filter(
            models.Street.id.in_(work_data.affected_streets),
            models.Street.booth_id == work_data.booth_id
        ).all()
        if len(streets) != len(work_data.affected_streets):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more affected streets do not exist or do not belong to this booth"
            )

    # Create civic work
    new_work = models.CivicWork(
        booth_id=work_data.booth_id,
        title=work_data.title,
        description=work_data.description,
        category=work_data.category,
        budget=work_data.budget,
        status=work_data.status,
        affected_streets=work_data.affected_streets,
        start_date=datetime.now(timezone.utc) if work_data.status == "Planned" else None
    )
    db.add(new_work)
    db.commit()
    db.refresh(new_work)

    logger.info(f"✅ Civic work created: {new_work.title} (ID: {new_work.id})")

    # Trigger notification engine in background (to avoid delaying response)
    background_tasks.add_task(_create_notifications_and_broadcast, new_work.id, db)

    return new_work


async def _create_notifications_and_broadcast(work_id: int, db: Session):
    """Background task: identify affected citizens, create notifications, broadcast WebSocket event."""
    try:
        work = db.query(models.CivicWork).filter(models.CivicWork.id == work_id).first()
        if not work:
            logger.error(f"Work {work_id} not found for notification creation")
            return

        start_time = datetime.now(timezone.utc)

        # Identify affected citizens
        affected_citizens = notification_service.get_affected_citizens(db, work)

        # Create notifications
        notifications_count = 0
        if affected_citizens:
            notifications_count = notification_service.create_notifications_bulk(
                db, work, affected_citizens
            )

        # Unique booths impacted
        booths_impacted = len(set(c.booth_id for c in affected_citizens))

        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        logger.info(f"🎯 Notification engine: {notifications_count} notifications to {len(affected_citizens)} citizens")
        logger.info(f"⏱️ Background execution time: {execution_time:.0f}ms")

        # Broadcast WebSocket event
        await manager.broadcast({
            "type": "civic_work_created",
            "data": {
                "work_id": work.id,
                "title": work.title,
                "category": work.category,
                "booth_id": work.booth_id,
                "affected_citizens": len(affected_citizens),
                "notifications_created": notifications_count,
                "booths_impacted": booths_impacted,
                "budget": work.budget,
                "execution_time_ms": round(execution_time, 2)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.info("📡 WebSocket event broadcast: civic_work_created")

    except Exception as e:
        logger.error(f"Error in background notification task: {e}", exc_info=True)


# ---------- List Civic Works ----------
@router.get("/", response_model=List[schemas.CivicWorkResponse])
async def get_civic_works(
    booth_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """Get civic works, optionally filtered by booth."""
    query = db.query(models.CivicWork)
    if booth_id:
        query = query.filter(models.CivicWork.booth_id == booth_id)
    works = query.order_by(models.CivicWork.created_at.desc()).offset(skip).limit(limit).all()
    return works


# ---------- Get Single Civic Work ----------
@router.get("/{work_id}", response_model=schemas.CivicWorkDetailResponse)  # need to define this schema
async def get_civic_work_detail(
    work_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """Get detailed information about a civic work, including impact metrics."""
    work = db.query(models.CivicWork).filter(models.CivicWork.id == work_id).first()
    if not work:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Civic work not found")

    # Count notifications sent for this work
    notification_count = db.query(func.count(models.Notification.id)).filter(
        models.Notification.work_id == work_id
    ).scalar() or 0

    # Count affected citizens (using the same logic as notification_service)
    affected_count = len(notification_service.get_affected_citizens(db, work))

    # Return combined data
    return {
        **work.__dict__,
        "notifications_sent": notification_count,
        "citizens_affected": affected_count
    }


# ---------- Update Civic Work Status ----------
@router.patch("/{work_id}/status", response_model=schemas.CivicWorkResponse)
async def update_work_status(
    work_id: int,
    status_update: schemas.WorkStatusUpdate,  # define schema with 'status' field
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin", "StateAdmin", "ConstituencyManager"]))
):
    """Update the status of a civic work."""
    work = db.query(models.CivicWork).filter(models.CivicWork.id == work_id).first()
    if not work:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Civic work not found")

    work.status = status_update.status
    if status_update.status == "Completed" and not work.completion_date:
        work.completion_date = datetime.now(timezone.utc)

    db.commit()
    db.refresh(work)
    return work


# ---------- Delete Civic Work ----------
@router.delete("/{work_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_civic_work(
    work_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["SuperAdmin"]))
):
    """Delete a civic work. Only SuperAdmin can delete."""
    work = db.query(models.CivicWork).filter(models.CivicWork.id == work_id).first()
    if not work:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Civic work not found")

    # Check for associated notifications (optional: cascade delete or forbid)
    notif_count = db.query(models.Notification).filter(models.Notification.work_id == work_id).count()
    if notif_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete civic work with existing notifications. Delete notifications first."
        )

    db.delete(work)
    db.commit()
    return None


# ---------- Notification Endpoints ----------
@router.get("/notifications/summary")
async def get_notifications_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """Get notification statistics for dashboard."""
    return notification_service.get_notification_summary(db)


@router.get("/notifications/recent")
async def get_recent_notifications(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """Get recent notifications with details."""
    notifications = notification_service.get_recent_notifications(db, limit)
    return {"notifications": notifications, "total": len(notifications)}