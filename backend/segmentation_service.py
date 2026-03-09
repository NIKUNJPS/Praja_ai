"""
AI Segmentation Engine
Hybrid approach: Rule‑based + KMeans refinement
"""

import logging
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder, StandardScaler
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
import models

logger = logging.getLogger(__name__)

# Segment definitions (for documentation)
SEGMENTS = {
    "Youth": "Citizens under 30 years",
    "Farmer": "Agricultural workers",
    "Business": "Business owners and entrepreneurs",
    "Women": "Female citizens",
    "Senior Citizen": "Citizens 60 years and above",
    "Urban Poor": "Low‑income urban workers",
    "Scheme Eligible": "Eligible but not enrolled in schemes"
}

# Occupation mapping for KMeans
OCCUPATION_MAP = {
    "Farmer": 1,
    "Teacher": 2,
    "Business Owner": 3,
    "IT Professional": 4,
    "Doctor": 5,
    "Engineer": 6,
    "Shopkeeper": 7,
    "Daily Wage Worker": 8,
    "Auto Driver": 9,
    "Government Employee": 10,
    "Retired": 11,
    "Student": 12,
    "Homemaker": 13,
    "Artisan": 14,
    "Carpenter": 15,
    "Labourer": 8,           # alias for Daily Wage Worker
    "Businessman": 3,
    "Entrepreneur": 3,
    "Clerk": 10,
    "Officer": 10,
    "Housewife": 13,
    "Unemployed": 0
}

def deterministic_segmentation(db: Session) -> int:
    """
    Phase A: Rule‑based tagging (fast + reliable).
    Returns number of citizens updated.
    """
    citizens = db.query(models.Citizen).all()
    updated_count = 0

    for citizen in citizens:
        segments = []
        rule_count = 0

        # Rule 1: Youth (age < 30)
        if citizen.age and citizen.age < 30:
            segments.append("Youth")
            rule_count += 1

        # Rule 2: Farmer (occupation contains farmer)
        if citizen.occupation and "farmer" in citizen.occupation.lower():
            segments.append("Farmer")
            rule_count += 1

        # Rule 3: Business (occupation contains business)
        if citizen.occupation and any(kw in citizen.occupation.lower() for kw in ["business", "shop", "trader", "merchant"]):
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
        urban_poor_keywords = ["daily wage", "auto driver", "shopkeeper", "artisan", "carpenter", "labourer", "coolie"]
        if citizen.occupation and any(kw in citizen.occupation.lower() for kw in urban_poor_keywords):
            segments.append("Urban Poor")
            rule_count += 1

        # Rule 7: Scheme Eligible (not a beneficiary but eligible age/occupation)
        beneficiary_count = db.query(func.count(models.Beneficiary.id)).filter(
            models.Beneficiary.citizen_id == citizen.id
        ).scalar() or 0

        if beneficiary_count == 0 and citizen.age and citizen.age >= 18:
            # Check if they match any scheme criteria (e.g., senior, farmer, BPL)
            if citizen.age >= 60 or (citizen.occupation and "farmer" in citizen.occupation.lower()):
                segments.append("Scheme Eligible")
                rule_count += 1

        # Calculate confidence (1.0 for rule‑based)
        confidence = 1.0 if rule_count > 0 else 0.0

        # Update citizen
        citizen.segment_tags = list(set(segments))  # remove duplicates
        citizen.ai_segment_confidence = confidence
        citizen.last_segmented_at = datetime.now(timezone.utc)
        updated_count += 1

    db.commit()
    logger.info(f"Deterministic segmentation updated {updated_count} citizens")
    return updated_count


