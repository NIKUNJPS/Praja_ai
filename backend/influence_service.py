"""
Key Citizen Influence Scoring Engine
NetworkX-based graph analysis for power network intelligence
"""

import networkx as nx
import numpy as np
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List, Tuple
import logging
import models

logger = logging.getLogger(__name__)

# Configurable edge weights
EDGE_WEIGHTS = {
    'same_street': 0.4,
    'same_booth': 0.2,
    'shared_scheme': 0.25,
    'shared_activity': 0.15
}

# Centrality weights for composite score
CENTRALITY_WEIGHTS = {
    'degree': 0.4,
    'betweenness': 0.3,
    'eigenvector': 0.3
}


class InfluenceGraphBuilder:
    """Build citizen relationship graph from PostgreSQL data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.graph = nx.Graph()
    
    def build_graph(self, limit: int = None) -> nx.Graph:
        """
        Construct NetworkX graph from citizen relationships
        Returns: NetworkX Graph with weighted edges
        """
        
        logger.info("Building citizen influence graph...")
        
        # Get citizens
        query = self.db.query(models.Citizen)
        if limit:
            query = query.limit(limit)
        
        citizens = query.all()
        logger.info(f"Loaded {len(citizens)} citizens")
        
        # Add nodes
        for citizen in citizens:
            self.graph.add_node(
                citizen.id,
                name=citizen.name,
                booth_id=citizen.booth_id,
                street_id=citizen.street_id,
                age=citizen.age,
                occupation=citizen.occupation
            )
        
        # Build edges
        self._add_street_edges(citizens)
        self._add_booth_edges(citizens)
        self._add_scheme_edges()
        self._add_activity_edges()
        
        logger.info(f"Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        
        return self.graph
    
    def _add_street_edges(self, citizens: List):
        """Add edges for citizens on same street"""
        
        street_groups = {}
        for citizen in citizens:
            if citizen.street_id:
                if citizen.street_id not in street_groups:
                    street_groups[citizen.street_id] = []
                street_groups[citizen.street_id].append(citizen.id)
        
        edge_count = 0
        for street_id, citizen_ids in street_groups.items():
            # Connect all citizens on same street
            for i in range(len(citizen_ids)):
                for j in range(i + 1, len(citizen_ids)):
                    self.graph.add_edge(
                        citizen_ids[i],
                        citizen_ids[j],
                        weight=EDGE_WEIGHTS['same_street'],
                        relationship='same_street'
                    )
                    edge_count += 1
        
        logger.info(f"Added {edge_count} same-street edges")
    
    def _add_booth_edges(self, citizens: List):
        """Add edges for citizens in same booth"""
        
        booth_groups = {}
        for citizen in citizens:
            if citizen.booth_id not in booth_groups:
                booth_groups[citizen.booth_id] = []
            booth_groups[citizen.booth_id].append(citizen.id)
        
        edge_count = 0
        for booth_id, citizen_ids in booth_groups.items():
            # Sample connections to avoid O(N²) explosion
            # Connect each citizen to max 20 random booth-mates
            for cid in citizen_ids:
                sample_size = min(20, len(citizen_ids) - 1)
                if sample_size > 0:
                    connections = np.random.choice(
                        [c for c in citizen_ids if c != cid],
                        size=sample_size,
                        replace=False
                    )
                    for other_cid in connections:
                        if not self.graph.has_edge(cid, other_cid):
                            self.graph.add_edge(
                                cid,
                                other_cid,
                                weight=EDGE_WEIGHTS['same_booth'],
                                relationship='same_booth'
                            )
                            edge_count += 1
        
        logger.info(f"Added {edge_count} same-booth edges")
    
    def _add_scheme_edges(self):
        """Add edges for citizens in same scheme"""
        
        # Get scheme co-memberships
        beneficiaries = self.db.query(models.Beneficiary).all()
        
        scheme_groups = {}
        for ben in beneficiaries:
            if ben.scheme_id not in scheme_groups:
                scheme_groups[ben.scheme_id] = []
            scheme_groups[ben.scheme_id].append(ben.citizen_id)
        
        edge_count = 0
        for scheme_id, citizen_ids in scheme_groups.items():
            # Connect beneficiaries of same scheme (sample for large schemes)
            for i in range(len(citizen_ids)):
                sample_size = min(15, len(citizen_ids) - i - 1)
                if sample_size > 0:
                    connections = citizen_ids[i+1:i+1+sample_size]
                    for other_cid in connections:
                        if self.graph.has_node(citizen_ids[i]) and self.graph.has_node(other_cid):
                            if not self.graph.has_edge(citizen_ids[i], other_cid):
                                self.graph.add_edge(
                                    citizen_ids[i],
                                    other_cid,
                                    weight=EDGE_WEIGHTS['shared_scheme'],
                                    relationship='shared_scheme'
                                )
                                edge_count += 1
        
        logger.info(f"Added {edge_count} shared-scheme edges")
    
    def _add_activity_edges(self):
        """Add edges for citizens with shared activities"""
        
        # Get activities
        activities = self.db.query(models.Activity).limit(5000).all()
        
        # Group by activity type and time proximity
        activity_groups = {}
        for activity in activities:
            key = f"{activity.activity_type}_{activity.timestamp.date()}"
            if key not in activity_groups:
                activity_groups[key] = []
            activity_groups[key].append(activity.citizen_id)
        
        edge_count = 0
        for key, citizen_ids in activity_groups.items():
            if len(citizen_ids) > 1:
                # Connect citizens who did same activity on same day
                for i in range(len(citizen_ids)):
                    for j in range(i + 1, min(i + 10, len(citizen_ids))):  # Limit connections
                        if self.graph.has_node(citizen_ids[i]) and self.graph.has_node(citizen_ids[j]):
                            if not self.graph.has_edge(citizen_ids[i], citizen_ids[j]):
                                self.graph.add_edge(
                                    citizen_ids[i],
                                    citizen_ids[j],
                                    weight=EDGE_WEIGHTS['shared_activity'],
                                    relationship='shared_activity'
                                )
                                edge_count += 1
        
        logger.info(f"Added {edge_count} shared-activity edges")


class InfluenceCentralityCalculator:
    """Calculate influence scores using hybrid centrality approach"""
    
    def __init__(self, graph: nx.Graph):
        self.graph = graph
    
    def compute_scores(self, mode: str = 'full') -> Dict[int, float]:
        """
        Compute influence scores for all nodes
        mode: 'full' or 'demo' (demo uses faster approximations)
        
        Returns: {citizen_id: influence_score} normalized 0-100
        """
        
        if self.graph.number_of_nodes() == 0:
            return {}
        
        logger.info(f"Computing centrality scores (mode={mode})...")
        
        # Compute centrality measures
        degree_cent = self._compute_degree_centrality()
        betweenness_cent = self._compute_betweenness_centrality(mode)
        eigenvector_cent = self._compute_eigenvector_centrality(mode)
        
        # Composite score
        influence_scores = {}
        for node in self.graph.nodes():
            composite = (
                CENTRALITY_WEIGHTS['degree'] * degree_cent.get(node, 0) +
                CENTRALITY_WEIGHTS['betweenness'] * betweenness_cent.get(node, 0) +
                CENTRALITY_WEIGHTS['eigenvector'] * eigenvector_cent.get(node, 0)
            )
            influence_scores[node] = composite
        
        # Normalize to 0-100
        if influence_scores:
            min_score = min(influence_scores.values())
            max_score = max(influence_scores.values())
            
            if max_score > min_score:
                for node in influence_scores:
                    influence_scores[node] = ((influence_scores[node] - min_score) / (max_score - min_score)) * 100
            else:
                # All same score
                for node in influence_scores:
                    influence_scores[node] = 50.0
        
        logger.info(f"Computed {len(influence_scores)} influence scores")
        
        return influence_scores
    
    def _compute_degree_centrality(self) -> Dict:
        """Compute weighted degree centrality"""
        return nx.degree_centrality(self.graph)
    
    def _compute_betweenness_centrality(self, mode: str) -> Dict:
        """Compute betweenness centrality (approximate for demo mode)"""
        
        if mode == 'demo':
            # Approximate betweenness using subset of nodes
            k = min(100, self.graph.number_of_nodes())
            return nx.betweenness_centrality(self.graph, k=k)
        else:
            # Full betweenness (slower but accurate)
            return nx.betweenness_centrality(self.graph)
    
    def _compute_eigenvector_centrality(self, mode: str) -> Dict:
        """Compute eigenvector centrality with fallback"""
        
        try:
            max_iter = 100 if mode == 'demo' else 500
            return nx.eigenvector_centrality(self.graph, max_iter=max_iter)
        except nx.PowerIterationFailedConvergence:
            logger.warning("Eigenvector centrality did not converge, using PageRank as fallback")
            return nx.pagerank(self.graph, max_iter=max_iter)
        except Exception as e:
            logger.error(f"Eigenvector centrality failed: {e}, returning zero values")
            return {node: 0.0 for node in self.graph.nodes()}


def run_influence_scoring(db: Session, mode: str = 'full', limit: int = None) -> Dict:
    """
    Main function to run influence scoring
    
    Args:
        mode: 'full' or 'demo' (demo is faster)
        limit: Limit number of citizens (for testing)
    
    Returns: Statistics dict
    """
    
    start_time = datetime.now(timezone.utc)
    logger.info(f"Starting influence scoring (mode={mode}, limit={limit})...")
    
    # Build graph
    builder = InfluenceGraphBuilder(db)
    graph = builder.build_graph(limit=limit)
    
    if graph.number_of_nodes() == 0:
        return {
            "status": "error",
            "message": "No citizens found",
            "execution_time": 0
        }
    
    # Compute scores
    calculator = InfluenceCentralityCalculator(graph)
    influence_scores = calculator.compute_scores(mode=mode)
    
    # Update database
    updated_count = 0
    sorted_scores = sorted(influence_scores.items(), key=lambda x: x[1], reverse=True)
    
    for rank, (citizen_id, score) in enumerate(sorted_scores, 1):
        citizen = db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
        if citizen:
            citizen.influence_score = round(score, 2)
            citizen.influence_rank = rank
            citizen.last_influence_updated = datetime.now(timezone.utc)
            updated_count += 1
    
    db.commit()
    
    # Also cache avg sentiment for booths (optimization)
    update_booth_sentiment_cache(db)
    
    end_time = datetime.now(timezone.utc)
    execution_time = (end_time - start_time).total_seconds()
    
    logger.info(f"Influence scoring complete in {execution_time:.2f}s")
    
    return {
        "status": "success",
        "citizens_updated": updated_count,
        "graph_nodes": graph.number_of_nodes(),
        "graph_edges": graph.number_of_edges(),
        "execution_time": round(execution_time, 2),
        "avg_influence_score": round(np.mean(list(influence_scores.values())), 2),
        "max_influence_score": round(max(influence_scores.values()), 2),
        "min_influence_score": round(min(influence_scores.values()), 2)
    }


def update_booth_sentiment_cache(db: Session):
    """Cache booth sentiment averages for fast dashboard loading"""
    
    logger.info("Updating booth sentiment cache...")
    
    booths = db.query(models.Booth).all()
    
    for booth in booths:
        avg_sentiment = db.query(func.avg(models.SentimentLog.sentiment_score)).filter(
            models.SentimentLog.booth_id == booth.id
        ).scalar()
        
        if avg_sentiment is not None:
            # Normalize from -1,1 to 0,100
            booth.avg_sentiment = round(((avg_sentiment + 1) / 2) * 100, 2)
        else:
            booth.avg_sentiment = 50.0
    
    db.commit()
    logger.info("✅ Booth sentiment cache updated")


def get_top_influencers(db: Session, limit: int = 20) -> List[Dict]:
    """Get top influencers with enriched data"""
    
    citizens = db.query(models.Citizen).order_by(
        models.Citizen.influence_score.desc()
    ).limit(limit).all()
    
    results = []
    for citizen in citizens:
        booth = db.query(models.Booth).filter(models.Booth.id == citizen.booth_id).first()
        
        # Get engagement metrics
        activity_count = db.query(func.count(models.Activity.id)).filter(
            models.Activity.citizen_id == citizen.id
        ).scalar() or 0
        
        beneficiary_count = db.query(func.count(models.Beneficiary.id)).filter(
            models.Beneficiary.citizen_id == citizen.id
        ).scalar() or 0
        
        results.append({
            "citizen_id": citizen.id,
            "name": citizen.name,
            "influence_score": citizen.influence_score,
            "influence_rank": citizen.influence_rank,
            "booth_id": citizen.booth_id,
            "booth_name": booth.name if booth else "Unknown",
            "age": citizen.age,
            "occupation": citizen.occupation,
            "segments": citizen.segment_tags,
            "activity_count": activity_count,
            "beneficiary_count": beneficiary_count
        })
    
    return results


def get_booth_influence_summary(db: Session) -> Dict:
    """Get booth-level influence statistics"""
    
    booths = db.query(models.Booth).all()
    
    results = []
    
    for booth in booths:
        # Get citizens in booth
        citizens = db.query(models.Citizen).filter(models.Citizen.booth_id == booth.id).all()
        
        if not citizens:
            continue
        
        influence_scores = [c.influence_score for c in citizens if c.influence_score > 0]
        
        if influence_scores:
            avg_influence = np.mean(influence_scores)
            top_influencer = max(citizens, key=lambda c: c.influence_score)
            
            results.append({
                "booth_id": booth.id,
                "booth_name": booth.name,
                "avg_influence": round(avg_influence, 2),
                "citizens_count": len(citizens),
                "top_influencer": {
                    "citizen_id": top_influencer.id,
                    "name": top_influencer.name,
                    "influence_score": top_influencer.influence_score
                }
            })
    
    # Sort by avg influence
    results.sort(key=lambda x: x['avg_influence'], reverse=True)
    
    # Distribution stats
    all_scores = [r['avg_influence'] for r in results]
    
    return {
        "booth_summaries": results[:20],  # Top 20 booths
        "total_booths": len(results),
        "avg_booth_influence": round(np.mean(all_scores), 2) if all_scores else 0,
        "max_booth_influence": round(max(all_scores), 2) if all_scores else 0,
        "min_booth_influence": round(min(all_scores), 2) if all_scores else 0
    }
