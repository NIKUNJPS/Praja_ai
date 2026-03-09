from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from database import get_db
import models
import auth
import segmentation_service
import sentiment_service
import influence_service
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

# ---------- Request/Response Models ----------
class SentimentAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    citizen_id: Optional[int] = None

class BatchSentimentRequest(BaseModel):
    limit: int = Field(1000, ge=1, le=10000)

# ---------- Helper: update booth health score (optional) ----------
def _update_booth_health(db: Session, booth_id: int):
    """Recalculate and update health score for a single booth."""
    # (Logic similar to get_booth_health_intelligence, but only update DB)
    # For brevity, we reuse the main function's logic – but to avoid duplication,
    # we could move the core computation to a separate function.
    pass  # We'll keep this simple; the health endpoint already updates DB.

# ---------- Endpoints ----------
@router.get("/booth-health")
async def get_booth_health_intelligence(
    booth_id: Optional[int] = None,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """
    Compute booth health intelligence with AI‑powered scoring.
    Health Score = 0.35*Sentiment + 0.25*Scheme Coverage + 0.20*Civic Works Density + 0.20*Engagement
    """
    try:
        query = db.query(models.Booth)
        if booth_id:
            query = query.filter(models.Booth.id == booth_id)

        booths = query.limit(limit).all()
        results = []

        for booth in booths:
            citizens_count = db.query(func.count(models.Citizen.id)).filter(
                models.Citizen.booth_id == booth.id
            ).scalar() or 0

            if citizens_count == 0:
                results.append({
                    "booth_id": booth.id,
                    "booth_name": booth.name,
                    "health_score": 50.0,
                    "risk_level": "Medium",
                    "sentiment_avg": 0.0,
                    "scheme_coverage": 0.0,
                    "civic_works_count": 0,
                    "engagement_score": 0.0,
                    "complaint_ratio": 0.0,
                    "citizens_count": 0,
                    "top_issues": []
                })
                continue

            # 1. Sentiment Average
            sentiment_data = db.query(
                func.avg(models.SentimentLog.sentiment_score)
            ).join(
                models.Citizen, models.SentimentLog.citizen_id == models.Citizen.id
            ).filter(
                models.Citizen.booth_id == booth.id
            ).scalar()
            sentiment_avg = sentiment_data if sentiment_data else 0.0
            sentiment_normalized = ((sentiment_avg + 1) / 2) * 100

            # 2. Scheme Coverage %
            beneficiaries_count = db.query(func.count(models.Beneficiary.id)).join(
                models.Citizen, models.Beneficiary.citizen_id == models.Citizen.id
            ).filter(
                models.Citizen.booth_id == booth.id,
                models.Beneficiary.status == "Active"
            ).scalar() or 0
            scheme_coverage = (beneficiaries_count / citizens_count * 100) if citizens_count else 0

            # 3. Civic Works Density (normalised)
            civic_works_count = db.query(func.count(models.CivicWork.id)).filter(
                models.CivicWork.booth_id == booth.id
            ).scalar() or 0
            civic_works_density = min((civic_works_count / 20) * 100, 100)  # assume max 20 works

            # 4. Engagement Score (based on activities)
            activities_count = db.query(func.count(models.Activity.id)).join(
                models.Citizen, models.Activity.citizen_id == models.Citizen.id
            ).filter(
                models.Citizen.booth_id == booth.id
            ).scalar() or 0
            engagement_score = min((activities_count / (citizens_count * 10)) * 100, 100) if citizens_count else 0

            # 5. Complaint Ratio
            complaints_count = db.query(func.count(models.Issue.id)).filter(
                models.Issue.booth_id == booth.id,
                models.Issue.status.in_(["Open", "In Progress"])
            ).scalar() or 0
            complaint_ratio = (complaints_count / citizens_count * 100) if citizens_count else 0

            # Composite Health Score
            health_score = (
                0.35 * sentiment_normalized +
                0.25 * scheme_coverage +
                0.20 * civic_works_density +
                0.20 * engagement_score
            ) - (complaint_ratio * 0.5)
            health_score = max(0, min(100, health_score))

            # Risk Level
            if health_score >= 75:
                risk_level = "Low"
            elif health_score >= 50:
                risk_level = "Medium"
            else:
                risk_level = "High"

            # Top Issues
            top_issues = db.query(
                models.Issue.category,
                func.count(models.Issue.id).label('count')
            ).filter(
                models.Issue.booth_id == booth.id,
                models.Issue.status.in_(["Open", "In Progress"])
            ).group_by(models.Issue.category).order_by(func.count(models.Issue.id).desc()).limit(3).all()
            top_issues_list = [{"category": issue.category, "count": issue.count} for issue in top_issues]

            # Update booth in DB
            booth.health_score = round(health_score, 2)
            booth.risk_level = risk_level
            booth.engagement_index = round(engagement_score, 2)
            db.commit()

            results.append({
                "booth_id": booth.id,
                "booth_name": booth.name,
                "booth_code": booth.code,
                "health_score": round(health_score, 2),
                "risk_level": risk_level,
                "sentiment_avg": round(sentiment_avg, 3),
                "scheme_coverage": round(scheme_coverage, 2),
                "civic_works_count": civic_works_count,
                "engagement_score": round(engagement_score, 2),
                "complaint_ratio": round(complaint_ratio, 2),
                "citizens_count": citizens_count,
                "top_issues": top_issues_list
            })

        return {
            "booths": results,
            "total_booths": len(results),
            "avg_health_score": round(sum(b["health_score"] for b in results) / len(results), 2) if results else 0
        }

    except Exception as e:
        logger.error(f"Booth health intelligence error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """Get high‑level dashboard statistics."""
    try:
        total_citizens = db.query(func.count(models.Citizen.id)).scalar() or 0
        total_booths = db.query(func.count(models.Booth.id)).scalar() or 0
        total_civic_works = db.query(func.count(models.CivicWork.id)).scalar() or 0
        avg_health_score = db.query(func.avg(models.Booth.health_score)).scalar() or 0
        active_beneficiaries = db.query(func.count(models.Beneficiary.id)).filter(
            models.Beneficiary.status == "Active"
        ).scalar() or 0
        open_issues = db.query(func.count(models.Issue.id)).filter(
            models.Issue.status.in_(["Open", "In Progress"])
        ).scalar() or 0
        recent_sentiments = db.query(func.avg(models.SentimentLog.sentiment_score)).scalar() or 0

        return {
            "total_citizens": total_citizens,
            "total_booths": total_booths,
            "total_civic_works": total_civic_works,
            "avg_health_score": round(avg_health_score, 2),
            "active_beneficiaries": active_beneficiaries,
            "open_issues": open_issues,
            "sentiment_trend": round(recent_sentiments, 3),
            "scheme_coverage_pct": round((active_beneficiaries / total_citizens * 100), 2) if total_citizens > 0 else 0
        }
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/run-segmentation")
async def run_segmentation(
    method: str = "deterministic",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["Analyst", "SuperAdmin"]))
):
    """
    Run AI segmentation engine.
    Methods: deterministic, kmeans, hybrid
    """
    try:
        if method == "deterministic":
            updated = segmentation_service.deterministic_segmentation(db)
            return {
                "status": "success",
                "method": "deterministic",
                "citizens_updated": updated,
                "message": "Rule‑based segmentation completed"
            }
        elif method == "kmeans":
            updated = segmentation_service.kmeans_refinement(db)
            return {
                "status": "success",
                "method": "kmeans",
                "citizens_updated": updated,
                "message": "KMeans clustering completed"
            }
        elif method == "hybrid":
            updated_det = segmentation_service.deterministic_segmentation(db)
            updated_km = segmentation_service.kmeans_refinement(db)
            return {
                "status": "success",
                "method": "hybrid",
                "citizens_updated": updated_det + updated_km,
                "deterministic_count": updated_det,
                "kmeans_count": updated_km,
                "message": "Hybrid segmentation completed"
            }
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid method")
    except Exception as e:
        logger.error(f"Segmentation error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Segmentation failed")


@router.get("/segment-summary")
async def get_segment_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """Get segment distribution and statistics."""
    try:
        return segmentation_service.get_segment_summary(db)
    except Exception as e:
        logger.error(f"Segment summary error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/analyze-sentiment")
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """Analyze sentiment for a single text (English, Hindi, Marathi)."""
    try:
        pipeline = sentiment_service.SentimentPipeline()
        result = pipeline.process(request.text)

        # If citizen_id provided, store in database (async)
        if request.citizen_id:
            background_tasks.add_task(
                _store_sentiment_log,
                db, request.citizen_id, result
            )

        return result
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analysis failed")


def _store_sentiment_log(db: Session, citizen_id: int, result: dict):
    """Background task to store sentiment log."""
    try:
        citizen = db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
        if not citizen:
            logger.warning(f"Citizen {citizen_id} not found, cannot store sentiment log")
            return

        log = models.SentimentLog(
            citizen_id=citizen_id,
            booth_id=citizen.booth_id,
            text=result['text'],
            language=result['language'],
            sentiment_score=result['sentiment_score'],
            sentiment_label=result['sentiment_label'],
            keywords=result['keywords'],
            logged_at=datetime.now(timezone.utc)
        )
        db.add(log)
        db.commit()
        logger.info(f"Stored sentiment log for citizen {citizen_id}")
    except Exception as e:
        logger.error(f"Failed to store sentiment log: {e}")


@router.post("/batch-sentiment")
async def batch_sentiment_analysis(
    request: BatchSentimentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["Analyst", "SuperAdmin"]))
):
    """Process unanalyzed sentiment logs with ML inference (background)."""
    # Get unprocessed logs (score == 0.0)
    logs = db.query(models.SentimentLog).filter(
        models.SentimentLog.sentiment_score == 0.0
    ).limit(request.limit).all()

    if not logs:
        return {
            "status": "no_data",
            "message": "No unprocessed sentiment logs found",
            "processed": 0
        }

    # Process in background to avoid timeout
    background_tasks.add_task(_process_batch_sentiment, logs, db)

    return {
        "status": "processing",
        "message": f"Processing {len(logs)} logs in background",
        "total_logs": len(logs)
    }


def _process_batch_sentiment(logs: List[models.SentimentLog], db: Session):
    """Background batch processing."""
    pipeline = sentiment_service.SentimentPipeline()
    processed = 0
    for log in logs:
        try:
            result = pipeline.process(log.text)
            log.language = result['language']
            log.sentiment_score = result['sentiment_score']
            log.sentiment_label = result['sentiment_label']
            log.keywords = result['keywords']
            processed += 1
        except Exception as e:
            logger.error(f"Failed to process log {log.id}: {e}")
            continue
    db.commit()
    logger.info(f"Batch processed {processed} sentiment logs")


@router.get("/sentiment-trends")
async def get_sentiment_trends(
    days: int = 30,
    booth_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """Get sentiment trends for last N days with positive/neutral/negative counts."""
    try:
        threshold_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = db.query(models.SentimentLog).filter(models.SentimentLog.logged_at >= threshold_date)
        if booth_id:
            query = query.filter(models.SentimentLog.booth_id == booth_id)

        logs = query.all()
        if not logs:
            return {
                "days": days,
                "booth_id": booth_id,
                "total_logs": 0,
                "sentiment_counts": {"Positive": 0, "Neutral": 0, "Negative": 0},
                "avg_sentiment_score": 0.0,
                "momentum": "neutral"
            }

        sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
        total_score = 0.0
        for log in logs:
            sentiment_counts[log.sentiment_label] = sentiment_counts.get(log.sentiment_label, 0) + 1
            total_score += log.sentiment_score

        avg_score = total_score / len(logs)

        # Momentum (positive/negative ratio)
        neg = sentiment_counts["Negative"]
        pos = sentiment_counts["Positive"]
        if neg > 0:
            momentum_ratio = pos / neg
        else:
            momentum_ratio = pos if pos > 0 else 1.0

        if momentum_ratio > 1.5:
            momentum = "positive"
        elif momentum_ratio < 0.7:
            momentum = "negative"
        else:
            momentum = "neutral"

        # Booth‑wise aggregation (if no booth_id given)
        booth_sentiments = []
        if not booth_id:
            booth_data = db.query(
                models.SentimentLog.booth_id,
                func.count(models.SentimentLog.id).label('count'),
                func.avg(models.SentimentLog.sentiment_score).label('avg_score')
            ).filter(
                models.SentimentLog.logged_at >= threshold_date,
                models.SentimentLog.booth_id.isnot(None)
            ).group_by(
                models.SentimentLog.booth_id
            ).order_by(
                func.count(models.SentimentLog.id).desc()
            ).limit(10).all()

            for bid, count, avg_score in booth_data:
                booth = db.query(models.Booth).filter(models.Booth.id == bid).first()
                if booth:
                    booth_sentiments.append({
                        "booth_id": bid,
                        "booth_name": booth.name,
                        "sentiment_count": count,
                        "avg_sentiment_score": round(float(avg_score), 3)
                    })

        return {
            "days": days,
            "booth_id": booth_id,
            "total_logs": len(logs),
            "sentiment_counts": sentiment_counts,
            "avg_sentiment_score": round(avg_score, 3),
            "avg_sentiment_normalized": round(((avg_score + 1) / 2) * 100, 2),
            "momentum": momentum,
            "booth_sentiments": booth_sentiments
        }
    except Exception as e:
        logger.error(f"Sentiment trends error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/segments-distribution")
async def get_segments_distribution(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """Get detailed segment distribution for visualizations."""
    try:
        summary = segmentation_service.get_segment_summary(db)
        return {
            "segments": summary["segment_distribution"],
            "total_citizens": summary["total_citizens"],
            "coverage": summary["segmentation_coverage"],
            "avg_confidence": summary["avg_confidence"]
        }
    except Exception as e:
        logger.error(f"Segments distribution error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/run-influence")
async def run_influence_scoring(
    mode: str = "demo",
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(["Analyst", "SuperAdmin"]))
):
    """Run influence scoring engine with NetworkX. Mode: 'full' or 'demo'."""
    try:
        result = influence_service.run_influence_scoring(db, mode=mode, limit=limit)
        return result
    except Exception as e:
        logger.error(f"Influence scoring error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Influence scoring failed")


@router.get("/top-influencers")
async def get_top_influencers(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """Get top influencers with enriched data."""
    try:
        influencers = influence_service.get_top_influencers(db, limit=limit)
        return {"influencers": influencers, "total": len(influencers)}
    except Exception as e:
        logger.error(f"Top influencers error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/booth-influence-summary")
async def get_booth_influence_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """Get booth‑level influence statistics."""
    try:
        return influence_service.get_booth_influence_summary(db)
    except Exception as e:
        logger.error(f"Booth influence summary error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")