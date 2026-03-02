"""
Generate realistic multilingual civic feedback for sentiment demo
"""

import sys
sys.path.append('/app/backend')

from database import SessionLocal
import models
import random
from datetime import datetime, timedelta, timezone

# Realistic feedback samples
ENGLISH_FEEDBACK = {
    'positive': [
        "Great development work in our area! The new road construction is excellent.",
        "Very happy with the water supply improvement. Thank you government.",
        "The street lighting project is amazing. Our area feels much safer now.",
        "Excellent work on drainage system. No more waterlogging during rains.",
        "Appreciate the quick resolution of garbage collection issues.",
        "The new community center is wonderful. Great initiative!",
        "Clean and well-maintained public toilet facilities. Keep up the good work.",
        "The vaccination drive was very well organized. Thank you.",
        "Ayushman Bharat scheme helped my family. Very grateful.",
        "PM Awas Yojana housing is excellent quality. Thank you!"
    ],
    'negative': [
        "Road condition is very poor in our street. Needs immediate repair.",
        "No water supply for 3 days. This is unacceptable.",
        "Street lights not working for 2 weeks. Safety concern.",
        "Garbage not collected regularly. Health hazard in our area.",
        "The drainage is completely blocked. Water logging everywhere.",
        "Pothole on main road causing accidents. Please fix urgently.",
        "Public toilet is very dirty and not maintained.",
        "Power outage every day for 4-5 hours. Affecting businesses.",
        "No response to complaints. Contacted multiple times.",
        "Road construction work abandoned halfway. When will it complete?"
    ],
    'neutral': [
        "New project started in our area. Waiting to see the results.",
        "Meeting scheduled with ward officer next week.",
        "Submitted application for scheme enrollment.",
        "Survey team visited our booth yesterday.",
        "Notice received about upcoming civic work in area.",
        "Registration process for beneficiary ID completed.",
        "Attended community meeting today. Good discussion.",
        "New guidelines announced for local development.",
        "Information session about government schemes organized.",
        "Voter ID verification drive ongoing in our locality."
    ]
}

HINDI_FEEDBACK = {
    'positive': [
        "हमारे क्षेत्र में बहुत अच्छा विकास कार्य! नई सड़क उत्कृष्ट है।",
        "पानी की आपूर्ति में सुधार से बहुत खुश हूं। धन्यवाद सरकार।",
        "स्ट्रीट लाइट परियोजना शानदार है। हमारा क्षेत्र अब सुरक्षित महसूस होता है।",
        "जल निकासी प्रणाली पर उत्कृष्ट काम। अब बारिश में पानी नहीं भरता।",
        "कचरा संग्रह की समस्या का त्वरित समाधान के लिए धन्यवाद।",
        "नई सामुदायिक केंद्र बहुत अच्छी पहल है।",
        "सार्वजनिक शौचालय स्वच्छ और अच्छी तरह से बनाए रखा गया है।"
    ],
    'negative': [
        "हमारी गली में सड़क की हालत बहुत खराब है। तुरंत मरम्मत की जरूरत है।",
        "3 दिन से पानी की आपूर्ति नहीं है। यह अस्वीकार्य है।",
        "2 सप्ताह से स्ट्रीट लाइट काम नहीं कर रही है। सुरक्षा चिंता।",
        "कचरा नियमित रूप से एकत्र नहीं किया जाता। हमारे क्षेत्र में स्वास्थ्य खतरा।",
        "जल निकासी पूरी तरह से अवरुद्ध है। हर जगह पानी भर जाता है।",
        "मुख्य सड़क पर गड्ढा दुर्घटनाओं का कारण बन रहा है। कृपया तुरंत ठीक करें।",
        "सार्वजनिक शौचालय बहुत गंदा है और रखरखाव नहीं होता।"
    ],
    'neutral': [
        "हमारे क्षेत्र में नई परियोजना शुरू हुई। परिणाम देखने के लिए प्रतीक्षा कर रहे हैं।",
        "अगले सप्ताह वार्ड अधिकारी के साथ बैठक निर्धारित है।",
        "योजना नामांकन के लिए आवेदन जमा किया।",
        "कल सर्वेक्षण टीम ने हमारे बूथ का दौरा किया।",
        "क्षेत्र में आगामी नागरिक कार्य के बारे में सूचना प्राप्त हुई।"
    ]
}

