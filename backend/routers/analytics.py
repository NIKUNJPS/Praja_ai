from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from database import get_db
import models

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

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
