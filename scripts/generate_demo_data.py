import sys
sys.path.append('/app/backend')

from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from datetime import datetime, timedelta, timezone
import random

indian_names = ["Rahul Sharma", "Priya Singh", "Amit Kumar", "Sneha Patel", "Vijay Reddy", "Anjali Gupta", "Raj Malhotra", "Pooja Iyer", "Arjun Nair", "Neha Verma", "Karan Mehta", "Sita Devi", "Ravi Rao", "Kavita Joshi", "Suresh Pillai", "Lakshmi Naidu", "Manoj Desai", "Divya Krishnan", "Anil Kapoor", "Meera Srinivasan"]

indian_streets = ["MG Road", "Brigade Road", "Anna Salai", "Park Street", "Marine Drive", "Connaught Place", "Nehru Place", "Gandhi Nagar", "Lajpat Nagar", "Karol Bagh", "Rajajinagar", "Jayanagar", "Indiranagar", "Koramangala", "Whitefield", "Electronic City", "Malleswaram", "Basavanagudi", "Marathahalli", "HSR Layout"]

occupations = ["Farmer", "Teacher", "Business Owner", "IT Professional", "Doctor", "Engineer", "Shopkeeper", "Daily Wage Worker", "Auto Driver", "Government Employee", "Retired", "Student", "Homemaker", "Artisan", "Carpenter"]

scheme_names = [
    ("Pradhan Mantri Awas Yojana", "Housing", 50000000),
    ("Ayushman Bharat", "Healthcare", 30000000),
    ("PM Kisan", "Agriculture", 25000000),
    ("Swachh Bharat Mission", "Sanitation", 15000000),
    ("Ujjwala Yojana", "Energy", 12000000),
    ("Digital India", "Technology", 20000000),
    ("Skill India", "Employment", 18000000),
]

civic_work_categories = ["Road Construction", "Water Supply", "Drainage", "Street Lighting", "Park Development", "Community Center", "School Renovation"]

issue_categories = ["Water Supply", "Road Damage", "Sanitation", "Power Outage", "Garbage Collection", "Street Lighting"]

sentiment_texts_positive = [
    "Great development work in our area!",
    "Very happy with the new road construction.",
    "Excellent water supply improvement.",
    "Thanks for the street lighting project.",
]

sentiment_texts_negative = [
    "Road condition is very poor.",
    "No water supply for 3 days.",
    "Street lights not working.",
    "Garbage not collected regularly.",
]

sentiment_texts_neutral = [
    "Project started in our area.",
    "New scheme announced for farmers.",
    "Meeting scheduled with officials.",
]

