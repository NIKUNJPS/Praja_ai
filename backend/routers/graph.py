"""
Knowledge Graph API for React Flow Visualization
Production-grade graph endpoint with smart node selection
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, cast
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional, Dict
import random
import math
import logging
from database import get_db
import models
import auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/graph", tags=["Graph"])


def calculate_position(index: int, total: int, radius: float = 400) -> Dict[str, float]:
    """Generate circular layout positions."""
    angle = (2 * math.pi * index) / total
    return {"x": radius * math.cos(angle), "y": radius * math.sin(angle)}


def select_smart_nodes(
    db: Session,
    limit: int,
    booth_id: Optional[int],
    min_influence: Optional[float],
    segment: Optional[str]
) -> List[models.Citizen]:
    """
    Smart node selection algorithm.
    Priority: top influencers → booth leaders → representative → sampled.
    """
    # Base query
    query = db.query(models.Citizen).filter(models.Citizen.influence_score > 0)
    if booth_id:
        query = query.filter(models.Citizen.booth_id == booth_id)
    if min_influence:
        query = query.filter(models.Citizen.influence_score >= min_influence)
    if segment:
        # Use JSONB contains (PostgreSQL specific)
        query = query.filter(cast(models.Citizen.segment_tags, JSONB).contains([segment]))

    selected_citizens = []

    # 1. Top influencers (up to 20)
    top_influencers = query.order_by(models.Citizen.influence_score.desc()).limit(20).all()
    selected_citizens.extend(top_influencers)

    if len(selected_citizens) >= limit:
        return selected_citizens[:limit]

    # 2. Booth leaders (one per booth) – only if not filtering by a single booth
    if not booth_id:
        # Get distinct booth IDs that have at least one citizen in the current query
        booth_ids_subquery = query.with_entities(models.Citizen.booth_id).distinct().subquery()
        booths = db.query(models.Booth).filter(models.Booth.id.in_(booth_ids_subquery)).all()
        for booth in booths:
            if len(selected_citizens) >= limit:
                break
            leader = query.filter(
                models.Citizen.booth_id == booth.id
            ).order_by(models.Citizen.influence_score.desc()).first()
            if leader and leader not in selected_citizens:
                selected_citizens.append(leader)

    # 3. Representative citizens by segment
    segments = ["Youth", "Farmer", "Business", "Women", "Senior Citizen", "Urban Poor", "Community Leader"]
    for seg in segments:
        if len(selected_citizens) >= limit:
            break
        seg_citizens = query.filter(
            cast(models.Citizen.segment_tags, JSONB).contains([seg])
        ).limit(5).all()
        for citizen in seg_citizens:
            if citizen not in selected_citizens and len(selected_citizens) < limit:
                selected_citizens.append(citizen)

    # 4. Fill remainder with random sampling
    if len(selected_citizens) < limit:
        remaining = limit - len(selected_citizens)
        excluded_ids = [c.id for c in selected_citizens]
        candidates = query.filter(~models.Citizen.id.in_(excluded_ids)).limit(remaining * 3).all()
        if candidates:
            sampled = random.sample(candidates, min(remaining, len(candidates)))
            selected_citizens.extend(sampled)

    return selected_citizens[:limit]


@router.get("/network")
async def get_network_graph(
    limit: int = Query(300, ge=50, le=500),
    booth_id: Optional[int] = None,
    min_influence: Optional[float] = None,
    segment: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """
    Get knowledge graph data in React Flow format.
    Smart node selection with server-side filtering.
    """
    try:
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

        # Pre‑fetch booths for all citizens (one query)
        booth_ids = set(c.booth_id for c in citizens)
        booths = {b.id: b for b in db.query(models.Booth).filter(models.Booth.id.in_(booth_ids)).all()}

        # Build nodes
        nodes = []
        segment_colors = {
            "Youth": "#3B82F6",        # blue
            "Women": "#EC4899",        # pink
            "Senior Citizen": "#F59E0B", # amber
            "Business": "#A855F7",      # purple
            "Farmer": "#10B981",        # green
            "Urban Poor": "#EF4444",    # red
            "Community Leader": "#8B5CF6", # violet
            "Scheme Beneficiary": "#06B6D4" # cyan
        }

        for idx, citizen in enumerate(citizens):
            primary_segment = citizen.segment_tags[0] if citizen.segment_tags else "Unknown"
            booth = booths.get(citizen.booth_id)
            node_size = 10 + (citizen.influence_score / 100) * 30
            position = calculate_position(idx, len(citizens), radius=600)

            nodes.append({
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
            })

        # Build edges
        edges = []
        edge_id_counter = 0

        # Get graph edges involving selected citizens
        graph_edges = db.query(models.GraphEdge).filter(
            models.GraphEdge.source_id.in_(citizen_ids),
            models.GraphEdge.target_id.in_(citizen_ids)
        ).limit(1000).all()

        for edge in graph_edges:
            source_id = str(edge.source_id)
            target_id = str(edge.target_id)
            if source_id in [n["id"] for n in nodes] and target_id in [n["id"] for n in nodes]:
                edges.append({
                    "id": f"e{edge_id_counter}",
                    "source": source_id,
                    "target": target_id,
                    "label": edge.relationship,
                    "weight": edge.weight,
                    "animated": edge.weight > 0.3,
                    "style": {
                        "strokeWidth": 1 + (edge.weight * 3),
                        "stroke": "#3B82F6" if edge.weight > 0.3 else "#6B7280"
                    }
                })
                edge_id_counter += 1

        # If no graph edges, create proximity edges (same booth)
        if not edges:
            # Group citizens by booth
            booth_groups = {}
            for citizen in citizens:
                booth_groups.setdefault(citizen.booth_id, []).append(citizen)

            for bid, group in booth_groups.items():
                # Connect first few citizens in each booth
                for i in range(min(5, len(group))):
                    for j in range(i + 1, min(i + 3, len(group))):
                        edges.append({
                            "id": f"e{edge_id_counter}",
                            "source": str(group[i].id),
                            "target": str(group[j].id),
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

    except Exception as e:
        logger.error(f"Error generating network graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate graph data"
        )


@router.get("/citizen/{citizen_id}")
async def get_citizen_detail(
    citizen_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_verified_user)
):
    """Get detailed citizen information for graph node click."""
    try:
        citizen = db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
        if not citizen:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citizen not found")

        # Booth
        booth = db.query(models.Booth).filter(models.Booth.id == citizen.booth_id).first()

        # Sentiment summary
        sentiment_avg = db.query(func.avg(models.SentimentLog.sentiment_score)).filter(
            models.SentimentLog.citizen_id == citizen_id
        ).scalar() or 0
        sentiment_count = db.query(func.count(models.SentimentLog.id)).filter(
            models.SentimentLog.citizen_id == citizen_id
        ).scalar() or 0

        # Schemes
        schemes = db.query(models.GovernmentScheme).join(
            models.Beneficiary
        ).filter(
            models.Beneficiary.citizen_id == citizen_id
        ).all()

        # Recent activities
        activities = db.query(models.Activity).filter(
            models.Activity.citizen_id == citizen_id
        ).order_by(models.Activity.timestamp.desc()).limit(5).all()

        # Determine sentiment label
        if sentiment_avg > 0.3:
            sentiment_label = "Positive"
        elif sentiment_avg < -0.3:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"

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
                "label": sentiment_label
            },
            "schemes": [{"id": s.id, "name": s.name, "category": s.category} for s in schemes],
            "recent_activities": [
                {
                    "type": a.activity_type,
                    "description": a.description,
                    "timestamp": a.timestamp.isoformat() if a.timestamp else None
                } for a in activities
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching citizen detail {citizen_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve citizen details"
        )