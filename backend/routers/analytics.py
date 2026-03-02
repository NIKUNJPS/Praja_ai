from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from database import get_db
import models
import segmentation_service
import sentiment_service
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

# Request models
class SentimentAnalysisRequest(BaseModel):
    text: str
    citizen_id: Optional[int] = None
    
class BatchSentimentRequest(BaseModel):
    limit: int = 1000

@router.get("/booth-health")
async def get_booth_health_intelligence(
    booth_id: int = None,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    """
    Compute booth health intelligence with AI-powered scoring
    
    Health Score = 0.35 * Sentiment + 0.25 * Scheme Coverage + 
                   0.20 * Civic Works Density + 0.20 * Engagement Score
    """
    
    query = db.query(models.Booth)
    if booth_id:
        query = query.filter(models.Booth.id == booth_id)
    
    booths = query.limit(limit).all()
    
    results = []
    for booth in booths:
        # Get citizens count
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
        
        # 1. Sentiment Average (weighted)
        sentiment_data = db.query(
            func.avg(models.SentimentLog.sentiment_score)
        ).join(
            models.Citizen, models.SentimentLog.citizen_id == models.Citizen.id
        ).filter(
            models.Citizen.booth_id == booth.id
        ).scalar()
        
        sentiment_avg = sentiment_data if sentiment_data else 0.0
        # Normalize from -1,1 to 0,100
        sentiment_normalized = ((sentiment_avg + 1) / 2) * 100
        
        # 2. Scheme Coverage %
        beneficiaries_count = db.query(func.count(models.Beneficiary.id)).join(
            models.Citizen, models.Beneficiary.citizen_id == models.Citizen.id
        ).filter(
            models.Citizen.booth_id == booth.id,
            models.Beneficiary.status == "Active"
        ).scalar() or 0
        
        scheme_coverage = (beneficiaries_count / citizens_count * 100) if citizens_count > 0 else 0
        
        # 3. Civic Works Count & Density
        civic_works_count = db.query(func.count(models.CivicWork.id)).filter(
            models.CivicWork.booth_id == booth.id
        ).scalar() or 0
        
        # Normalize works count (assuming max 20 works per booth)
        civic_works_density = min((civic_works_count / 20) * 100, 100)
        
        # 4. Engagement Score (based on activity logs)
        activities_count = db.query(func.count(models.Activity.id)).join(
            models.Citizen, models.Activity.citizen_id == models.Citizen.id
        ).filter(
            models.Citizen.booth_id == booth.id
        ).scalar() or 0
        
        # Normalize activity (assuming 10 activities per citizen is high engagement)
        engagement_score = min((activities_count / (citizens_count * 10)) * 100, 100) if citizens_count > 0 else 0
        
        # 5. Complaint Ratio
        complaints_count = db.query(func.count(models.Issue.id)).filter(
            models.Issue.booth_id == booth.id,
            models.Issue.status.in_(["Open", "In Progress"])
        ).scalar() or 0
        
        complaint_ratio = (complaints_count / citizens_count * 100) if citizens_count > 0 else 0
        
        # Compute Composite Health Score
        health_score = (
            0.35 * sentiment_normalized +
            0.25 * scheme_coverage +
            0.20 * civic_works_density +
            0.20 * engagement_score
        )
        
        # Adjust for complaints (penalty)
        health_score = max(0, health_score - (complaint_ratio * 0.5))
        
        # Determine Risk Level
        if health_score >= 75:
            risk_level = "Low"
        elif health_score >= 50:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        # Get Top Issues
        top_issues = db.query(
            models.Issue.category,
            func.count(models.Issue.id).label('count')
        ).filter(
            models.Issue.booth_id == booth.id,
            models.Issue.status.in_(["Open", "In Progress"])
        ).group_by(
            models.Issue.category
        ).order_by(
            func.count(models.Issue.id).desc()
        ).limit(3).all()
        
        top_issues_list = [{"category": issue.category, "count": issue.count} for issue in top_issues]
        
        # Update booth health score in database
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

@router.get("/dashboard-stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get high-level dashboard statistics"""
    
    total_citizens = db.query(func.count(models.Citizen.id)).scalar() or 0
    total_booths = db.query(func.count(models.Booth.id)).scalar() or 0
    total_civic_works = db.query(func.count(models.CivicWork.id)).scalar() or 0
    
    avg_health_score = db.query(func.avg(models.Booth.health_score)).scalar() or 0
    
    # Active schemes
    active_beneficiaries = db.query(func.count(models.Beneficiary.id)).filter(
        models.Beneficiary.status == "Active"
    ).scalar() or 0
    
    # Open issues
    open_issues = db.query(func.count(models.Issue.id)).filter(
        models.Issue.status.in_(["Open", "In Progress"])
    ).scalar() or 0
    
    # Recent sentiment trend
    recent_sentiments = db.query(
        func.avg(models.SentimentLog.sentiment_score)
    ).scalar() or 0
    
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


@router.post("/run-segmentation")
async def run_segmentation(
    method: str = "deterministic",
    db: Session = Depends(get_db)
):
    """
    Run AI segmentation engine
    Methods: deterministic, kmeans, hybrid
    """
    
    if method == "deterministic":
        updated = segmentation_service.deterministic_segmentation(db)
        return {
            "status": "success",
            "method": "deterministic",
            "citizens_updated": updated,
            "message": "Rule-based segmentation completed"
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
        # Run deterministic first, then KMeans
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
        return {"status": "error", "message": "Invalid method"}

@router.get("/segment-summary")
async def get_segment_summary(db: Session = Depends(get_db)):
    """Get segment distribution and statistics"""
    return segmentation_service.get_segment_summary(db)

@router.post("/analyze-sentiment")
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze sentiment for a single text. Supports English, Hindi, Marathi"""
    
    pipeline = sentiment_service.SentimentPipeline()
    result = pipeline.process(request.text)
    
    # If citizen_id provided, store in database
    if request.citizen_id:
        citizen = db.query(models.Citizen).filter(models.Citizen.id == request.citizen_id).first()
        
        if citizen:
            sentiment_log = models.SentimentLog(
                citizen_id=request.citizen_id,
                booth_id=citizen.booth_id,
                text=result['text'],
                language=result['language'],
                sentiment_score=result['sentiment_score'],
                sentiment_label=result['sentiment_label'],
                keywords=result['keywords'],
                logged_at=datetime.now(timezone.utc)
            )
            db.add(sentiment_log)
            db.commit()
            db.refresh(sentiment_log)
            
            result['stored'] = True
            result['sentiment_log_id'] = sentiment_log.id
    
    return result

@router.post("/batch-sentiment")
async def batch_sentiment_analysis(
    request: BatchSentimentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process unanalyzed sentiment logs with ML inference"""
    
    # Get unprocessed sentiment logs (score = 0.0)
    logs = db.query(models.SentimentLog).filter(
        models.SentimentLog.sentiment_score == 0.0
    ).limit(request.limit).all()
    
    if not logs:
        return {
            "status": "no_data",
            "message": "No unprocessed sentiment logs found",
            "processed": 0
        }
    
    pipeline = sentiment_service.SentimentPipeline()
    processed_count = 0
    
    for log in logs:
        try:
            # Run sentiment analysis
            result = pipeline.process(log.text)
            
            # Update log
            log.language = result['language']
            log.sentiment_score = result['sentiment_score']
            log.sentiment_label = result['sentiment_label']
            log.keywords = result['keywords']
            
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Failed to process sentiment log {log.id}: {e}")
            continue
    
    db.commit()
    
    return {
        "status": "success",
        "processed": processed_count,
        "total_logs": len(logs),
        "message": f"Processed {processed_count} sentiment logs"
    }

@router.get("/sentiment-trends")
async def get_sentiment_trends(
    days: int = 30,
    booth_id: int = None,
    db: Session = Depends(get_db)
):
    """Get sentiment trends for last N days with positive/neutral/negative counts"""
    
    # Calculate date threshold
    threshold_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Base query
    query = db.query(models.SentimentLog).filter(
        models.SentimentLog.logged_at >= threshold_date
    )
    
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
    
    # Count by sentiment label
    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    total_score = 0.0
    
    for log in logs:
        sentiment_counts[log.sentiment_label] = sentiment_counts.get(log.sentiment_label, 0) + 1
        total_score += log.sentiment_score
    
    avg_score = total_score / len(logs) if logs else 0
    
    # Calculate momentum (positive/negative ratio)
    if sentiment_counts["Negative"] > 0:
        momentum_ratio = sentiment_counts["Positive"] / sentiment_counts["Negative"]
    else:
        momentum_ratio = sentiment_counts["Positive"] if sentiment_counts["Positive"] > 0 else 1.0
    
    if momentum_ratio > 1.5:
        momentum = "positive"
    elif momentum_ratio < 0.7:
        momentum = "negative"
    else:
        momentum = "neutral"
    
    # Booth-wise aggregation
    booth_sentiments = []
    if not booth_id:
        # Get top 10 booths by sentiment activity
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
        
        for booth_id, count, avg_score in booth_data:
            booth = db.query(models.Booth).filter(models.Booth.id == booth_id).first()
            if booth:
                booth_sentiments.append({
                    "booth_id": booth_id,
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
        "booth_sentiments": booth_sentiments[:10]
    }

import logging
logger = logging.getLogger(__name__)

@router.get("/segments-distribution")
async def get_segments_distribution(db: Session = Depends(get_db)):
    """
    Get detailed segment distribution for visualizations
    """
    summary = segmentation_service.get_segment_summary(db)
    return {
        "segments": summary["segment_distribution"],
        "total_citizens": summary["total_citizens"],
        "coverage": summary["segmentation_coverage"],
        "avg_confidence": summary["avg_confidence"]
    }
