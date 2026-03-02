"""
AI Segmentation Engine
Hybrid approach: Rule-based + KMeans refinement
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder, StandardScaler
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
import models

# Segment definitions
SEGMENTS = {
    "Youth": "Citizens under 30 years",
    "Farmer": "Agricultural workers",
    "Business": "Business owners and entrepreneurs",
    "Women": "Female citizens",
    "Senior Citizen": "Citizens 60 years and above",
    "Urban Poor": "Low-income urban workers",
    "Scheme Eligible": "Eligible but not enrolled in schemes"
}

def deterministic_segmentation(db: Session):
    """
    Phase A: Rule-based tagging (fast + reliable)
    Returns: Updated citizen count
    """
    
    citizens = db.query(models.Citizen).all()
    updated_count = 0
    
    for citizen in citizens:
        segments = []
        confidence = 0.0
        rule_count = 0
        
        # Rule 1: Youth (age < 30)
        if citizen.age and citizen.age < 30:
            segments.append("Youth")
            rule_count += 1
        
        # Rule 2: Farmer (occupation contains farmer)
        if citizen.occupation and "Farmer" in citizen.occupation:
            segments.append("Farmer")
            rule_count += 1
        
        # Rule 3: Business (occupation contains business)
        if citizen.occupation and "Business" in citizen.occupation:
            segments.append("Business")
            rule_count += 1
        
        # Rule 4: Women (gender = Female)
        if citizen.gender and citizen.gender.lower() in ["female", "f"]:
            segments.append("Women")
            rule_count += 1
        
        # Rule 5: Senior Citizen (age >= 60)
        if citizen.age and citizen.age >= 60:
            segments.append("Senior Citizen")
            rule_count += 1
        
        # Rule 6: Urban Poor (specific occupations)
        urban_poor_occupations = ["Daily Wage Worker", "Auto Driver", "Shopkeeper", "Artisan", "Carpenter"]
        if citizen.occupation and citizen.occupation in urban_poor_occupations:
            segments.append("Urban Poor")
            rule_count += 1
        
        # Rule 7: Scheme Eligible (not a beneficiary but eligible age/occupation)
        beneficiary_count = db.query(func.count(models.Beneficiary.id)).filter(
            models.Beneficiary.citizen_id == citizen.id
        ).scalar() or 0
        
        if beneficiary_count == 0 and citizen.age and citizen.age >= 18:
            # Check if they match any scheme criteria
            if citizen.age >= 60 or (citizen.occupation and "Farmer" in citizen.occupation):
                segments.append("Scheme Eligible")
                rule_count += 1
        
        # Calculate confidence (100% for rule-based)
        if rule_count > 0:
            confidence = 1.0  # Full confidence in deterministic rules
        
        # Update citizen
        citizen.segment_tags = segments
        citizen.ai_segment_confidence = confidence
        citizen.last_segmented_at = datetime.now(timezone.utc)
        updated_count += 1
    
    db.commit()
    return updated_count


def kmeans_refinement(db: Session, n_clusters=7):
    """
    Phase B: KMeans clustering for AI credibility
    Features: age, occupation, scheme participation, engagement, influence
    """
    
    citizens = db.query(models.Citizen).all()
    
    # Prepare features
    features = []
    citizen_ids = []
    
    for citizen in citizens:
        # Skip if missing critical data
        if not citizen.age or not citizen.occupation:
            continue
        
        # Feature 1: Age (normalized)
        age = citizen.age
        
        # Feature 2: Occupation encoding
        occupation_map = {
            "Farmer": 1, "Teacher": 2, "Business Owner": 3, "IT Professional": 4,
            "Doctor": 5, "Engineer": 6, "Shopkeeper": 7, "Daily Wage Worker": 8,
            "Auto Driver": 9, "Government Employee": 10, "Retired": 11, "Student": 12,
            "Homemaker": 13, "Artisan": 14, "Carpenter": 15
        }
        occupation_encoded = occupation_map.get(citizen.occupation, 0)
        
        # Feature 3: Scheme participation (binary)
        beneficiary_count = db.query(func.count(models.Beneficiary.id)).filter(
            models.Beneficiary.citizen_id == citizen.id
        ).scalar() or 0
        scheme_participation = 1 if beneficiary_count > 0 else 0
        
        # Feature 4: Engagement score (activity count)
        activity_count = db.query(func.count(models.Activity.id)).filter(
            models.Activity.citizen_id == citizen.id
        ).scalar() or 0
        
        # Feature 5: Influence score
        influence = citizen.influence_score
        
        features.append([age, occupation_encoded, scheme_participation, activity_count, influence])
        citizen_ids.append(citizen.id)
    
    if len(features) < n_clusters:
        return 0
    
    # Standardize features
    features_array = np.array(features)
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features_array)
    
    # KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(features_scaled)
    
    # Map clusters to semantic labels based on cluster centers
    cluster_profiles = []
    for i in range(n_clusters):
        cluster_mask = cluster_labels == i
        cluster_features = features_array[cluster_mask]
        
        avg_age = cluster_features[:, 0].mean()
        avg_occupation = cluster_features[:, 1].mean()
        avg_scheme = cluster_features[:, 2].mean()
        avg_activity = cluster_features[:, 3].mean()
        avg_influence = cluster_features[:, 4].mean()
        
        cluster_profiles.append({
            'cluster': i,
            'avg_age': avg_age,
            'avg_occupation': avg_occupation,
            'avg_scheme': avg_scheme,
            'avg_activity': avg_activity,
            'avg_influence': avg_influence,
            'count': cluster_mask.sum()
        })
    
    # Assign ML-derived segments based on profiles
    updated_count = 0
    for idx, cluster in enumerate(cluster_labels):
        citizen_id = citizen_ids[idx]
        citizen = db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
        
        if citizen:
            profile = cluster_profiles[cluster]
            ml_segment = None
            
            # Map cluster to segment based on profile
            if profile['avg_age'] < 35 and profile['avg_activity'] > 1:
                ml_segment = "Active Youth"
            elif profile['avg_age'] >= 60:
                ml_segment = "Senior Engaged"
            elif profile['avg_scheme'] > 0.5:
                ml_segment = "Scheme Beneficiary"
            elif profile['avg_occupation'] in [1, 8, 9]:  # Farmer, Daily Wage, Auto
                ml_segment = "Working Class"
            elif profile['avg_influence'] > 50:
                ml_segment = "Community Leader"
            else:
                ml_segment = f"Cluster_{cluster}"
            
            # Add ML segment to existing tags (don't overwrite deterministic ones)
            if ml_segment and ml_segment not in citizen.segment_tags:
                citizen.segment_tags = citizen.segment_tags + [ml_segment]
            
            # Update confidence (blend of deterministic and ML)
            ml_confidence = 0.7  # KMeans confidence
            citizen.ai_segment_confidence = max(citizen.ai_segment_confidence, ml_confidence)
            citizen.last_segmented_at = datetime.now(timezone.utc)
            updated_count += 1
    
    db.commit()
    return updated_count


def get_segment_summary(db: Session):
    """
    Get segment distribution and stats
    """
    
    citizens = db.query(models.Citizen).all()
    
    segment_counts = {}
    total_segmented = 0
    
    for citizen in citizens:
        if citizen.segment_tags:
            total_segmented += 1
            for segment in citizen.segment_tags:
                segment_counts[segment] = segment_counts.get(segment, 0) + 1
    
    total_citizens = len(citizens)
    
    # Calculate percentages
    segment_distribution = []
    for segment, count in segment_counts.items():
        segment_distribution.append({
            "segment": segment,
            "count": count,
            "percentage": round((count / total_citizens * 100), 2) if total_citizens > 0 else 0
        })
    
    # Sort by count
    segment_distribution.sort(key=lambda x: x['count'], reverse=True)
    
    # Get top segment per booth (sample of first 10 booths)
    booth_segments = []
    booths = db.query(models.Booth).limit(10).all()
    
    for booth in booths:
        booth_citizens = db.query(models.Citizen).filter(models.Citizen.booth_id == booth.id).all()
        booth_segment_counts = {}
        
        for citizen in booth_citizens:
            for segment in citizen.segment_tags:
                booth_segment_counts[segment] = booth_segment_counts.get(segment, 0) + 1
        
        if booth_segment_counts:
            top_segment = max(booth_segment_counts.items(), key=lambda x: x[1])
            booth_segments.append({
                "booth_id": booth.id,
                "booth_name": booth.name,
                "top_segment": top_segment[0],
                "count": top_segment[1]
            })
    
    # Average confidence
    avg_confidence = db.query(func.avg(models.Citizen.ai_segment_confidence)).scalar() or 0
    
    return {
        "total_citizens": total_citizens,
        "total_segmented": total_segmented,
        "segmentation_coverage": round((total_segmented / total_citizens * 100), 2) if total_citizens > 0 else 0,
        "segment_distribution": segment_distribution,
        "top_segments": segment_distribution[:5],
        "booth_segments": booth_segments,
        "avg_confidence": round(avg_confidence, 3)
    }