def kmeans_refinement(db: Session, n_clusters: int = 7) -> int:
    """
    Phase B: KMeans clustering for AI credibility.
    Features: age, occupation (encoded), scheme participation, activity count, influence score.
    Returns number of citizens updated.
    """
    citizens = db.query(models.Citizen).all()

    # Prepare features
    features = []
    citizen_ids = []

    for citizen in citizens:
        # Skip if missing critical data
        if not citizen.age:
            continue

        # Feature 1: Age
        age = citizen.age

        # Feature 2: Occupation encoding
        occ_code = 0
        if citizen.occupation:
            # try exact match, else fallback to partial match
            occ_lower = citizen.occupation.lower()
            if occ_lower in OCCUPATION_MAP:
                occ_code = OCCUPATION_MAP[occ_lower]
            else:
                # fallback: check if any key is substring
                for key, code in OCCUPATION_MAP.items():
                    if key.lower() in occ_lower:
                        occ_code = code
                        break

        # Feature 3: Scheme participation (binary)
        beneficiary_count = db.query(func.count(models.Beneficiary.id)).filter(
            models.Beneficiary.citizen_id == citizen.id
        ).scalar() or 0
        scheme_participation = 1 if beneficiary_count > 0 else 0

        # Feature 4: Engagement (activity count)
        activity_count = db.query(func.count(models.Activity.id)).filter(
            models.Activity.citizen_id == citizen.id
        ).scalar() or 0

        # Feature 5: Influence score
        influence = citizen.influence_score

        features.append([age, occ_code, scheme_participation, activity_count, influence])
        citizen_ids.append(citizen.id)

    if len(features) < n_clusters:
        logger.warning(f"Not enough samples ({len(features)}) for {n_clusters} clusters, skipping KMeans")
        return 0

    # Standardize features
    features_array = np.array(features)
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features_array)

    # KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(features_scaled)

    # Build cluster profiles
    cluster_profiles = []
    for i in range(n_clusters):
        cluster_mask = cluster_labels == i
        cluster_features = features_array[cluster_mask]
        if len(cluster_features) == 0:
            continue
        avg_age = cluster_features[:, 0].mean()
        avg_occ = cluster_features[:, 1].mean()
        avg_scheme = cluster_features[:, 2].mean()
        avg_activity = cluster_features[:, 3].mean()
        avg_influence = cluster_features[:, 4].mean()
        cluster_profiles.append({
            'cluster': i,
            'avg_age': avg_age,
            'avg_occ': avg_occ,
            'avg_scheme': avg_scheme,
            'avg_activity': avg_activity,
            'avg_influence': avg_influence,
            'count': len(cluster_features)
        })

    # Assign ML‑derived segments based on profiles
    updated_count = 0
    for idx, cluster in enumerate(cluster_labels):
        citizen_id = citizen_ids[idx]
        citizen = db.query(models.Citizen).filter(models.Citizen.id == citizen_id).first()
        if not citizen:
            continue

        profile = next(p for p in cluster_profiles if p['cluster'] == cluster)

        # Heuristic mapping of cluster to segment
        ml_segment = None
        if profile['avg_age'] < 35 and profile['avg_activity'] > 1:
            ml_segment = "Active Youth"
        elif profile['avg_age'] >= 60:
            ml_segment = "Senior Engaged"
        elif profile['avg_scheme'] > 0.5:
            ml_segment = "Scheme Beneficiary"
        elif profile['avg_occ'] in [1, 8, 9]:   # Farmer, Daily Wage, Auto
            ml_segment = "Working Class"
        elif profile['avg_influence'] > 50:
            ml_segment = "Community Leader"
        else:
            ml_segment = f"Cluster_{cluster}"

        # Add ML segment (avoid duplicates)
        if ml_segment and ml_segment not in citizen.segment_tags:
            citizen.segment_tags = citizen.segment_tags + [ml_segment]

        # Update confidence (blend: 0.7 for ML)
        citizen.ai_segment_confidence = max(citizen.ai_segment_confidence, 0.7)
        citizen.last_segmented_at = datetime.now(timezone.utc)
        updated_count += 1

    db.commit()
    logger.info(f"KMeans refinement updated {updated_count} citizens")
    return updated_count


def get_segment_summary(db: Session) -> dict:
    """
    Get segment distribution and statistics.
    """
    citizens = db.query(models.Citizen).all()
    total_citizens = len(citizens)
    total_segmented = 0
    segment_counts = {}

    for citizen in citizens:
        if citizen.segment_tags:
            total_segmented += 1
            for seg in citizen.segment_tags:
                segment_counts[seg] = segment_counts.get(seg, 0) + 1

    segment_distribution = [
        {"segment": seg, "count": cnt, "percentage": round(cnt / total_citizens * 100, 2) if total_citizens else 0}
        for seg, cnt in segment_counts.items()
    ]
    segment_distribution.sort(key=lambda x: x['count'], reverse=True)

    # Top segments per booth (first 10 booths)
    booth_segments = []
    booths = db.query(models.Booth).limit(10).all()
    for booth in booths:
        booth_citizens = db.query(models.Citizen).filter(models.Citizen.booth_id == booth.id).all()
        booth_seg_counts = {}
        for c in booth_citizens:
            for seg in c.segment_tags:
                booth_seg_counts[seg] = booth_seg_counts.get(seg, 0) + 1
        if booth_seg_counts:
            top_seg = max(booth_seg_counts.items(), key=lambda x: x[1])
            booth_segments.append({
                "booth_id": booth.id,
                "booth_name": booth.name,
                "top_segment": top_seg[0],
                "count": top_seg[1]
            })

    avg_confidence = db.query(func.avg(models.Citizen.ai_segment_confidence)).scalar() or 0

    return {
        "total_citizens": total_citizens,
        "total_segmented": total_segmented,
        "segmentation_coverage": round(total_segmented / total_citizens * 100, 2) if total_citizens else 0,
        "segment_distribution": segment_distribution,
        "top_segments": segment_distribution[:5],
        "booth_segments": booth_segments,
        "avg_confidence": round(avg_confidence, 3)
    }