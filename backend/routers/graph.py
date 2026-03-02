"""
Knowledge Graph API for React Flow Visualization
Production-grade graph endpoint with smart node selection
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Dict, Optional
import random
import math
from database import get_db
import models

router = APIRouter(prefix="/api/graph", tags=["Graph"])


def calculate_position(index: int, total: int, radius: float = 400) -> Dict[str, float]:
    """Generate circular layout positions"""
    angle = (2 * math.pi * index) / total
    return {
        "x": radius * math.cos(angle),
        "y": radius * math.sin(angle)
    }


def select_smart_nodes(
    db: Session,
    limit: int,
    booth_id: Optional[int],
    min_influence: Optional[float],
    segment: Optional[str]
) -> List[models.Citizen]:
    """
    Smart node selection algorithm
    Priority: top influencers → booth leaders → representative → sampled
    """
    
    selected_citizens = []
    
    # 1. Top influencers (always include top 20)
    query = db.query(models.Citizen).filter(models.Citizen.influence_score > 0)
    
    if booth_id:
        query = query.filter(models.Citizen.booth_id == booth_id)
    if min_influence:
        query = query.filter(models.Citizen.influence_score >= min_influence)
    if segment:
        # Fix: Use JSON contains operator
        from sqlalchemy.dialects.postgresql import JSONB
        query = query.filter(models.Citizen.segment_tags.cast(JSONB).contains([segment]))
    
    top_influencers = query.order_by(models.Citizen.influence_score.desc()).limit(20).all()
    selected_citizens.extend(top_influencers)
    
    if len(selected_citizens) >= limit:
        return selected_citizens[:limit]
    
    # 2. Booth leaders (top from each booth)
    if not booth_id:  # Only if not filtering by specific booth
        booths = db.query(models.Booth).limit(30).all()
        for booth in booths:
            if len(selected_citizens) >= limit:
                break
            
            booth_leader = db.query(models.Citizen).filter(
                models.Citizen.booth_id == booth.id,
                models.Citizen.influence_score > 0
            ).order_by(models.Citizen.influence_score.desc()).first()
            
            if booth_leader and booth_leader not in selected_citizens:
                selected_citizens.append(booth_leader)
    
    # 3. Representative citizens by segment
    from sqlalchemy.dialects.postgresql import JSONB
    segments = ["Youth", "Farmer", "Business", "Women", "Senior Citizen", "Urban Poor", "Community Leader"]
    for seg in segments:
        if len(selected_citizens) >= limit:
            break
        
        seg_citizens = query.filter(
            models.Citizen.segment_tags.cast(JSONB).contains([seg])
        ).limit(5).all()
        
        for citizen in seg_citizens:
            if citizen not in selected_citizens and len(selected_citizens) < limit:
                selected_citizens.append(citizen)
    
    # 4. Fill remainder with random sampling
    if len(selected_citizens) < limit:
        remaining = limit - len(selected_citizens)
        all_ids = [c.id for c in selected_citizens]
        
        additional = query.filter(
            ~models.Citizen.id.in_(all_ids)
        ).limit(remaining * 3).all()  # Get more for sampling
        
        if additional:
            sampled = random.sample(additional, min(remaining, len(additional)))
            selected_citizens.extend(sampled)
    
    return selected_citizens[:limit]


@router.get("/network")
async def get_network_graph(
    limit: int = Query(300, ge=50, le=500),
    booth_id: Optional[int] = None,
    min_influence: Optional[float] = None,
    segment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get knowledge graph data in React Flow format
    Smart node selection with server-side filtering
    """
    
    # Select nodes intelligently
    citizens = select_smart_nodes(db, limit, booth_id, min_influence, segment)
    
    if not citizens:
        return {
            "nodes": [],
            "edges": [],
            "meta": {
                "total_nodes": 0,
                "total_edges": 0,
                "avg_influence": 0
            }
        }
    
    citizen_ids = [c.id for c in citizens]
    
    # Build nodes
    nodes = []
    segment_colors = {
        "Youth": "#3B82F6",  # blue
        "Women": "#EC4899",  # pink
        "Senior Citizen": "#F59E0B",  # amber
        "Business": "#A855F7",  # purple
        "Farmer": "#10B981",  # green
        "Urban Poor": "#EF4444",  # red
        "Community Leader": "#8B5CF6",  # violet
        "Scheme Beneficiary": "#06B6D4"  # cyan
    }
    
    for idx, citizen in enumerate(citizens):
        # Get primary segment
        primary_segment = citizen.segment_tags[0] if citizen.segment_tags else "Unknown"
        
        # Get booth info
        booth = db.query(models.Booth).filter(models.Booth.id == citizen.booth_id).first()
        
        # Calculate node size based on influence (10-40px)
        node_size = 10 + (citizen.influence_score / 100) * 30
        
        # Position hint (circular layout)
        position = calculate_position(idx, len(citizens), radius=600)
        
        node = {
            "id": str(citizen.id),
            "type": "citizen",
            "position": position,
            "data": {
                "label": citizen.name,
                "name": citizen.name,
                "influence_score": citizen.influence_score,
                "influence_rank": citizen.influence_rank,
                "primary_segment": primary_segment,
                "segments": citizen.segment_tags,
                "booth_id": citizen.booth_id,
                "booth_name": booth.name if booth else "Unknown",
                "age": citizen.age,
                "occupation": citizen.occupation,
                "color": segment_colors.get(primary_segment, "#6B7280"),
                "size": node_size,
                "is_top_influencer": citizen.influence_rank <= 10
            }
        }
        
        nodes.append(node)
    
    # Build edges from relationships
    edges = []
    edge_id_counter = 0
    
    # Get graph edges for selected citizens
    graph_edges = db.query(models.GraphEdge).filter(
        models.GraphEdge.source_id.in_(citizen_ids),
        models.GraphEdge.target_id.in_(citizen_ids)
    ).limit(1000).all()  # Limit edges for performance
    
    for edge in graph_edges:
        if str(edge.source_id) in [n["id"] for n in nodes] and str(edge.target_id) in [n["id"] for n in nodes]:
            edges.append({
                "id": f"e{edge_id_counter}",
                "source": str(edge.source_id),
                "target": str(edge.target_id),
                "label": edge.relationship,
                "weight": edge.weight,
                "animated": edge.weight > 0.3,  # Animate strong connections
                "style": {
                    "strokeWidth": 1 + (edge.weight * 3),  # 1-4px based on weight
                    "stroke": "#3B82F6" if edge.weight > 0.3 else "#6B7280"
                }
            })
            edge_id_counter += 1
    
    # If no graph edges, create proximity edges (same booth)
    if not edges:
        # Create edges between citizens in same booth
        booth_groups = {}
        for citizen in citizens:
            if citizen.booth_id not in booth_groups:
                booth_groups[citizen.booth_id] = []
            booth_groups[citizen.booth_id].append(citizen)
        
        for booth_id, booth_citizens in booth_groups.items():
            # Connect first few citizens in each booth
            for i in range(min(5, len(booth_citizens))):
                for j in range(i + 1, min(i + 3, len(booth_citizens))):
                    edges.append({
                        "id": f"e{edge_id_counter}",
                        "source": str(booth_citizens[i].id),
                        "target": str(booth_citizens[j].id),
                        "label": "same_booth",
                        "weight": 0.2,
                        "animated": False,
                        "style": {
                            "strokeWidth": 1,
                            "stroke": "#6B7280"
                        }
                    })
                    edge_id_counter += 1
    
    # Calculate metadata
    influence_scores = [c.influence_score for c in citizens if c.influence_score > 0]
    avg_influence = sum(influence_scores) / len(influence_scores) if influence_scores else 0
    
    return {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "avg_influence": round(avg_influence, 2),
            "top_influencer": {
                "name": citizens[0].name if citizens else None,
                "score": citizens[0].influence_score if citizens else 0
            }
        }
    }


