"""
Civic Works Router
Trigger hyper-local notification engine on civic work creation
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from database import get_db
import models
import notification_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/civic-works", tags=["Civic Works"])


class CivicWorkCreate(BaseModel):
    booth_id: int
    title: str
    description: Optional[str] = None
    category: str
    budget: float = 0.0
    status: str = "Planned"
    affected_streets: List[int] = []


class CivicWorkResponse(BaseModel):
    civic_work_id: int
    title: str
    category: str
    affected_citizens: int
    notifications_created: int
    booths_impacted: int
    execution_time_ms: float
    
    class Config:
        from_attributes = True


@router.post("/create", response_model=CivicWorkResponse)
async def create_civic_work_with_notifications(
    work_data: CivicWorkCreate,
    db: Session = Depends(get_db)
):
    """
    Create civic work and automatically trigger hyper-local notification engine
    
    Flow:
    1. Create civic work
    2. Identify affected citizens
    3. Generate multilingual messages
    4. Create notifications
    5. Return execution summary
    """
    
    start_time = datetime.now(timezone.utc)
    
    # 1. Create civic work
    new_work = models.CivicWork(
        booth_id=work_data.booth_id,
        title=work_data.title,
        description=work_data.description,
        category=work_data.category,
        budget=work_data.budget,
        status=work_data.status,
        affected_streets=work_data.affected_streets,
        start_date=datetime.now(timezone.utc)
    )
    
    db.add(new_work)
    db.commit()
    db.refresh(new_work)
    
    logger.info(f"✅ Civic work created: {new_work.title} (ID: {new_work.id})")
    
    # 2. Identify affected citizens
    affected_citizens = notification_service.get_affected_citizens(db, new_work)
    
    # 3. Generate and create notifications
    notifications_count = 0
    if affected_citizens:
        notifications_count = notification_service.create_notifications_bulk(
            db, new_work, affected_citizens
        )
    
    # 4. Get unique booths impacted
    booths_impacted = len(set(c.booth_id for c in affected_citizens))
    
    end_time = datetime.now(timezone.utc)
    execution_time_ms = (end_time - start_time).total_seconds() * 1000
    
    logger.info(f"🎯 Notification engine: {notifications_count} notifications to {len(affected_citizens)} citizens")
    logger.info(f"⏱️ Total execution time: {execution_time_ms:.0f}ms")
    
    return {
        "civic_work_id": new_work.id,
        "title": new_work.title,
        "category": new_work.category,
        "affected_citizens": len(affected_citizens),
        "notifications_created": notifications_count,
        "booths_impacted": booths_impacted,
        "execution_time_ms": round(execution_time_ms, 2)
    }


@router.get("/")
async def get_civic_works(
    booth_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get civic works with optional booth filter"""
    
    query = db.query(models.CivicWork)
    
    if booth_id:
        query = query.filter(models.CivicWork.booth_id == booth_id)
    
    works = query.order_by(models.CivicWork.created_at.desc()).limit(limit).all()
    
    return {
        "works": [
            {
                "id": w.id,
                "booth_id": w.booth_id,
                "title": w.title,
                "category": w.category,
                "budget": w.budget,
                "status": w.status,
                "affected_streets": w.affected_streets,
                "created_at": w.created_at
            }
            for w in works
        ],
        "total": len(works)
    }


@router.get("/{work_id}")
async def get_civic_work_detail(work_id: int, db: Session = Depends(get_db)):
    """Get detailed civic work information"""
    
    work = db.query(models.CivicWork).filter(models.CivicWork.id == work_id).first()
    
    if not work:
        return {"error": "Civic work not found"}
    
    # Get notification count
    notification_count = db.query(models.func.count(models.Notification.id)).filter(
        models.Notification.work_id == work_id
    ).scalar() or 0
    
    # Get affected citizens count
    affected_count = len(notification_service.get_affected_citizens(db, work))
    
    return {
        "work": {
            "id": work.id,
            "booth_id": work.booth_id,
            "title": work.title,
            "description": work.description,
            "category": work.category,
            "budget": work.budget,
            "status": work.status,
            "affected_streets": work.affected_streets,
            "start_date": work.start_date,
            "completion_date": work.completion_date,
            "created_at": work.created_at
        },
        "impact": {
            "notifications_sent": notification_count,
            "citizens_affected": affected_count
        }
    }


@router.get("/notifications/summary")
async def get_notifications_summary(db: Session = Depends(get_db)):
    """Get notification statistics for dashboard"""
    
    return notification_service.get_notification_summary(db)


@router.get("/notifications/recent")
async def get_recent_notifications(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get recent notifications with details"""
    
    notifications = notification_service.get_recent_notifications(db, limit)
    
    return {
        "notifications": notifications,
        "total": len(notifications)
    }