def generate_demo_data():
    db = SessionLocal()
    try:
        print("🚀 Starting India Civic Intelligence OS Demo Data Generation...")
        
        # Clear existing data
        print("\n🧹 Clearing existing data...")
        db.query(models.GraphEdge).delete()
        db.query(models.Activity).delete()
        db.query(models.Notification).delete()
        db.query(models.SentimentLog).delete()
        db.query(models.Issue).delete()
        db.query(models.Beneficiary).delete()
        db.query(models.CivicWork).delete()
        db.query(models.Citizen).delete()
        db.query(models.Street).delete()
        db.query(models.Booth).delete()
        db.query(models.Constituency).delete()
        db.query(models.State).delete()
        db.query(models.GovernmentScheme).delete()
        db.query(models.Segment).delete()
        db.commit()
        print("✅ Cleared existing data")
        
        # Create States
        print("\n🗺️  Creating 5 States...")
        states_data = [
            ("Maharashtra", "MH", 125000000),
            ("Karnataka", "KA", 67000000),
            ("Tamil Nadu", "TN", 76000000),
            ("Uttar Pradesh", "UP", 230000000),
            ("Gujarat", "GJ", 65000000),
        ]
        
        states = []
        for name, code, population in states_data:
            state = models.State(name=name, code=code, population=population)
            db.add(state)
            states.append(state)
        db.commit()
        print(f"✅ Created {len(states)} states")
        
        # Create Constituencies (20 total, 4 per state)
        print("\n🏛️  Creating 20 Constituencies...")
        constituencies = []
        const_counter = 1
        for state in states:
            for i in range(4):
                const_name = f"{state.name} - District {i+1}"
                const_code = f"{state.code}{const_counter:03d}"
                const_pop = random.randint(500000, 2000000)
                constituency = models.Constituency(
                    state_id=state.id,
                    name=const_name,
                    code=const_code,
                    population=const_pop
                )
                db.add(constituency)
                constituencies.append(constituency)
                const_counter += 1
        db.commit()
        print(f"✅ Created {len(constituencies)} constituencies")
        
        # Create Booths (200 total, 10 per constituency)
        print("\n🗳️  Creating 200 Booths...")
        booths = []
        booth_counter = 1
        for constituency in constituencies:
            for i in range(10):
                booth_name = f"Booth {booth_counter}"
                booth_code = f"{constituency.code}B{i+1:02d}"
                total_voters = random.randint(300, 1500)
                lat = random.uniform(8.0, 35.0)
                lon = random.uniform(68.0, 97.0)
                
                booth = models.Booth(
                    constituency_id=constituency.id,
                    name=booth_name,
                    code=booth_code,
                    total_voters=total_voters,
                    latitude=lat,
                    longitude=lon,
                    health_score=random.uniform(40.0, 90.0),
                    risk_level=random.choice(["Low", "Medium", "High"]),
                    engagement_index=random.uniform(30.0, 95.0)
                )
                db.add(booth)
                booths.append(booth)
                booth_counter += 1
        db.commit()
        print(f"✅ Created {len(booths)} booths")
        
        # Create Streets (400 total, 2 per booth)
        print("\n🛣️  Creating 400 Streets...")
        streets = []
        for booth in booths:
            for i in range(2):
                street_name = random.choice(indian_streets) + f" Sector {i+1}"
                pincode = f"{random.randint(100000, 999999)}"
                households = random.randint(50, 300)
                
                street = models.Street(
                    booth_id=booth.id,
                    name=street_name,
                    pincode=pincode,
                    households=households
                )
                db.add(street)
                streets.append(street)
        db.commit()
        print(f"✅ Created {len(streets)} streets")
        
        # Create Citizens (10,000)
        print("\n👥 Creating 10,000 Citizens...")
        citizens = []
        for i in range(10000):
            booth = random.choice(booths)
            street = random.choice([s for s in streets if s.booth_id == booth.id])
            
            citizen = models.Citizen(
                booth_id=booth.id,
                street_id=street.id,
                name=random.choice(indian_names) + f" {i}",
                age=random.randint(18, 85),
                gender=random.choice(["Male", "Female", "Other"]),
                occupation=random.choice(occupations),
                phone=f"+91{random.randint(7000000000, 9999999999)}",
                language_preference=random.choice(["English", "Hindi", "Marathi"]),
                segment_tags=[],
                influence_score=random.uniform(0, 100)
            )
            db.add(citizen)
            citizens.append(citizen)
            
            if (i + 1) % 2000 == 0:
                db.commit()
                print(f"  ✅ Created {i+1} citizens")
        
        db.commit()
        print(f"✅ Created {len(citizens)} citizens total")
        
        # Create Government Schemes
        print("\n🏛️  Creating Government Schemes...")
        schemes = []
        for name, category, budget in scheme_names:
            scheme = models.GovernmentScheme(
                name=name,
                category=category,
                description=f"Government initiative for {category.lower()}",
                budget=budget,
                start_date=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 365))
            )
            db.add(scheme)
            schemes.append(scheme)
        db.commit()
        print(f"✅ Created {len(schemes)} schemes")
        
        # Create Beneficiaries (2000)
        print("\n💰 Creating 2000 Beneficiaries...")
        for i in range(2000):
            beneficiary = models.Beneficiary(
                scheme_id=random.choice(schemes).id,
                citizen_id=random.choice(citizens).id,
                enrolled_date=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 300)),
                status=random.choice(["Active", "Completed", "Pending"])
            )
            db.add(beneficiary)
        db.commit()
        print("✅ Created 2000 beneficiaries")
        
        # Create Civic Works (150)
        print("\n🏗️  Creating 150 Civic Works...")
        civic_works = []
        for i in range(150):
            booth = random.choice(booths)
            work = models.CivicWork(
                booth_id=booth.id,
                title=f"{random.choice(civic_work_categories)} Project {i+1}",
                description=f"Development project for {booth.name}",
                category=random.choice(civic_work_categories),
                budget=random.uniform(100000, 5000000),
                status=random.choice(["Planned", "In Progress", "Completed"]),
                start_date=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180)),
                affected_streets=[random.choice([s.id for s in streets if s.booth_id == booth.id])]
            )
            db.add(work)
            civic_works.append(work)
        db.commit()
        print(f"✅ Created {len(civic_works)} civic works")
        
        # Create Issues (500)
        print("\n⚠️  Creating 500 Issues...")
        for i in range(500):
            citizen = random.choice(citizens)
            issue = models.Issue(
                citizen_id=citizen.id,
                booth_id=citizen.booth_id,
                title=f"{random.choice(issue_categories)} Issue",
                description=f"Problem reported in booth {citizen.booth_id}",
                category=random.choice(issue_categories),
                status=random.choice(["Open", "In Progress", "Resolved", "Closed"]),
                priority=random.choice(["Low", "Medium", "High"]),
                reported_date=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90))
            )
            db.add(issue)
        db.commit()
        print("✅ Created 500 issues")
        
        # Create Sentiment Logs (1000)
        print("\n💬 Creating 1000 Sentiment Logs...")
        for i in range(1000):
            citizen = random.choice(citizens)
            sentiment_type = random.choice(["positive", "negative", "neutral"])
            
            if sentiment_type == "positive":
                text = random.choice(sentiment_texts_positive)
                score = random.uniform(0.6, 1.0)
                label = "Positive"
            elif sentiment_type == "negative":
                text = random.choice(sentiment_texts_negative)
                score = random.uniform(-1.0, -0.3)
                label = "Negative"
            else:
                text = random.choice(sentiment_texts_neutral)
                score = random.uniform(-0.2, 0.2)
                label = "Neutral"
            
            sentiment = models.SentimentLog(
                citizen_id=citizen.id,
                text=text,
                language=citizen.language_preference,
                sentiment_score=score,
                sentiment_label=label,
                keywords=["development", "infrastructure"] if sentiment_type == "positive" else ["issue", "problem"],
                logged_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
            )
            db.add(sentiment)
        db.commit()
        print("✅ Created 1000 sentiment logs")
        
        # Create Activities (2000)
        print("\n📊 Creating 2000 Activities...")
        activity_types = ["Feedback Submitted", "Issue Reported", "Scheme Enrolled", "Survey Participated", "Meeting Attended"]
        for i in range(2000):
            activity = models.Activity(
                citizen_id=random.choice(citizens).id,
                activity_type=random.choice(activity_types),
                description="Citizen engagement activity",
                timestamp=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))
            )
            db.add(activity)
        db.commit()
        print("✅ Created 2000 activities")
        
        # Create Segments
        print("\n📂 Creating Segments...")
        segments_data = [
            ("Youth", {"age_min": 18, "age_max": 35}),
            ("Farmer", {"occupation": "Farmer"}),
            ("Business", {"occupation": "Business Owner"}),
            ("Women", {"gender": "Female"}),
            ("Senior Citizen", {"age_min": 60}),
        ]
        
        for name, criteria in segments_data:
            segment = models.Segment(
                name=name,
                criteria=criteria,
                citizen_count=random.randint(500, 3000)
            )
            db.add(segment)
        db.commit()
        print(f"✅ Created {len(segments_data)} segments")
        
        # Create Graph Edges (sample relationships)
        print("\n🕸️  Creating Graph Edges...")
        edge_count = 0
        
        # Citizen -> Booth edges
        for i in range(500):
            citizen = random.choice(citizens)
            edge = models.GraphEdge(
                source_type="Citizen",
                source_id=citizen.id,
                target_type="Booth",
                target_id=citizen.booth_id,
                relationship="RESIDES_IN",
                weight=1.0
            )
            db.add(edge)
            edge_count += 1
        
        # Booth -> Constituency edges
        for booth in booths[:50]:
            edge = models.GraphEdge(
                source_type="Booth",
                source_id=booth.id,
                target_type="Constituency",
                target_id=booth.constituency_id,
                relationship="BELONGS_TO",
                weight=1.0
            )
            db.add(edge)
            edge_count += 1
        
        db.commit()
        print(f"✅ Created {edge_count} graph edges")
        
        print("\n" + "="*60)
        print("🎉 Demo Data Generation Complete!")
        print("="*60)
        print(f"📊 Summary:")
        print(f"  • States: {len(states)}")
        print(f"  • Constituencies: {len(constituencies)}")
        print(f"  • Booths: {len(booths)}")
        print(f"  • Streets: {len(streets)}")
        print(f"  • Citizens: {len(citizens)}")
        print(f"  • Schemes: {len(schemes)}")
        print(f"  • Civic Works: {len(civic_works)}")
        print(f"  • Issues: 500")
        print(f"  • Sentiment Logs: 1000")
        print(f"  • Activities: 2000")
        print(f"  • Graph Edges: {edge_count}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    generate_demo_data()