@router.get("/citizen/{citizen_id}")
async def get_citizen_detail(citizen_id: int, db: Session = Depends(get_db)):
    """Get detailed citizen information for graph node click"""
    
    citizen = db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
    
    if not citizen:
        return {"error": "Citizen not found"}
    
    # Get booth
    booth = db.query(models.Booth).filter(models.Booth.id == citizen.booth_id).first()
    
    # Get sentiment summary
    sentiment_avg = db.query(func.avg(models.SentimentLog.sentiment_score)).filter(
        models.SentimentLog.citizen_id == citizen_id
    ).scalar() or 0
    
    sentiment_count = db.query(func.count(models.SentimentLog.id)).filter(
        models.SentimentLog.citizen_id == citizen_id
    ).scalar() or 0
    
    # Get scheme participation
    schemes = db.query(models.GovernmentScheme).join(
        models.Beneficiary
    ).filter(
        models.Beneficiary.citizen_id == citizen_id
    ).all()
    
    # Get recent activities
    activities = db.query(models.Activity).filter(
        models.Activity.citizen_id == citizen_id
    ).order_by(models.Activity.timestamp.desc()).limit(5).all()
    
    return {
        "citizen": {
            "id": citizen.id,
            "name": citizen.name,
            "age": citizen.age,
            "gender": citizen.gender,
            "occupation": citizen.occupation,
            "phone": citizen.phone,
            "language_preference": citizen.language_preference
        },
        "influence": {
            "score": citizen.influence_score,
            "rank": citizen.influence_rank,
            "last_updated": citizen.last_influence_updated
        },
        "segments": citizen.segment_tags,
        "booth": {
            "id": booth.id if booth else None,
            "name": booth.name if booth else "Unknown",
            "health_score": booth.health_score if booth else 0
        },
        "sentiment": {
            "avg_score": round(sentiment_avg, 3),
            "count": sentiment_count,
            "label": "Positive" if sentiment_avg > 0.3 else "Negative" if sentiment_avg < -0.3 else "Neutral"
        },
        "schemes": [{"id": s.id, "name": s.name, "category": s.category} for s in schemes],
        "recent_activities": [
            {
                "type": a.activity_type,
                "description": a.description,
                "timestamp": a.timestamp
            } for a in activities
        ]
    }
