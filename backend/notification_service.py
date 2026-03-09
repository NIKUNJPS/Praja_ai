"""
Hyper-Local Governance Notification Engine
Automatic citizen targeting and multilingual message generation
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
import models

logger = logging.getLogger(__name__)

# Multilingual message templates
WORK_TEMPLATES = {
    "Road Construction": {
        "en": {
            "benefit": "road connectivity and safety",
            "template": "New road construction completed in your area ({street_name}). This improves road connectivity and safety. Total investment: ₹{budget:,.0f}."
        },
        "hi": {
            "benefit": "सड़क संपर्क और सुरक्षा",
            "template": "आपके क्षेत्र ({street_name}) में नया सड़क निर्माण पूरा हुआ है। यह सड़क संपर्क और सुरक्षा में सुधार करता है। कुल निवेश: ₹{budget:,.0f}।"
        },
        "mr": {
            "benefit": "रस्ता संपर्क आणि सुरक्षा",
            "template": "तुमच्या परिसरात ({street_name}) नवीन रस्ता बांधकाम पूर्ण झाले आहे। यामुळे रस्ता संपर्क आणि सुरक्षा सुधारते. एकूण गुंतवणूक: ₹{budget:,.0f}।"
        }
    },
    "Water Supply": {
        "en": {
            "benefit": "water availability and quality",
            "template": "Water supply infrastructure improved in {street_name}. Better water availability for your area. Project cost: ₹{budget:,.0f}."
        },
        "hi": {
            "benefit": "पानी की उपलब्धता और गुणवत्ता",
            "template": "{street_name} में पानी आपूर्ति बुनियादी ढांचा बेहतर हुआ। आपके क्षेत्र के लिए बेहतर पानी उपलब्धता। परियोजना लागत: ₹{budget:,.0f}।"
        },
        "mr": {
            "benefit": "पाणी उपलब्धता आणि गुणवत्ता",
            "template": "{street_name} मध्ये पाणी पुरवठा पायाभूत सुविधा सुधारल्या. तुमच्या भागासाठी चांगली पाणी उपलब्धता. प्रकल्प खर्च: ₹{budget:,.0f}।"
        }
    },
    "Drainage": {
        "en": {
            "benefit": "drainage and waterlogging prevention",
            "template": "Drainage system upgraded in {street_name}. No more waterlogging during rains! Investment: ₹{budget:,.0f}."
        },
        "hi": {
            "benefit": "जल निकासी और जलभराव रोकथाम",
            "template": "{street_name} में जल निकासी प्रणाली अपग्रेड की गई। अब बारिश में जलभराव नहीं! निवेश: ₹{budget:,.0f}।"
        },
        "mr": {
            "benefit": "गटार आणि पाणी साचणे प्रतिबंध",
            "template": "{street_name} मध्ये गटार व्यवस्था सुधारली. आता पावसात पाणी साचणार नाही! गुंतवणूक: ₹{budget:,.0f}।"
        }
    },
    "Street Lighting": {
        "en": {
            "benefit": "night safety and visibility",
            "template": "Street lighting upgraded in {street_name}. Enhanced night safety for residents. Cost: ₹{budget:,.0f}."
        },
        "hi": {
            "benefit": "रात की सुरक्षा और दृश्यता",
            "template": "{street_name} में स्ट्रीट लाइटिंग अपग्रेड की गई। निवासियों के लिए बेहतर रात की सुरक्षा। लागत: ₹{budget:,.0f}।"
        },
        "mr": {
            "benefit": "रात्रीची सुरक्षा आणि दृश्यमानता",
            "template": "{street_name} मध्ये रस्त्याच्या दिव्यांचे सुधारणा. रहिवाशांसाठी रात्रीची सुरक्षा वाढली. खर्च: ₹{budget:,.0f}।"
        }
    },
    "Park Development": {
        "en": {
            "benefit": "community recreation and health",
            "template": "New park developed in {street_name}. Great space for recreation and health! Budget: ₹{budget:,.0f}."
        },
        "hi": {
            "benefit": "सामुदायिक मनोरंजन और स्वास्थ्य",
            "template": "{street_name} में नया पार्क विकसित किया गया। मनोरंजन और स्वास्थ्य के लिए बेहतरीन स्थान! बजट: ₹{budget:,.0f}।"
        },
        "mr": {
            "benefit": "सामुदायिक मनोरंजन आणि आरोग्य",
            "template": "{street_name} मध्ये नवीन उद्यान विकसित केले. मनोरंजन आणि आरोग्यासाठी उत्तम जागा! अर्थसंकल्प: ₹{budget:,.0f}।"
        }
    },
    "Community Center": {
        "en": {
            "benefit": "community engagement and facilities",
            "template": "Community center established in {street_name}. Hub for local activities and services. Investment: ₹{budget:,.0f}."
        },
        "hi": {
            "benefit": "सामुदायिक भागीदारी और सुविधाएं",
            "template": "{street_name} में सामुदायिक केंद्र स्थापित किया गया। स्थानीय गतिविधियों और सेवाओं के लिए केंद्र। निवेश: ₹{budget:,.0f}।"
        },
        "mr": {
            "benefit": "सामुदायिक सहभाग आणि सुविधा",
            "template": "{street_name} मध्ये समुदाय केंद्र स्थापित केले. स्थानिक उपक्रम आणि सेवांसाठी केंद्र. गुंतवणूक: ₹{budget:,.0f}।"
        }
    }
}

# Default template for unknown categories
DEFAULT_TEMPLATE = {
    "en": "New development project completed in {street_name}. This improves local infrastructure. Budget: ₹{budget:,.0f}.",
    "hi": "{street_name} में नया विकास परियोजना पूरी हुई। यह स्थानीय बुनियादी ढांचा बेहतर करता है। बजट: ₹{budget:,.0f}।",
    "mr": "{street_name} मध्ये नवीन विकास प्रकल्प पूर्ण झाला. हे स्थानिक पायाभूत सुविधा सुधारते. अर्थसंकल्प: ₹{budget:,.0f}।"
}


def get_affected_citizens(db: Session, civic_work: models.CivicWork) -> List[models.Citizen]:
    """
    Smart targeting: Identify citizens affected by civic work

    Priority:
    1. Citizens on directly affected streets
    2. Citizens in same booth (broader reach)
    """
    affected_citizens = []

    # Primary targeting: Affected streets
    if civic_work.affected_streets:
        for street_id in civic_work.affected_streets:
            street_citizens = db.query(models.Citizen).filter(
                models.Citizen.street_id == street_id
            ).all()
            affected_citizens.extend(street_citizens)
            logger.info(f"Found {len(street_citizens)} citizens on street {street_id}")

    # Secondary targeting: Same booth (if no affected streets specified)
    if not affected_citizens:
        booth_citizens = db.query(models.Citizen).filter(
            models.Citizen.booth_id == civic_work.booth_id
        ).limit(500).all()  # Limit for performance
        affected_citizens.extend(booth_citizens)
        logger.info(f"No streets specified, targeting {len(booth_citizens)} booth citizens")

    # Remove duplicates
    unique_citizens = list({c.id: c for c in affected_citizens}.values())
    logger.info(f"Total unique citizens affected: {len(unique_citizens)}")
    return unique_citizens


def generate_multilingual_message(
    civic_work: models.CivicWork,
    street_name: str,
    language: str = "en"
) -> str:
    """
    Generate personalized multilingual message for civic work.

    Args:
        civic_work: CivicWork object
        street_name: Name of the street
        language: 'en', 'hi', or 'mr'

    Returns:
        Formatted message in specified language
    """
    templates = WORK_TEMPLATES.get(civic_work.category, {})
    if language in templates:
        template = templates[language]["template"]
    else:
        template = DEFAULT_TEMPLATE.get(language, DEFAULT_TEMPLATE["en"])

    return template.format(
        street_name=street_name,
        budget=civic_work.budget or 0
    )


def create_notifications_bulk(
    db: Session,
    civic_work: models.CivicWork,
    citizens: List[models.Citizen]
) -> int:
    """
    Bulk create notifications for affected citizens.
    Optimised for 100‑500 citizens per civic work.

    Returns: Number of notifications created.
    """
    if not citizens:
        return 0

    start_time = datetime.now(timezone.utc)

    # Pre‑fetch street names to avoid N+1 queries
    street_ids = {c.street_id for c in citizens if c.street_id}
    streets = db.query(models.Street).filter(models.Street.id.in_(street_ids)).all()
    street_map = {s.id: s.name for s in streets}

    notifications = []
    for citizen in citizens:
        street_name = street_map.get(citizen.street_id, "your area")

        msg_en = generate_multilingual_message(civic_work, street_name, "en")
        msg_hi = generate_multilingual_message(civic_work, street_name, "hi")
        msg_mr = generate_multilingual_message(civic_work, street_name, "mr")

        lang_map = {"English": msg_en, "Hindi": msg_hi, "Marathi": msg_mr}
        primary_message = lang_map.get(citizen.language_preference, msg_en)

        notifications.append(models.Notification(
            citizen_id=citizen.id,
            booth_id=citizen.booth_id,
            work_id=civic_work.id,
            message=primary_message,
            message_en=msg_en,
            message_hi=msg_hi,
            message_mr=msg_mr,
            language=citizen.language_preference,
            delivery_status="sent",
            delivered=True
        ))

    try:
        db.bulk_save_objects(notifications)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to bulk insert notifications: {e}", exc_info=True)
        db.rollback()
        return 0

    end_time = datetime.now(timezone.utc)
    execution_time = (end_time - start_time).total_seconds()
    logger.info(f"Created {len(notifications)} notifications in {execution_time:.2f}s")
    return len(notifications)


def get_notification_summary(db: Session) -> Dict:
    """
    Get notification statistics for dashboard.
    """
    total = db.query(func.count(models.Notification.id)).scalar() or 0
    last_24h_threshold = datetime.now(timezone.utc) - timedelta(hours=24)
    last_24h = db.query(func.count(models.Notification.id)).filter(
        models.Notification.sent_at >= last_24h_threshold
    ).scalar() or 0

    # Top 10 booths by notification count
    booth_stats = db.query(
        models.Booth.id,
        models.Booth.name,
        func.count(models.Notification.id).label('count')
    ).join(
        models.Notification, models.Notification.booth_id == models.Booth.id
    ).group_by(
        models.Booth.id, models.Booth.name
    ).order_by(
        func.count(models.Notification.id).desc()
    ).limit(10).all()

    booth_breakdown = [
        {"booth_id": b.id, "booth_name": b.name, "notifications": b.count}
        for b in booth_stats
    ]

    # Segment breakdown (using citizen segment tags)
    # This is an estimate – for large datasets consider a materialised view
    segment_counts = {}
    notifications = db.query(models.Notification).limit(1000).all()
    for notif in notifications:
        citizen = db.query(models.Citizen).filter(models.Citizen.id == notif.citizen_id).first()
        if citizen and citizen.segment_tags:
            for seg in citizen.segment_tags:
                segment_counts[seg] = segment_counts.get(seg, 0) + 1

    segment_breakdown = [
        {"segment": k, "count": v}
        for k, v in sorted(segment_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    delivered = db.query(func.count(models.Notification.id)).filter(
        models.Notification.delivered == True
    ).scalar() or 0

    return {
        "total_notifications": total,
        "last_24h_count": last_24h,
        "delivered_count": delivered,
        "delivery_rate": round((delivered / total * 100), 2) if total > 0 else 0,
        "booth_breakdown": booth_breakdown,
        "segment_breakdown": segment_breakdown
    }


def get_recent_notifications(db: Session, limit: int = 50) -> List[Dict]:
    """
    Get recent notifications with citizen and work details.
    """
    notifications = db.query(models.Notification).order_by(
        models.Notification.sent_at.desc()
    ).limit(limit).all()

    results = []
    for notif in notifications:
        citizen = db.query(models.Citizen).filter(models.Citizen.id == notif.citizen_id).first()
        work = db.query(models.CivicWork).filter(models.CivicWork.id == notif.work_id).first()

        msg = notif.message
        if len(msg) > 100:
            msg = msg[:100] + "..."

        results.append({
            "notification_id": notif.id,
            "citizen_name": citizen.name if citizen else "Unknown",
            "work_title": work.title if work else "N/A",
            "work_category": work.category if work else "N/A",
            "message": msg,
            "language": notif.language,
            "delivery_status": notif.delivery_status,
            "sent_at": notif.sent_at.isoformat() if notif.sent_at else None
        })

    return results