MARATHI_FEEDBACK = {
    'positive': [
        "आमच्या भागात उत्तम विकास कार्य! नवीन रस्ता उत्कृष्ट आहे.",
        "पाणीपुरवठ्यात सुधारणा झाल्याने खूप आनंद झाला. धन्यवाद सरकार.",
        "रस्त्यावरील दिवे प्रकल्प अप्रतिम आहे. आमचा भाग आता सुरक्षित वाटतो.",
        "गटार व्यवस्थेवर उत्कृष्ट काम. आता पावसाळ्यात पाणी साचत नाही.",
        "कचरा गोळा करण्याच्या समस्येचे त्वरित निराकरण केल्याबद्दल धन्यवाद.",
        "नवीन समुदाय केंद्र अप्रतिम आहे. उत्तम उपक्रम!",
        "सार्वजनिक शौचालय स्वच्छ आणि चांगले राखले आहे."
    ],
    'negative': [
        "आमच्या गल्लीत रस्त्याची स्थिती खूप खराब आहे. त्वरित दुरुस्तीची गरज आहे.",
        "3 दिवसांपासून पाणीपुरवठा नाही. हे अस्वीकार्य आहे.",
        "2 आठवड्यांपासून रस्त्यावरचे दिवे काम करत नाहीत. सुरक्षेची चिंता.",
        "नियमितपणे कचरा गोळा केला जात नाही. आमच्या भागात आरोग्याचा धोका.",
        "गटार पूर्णपणे अडकली आहे. सर्वत्र पाणी साचते.",
        "मुख्य रस्त्यावरील खड्डा अपघातांना कारणीभूत आहे. कृपया तातडीने दुरुस्त करा.",
        "सार्वजनिक शौचालय खूप घाणेरडे आहे आणि देखभाल होत नाही."
    ],
    'neutral': [
        "आमच्या भागात नवीन प्रकल्प सुरू झाला. परिणाम पाहण्यासाठी वाट पाहत आहोत.",
        "पुढील आठवड्यात वॉर्ड अधिकाऱ्यांसोबत बैठक नियोजित आहे.",
        "योजना नोंदणीसाठी अर्ज सादर केला.",
        "काल सर्वेक्षण टीमने आमच्या बूथला भेट दिली.",
        "भागात येणाऱ्या नागरी कामाबद्दल सूचना मिळाली."
    ]
}

def generate_realistic_feedback(num_samples=500):
    """Generate realistic multilingual civic feedback"""
    
    db = SessionLocal()
    
    try:
        # Clear existing sentiment logs first
        db.query(models.SentimentLog).delete()
        db.commit()
        
        print(f"🚀 Generating {num_samples} realistic multilingual feedback samples...")
        
        citizens = db.query(models.Citizen).all()
        
        if not citizens:
            print("❌ No citizens found in database")
            return
        
        generated = 0
        
        for i in range(num_samples):
            citizen = random.choice(citizens)
            
            # Choose language based on citizen's preference
            if citizen.language_preference == 'Hindi':
                feedback_pool = HINDI_FEEDBACK
                language = 'Hindi'
            elif citizen.language_preference == 'Marathi':
                feedback_pool = MARATHI_FEEDBACK
                language = 'Marathi'
            else:
                feedback_pool = ENGLISH_FEEDBACK
                language = 'English'
            
            # Choose sentiment type (weighted: 30% positive, 40% negative, 30% neutral)
            sentiment_type = random.choices(
                ['positive', 'negative', 'neutral'],
                weights=[30, 40, 30]
            )[0]
            
            # Get random feedback text
            text = random.choice(feedback_pool[sentiment_type])
            
            # Create sentiment log (unprocessed - score = 0.0 initially)
            sentiment_log = models.SentimentLog(
                citizen_id=citizen.id,
                booth_id=citizen.booth_id,
                text=text,
                language=language,
                sentiment_score=0.0,  # Will be processed by ML pipeline
                sentiment_label="Neutral",
                keywords=[],
                logged_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
            )
            
            db.add(sentiment_log)
            generated += 1
            
            if generated % 100 == 0:
                db.commit()
                print(f"  ✅ Generated {generated} samples...")
        
        db.commit()
        print(f"🎉 Successfully generated {generated} multilingual feedback samples!")
        print(f"📊 Distribution: ~{num_samples * 0.3:.0f} positive, ~{num_samples * 0.4:.0f} negative, ~{num_samples * 0.3:.0f} neutral")
        print(f"🌍 Languages: English, Hindi, Marathi based on citizen preferences")
        print("\n💡 Next: Run POST /api/analytics/batch-sentiment to process with ML models")
        
    except Exception as e:
        print(f"❌ Error generating feedback: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    num_samples = 1000 if len(sys.argv) < 2 else int(sys.argv[1])
    generate_realistic_feedback(num_samples)
