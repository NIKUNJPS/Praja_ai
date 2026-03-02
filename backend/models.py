from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base
import enum

class UserRole(enum.Enum):
    SUPER_ADMIN = "SuperAdmin"
    STATE_ADMIN = "StateAdmin"
    CONSTITUENCY_MANAGER = "ConstituencyManager"
    BOOTH_OFFICER = "BoothOfficer"
    ANALYST = "Analyst"
    PUBLIC_VIEWER = "PublicViewer"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.PUBLIC_VIEWER)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class State(Base):
    __tablename__ = "states"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    population = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    constituencies = relationship("Constituency", back_populates="state")

class Constituency(Base):
    __tablename__ = "constituencies"
    
    id = Column(Integer, primary_key=True, index=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    population = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    state = relationship("State", back_populates="constituencies")
    booths = relationship("Booth", back_populates="constituency")

class Booth(Base):
    __tablename__ = "booths"
    
    id = Column(Integer, primary_key=True, index=True)
    constituency_id = Column(Integer, ForeignKey("constituencies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    total_voters = Column(Integer, default=0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    health_score = Column(Float, default=50.0)
    risk_level = Column(String(20), default="Medium")
    engagement_index = Column(Float, default=50.0)
    avg_sentiment = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    constituency = relationship("Constituency", back_populates="booths")
    streets = relationship("Street", back_populates="booth")
    citizens = relationship("Citizen", back_populates="booth")
    civic_works = relationship("CivicWork", back_populates="booth")
    issues = relationship("Issue", back_populates="booth")

class Street(Base):
    __tablename__ = "streets"
    
    id = Column(Integer, primary_key=True, index=True)
    booth_id = Column(Integer, ForeignKey("booths.id"), nullable=False)
    name = Column(String(255), nullable=False)
    pincode = Column(String(10), nullable=True)
    households = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    booth = relationship("Booth", back_populates="streets")
    citizens = relationship("Citizen", back_populates="street")

class Citizen(Base):
    __tablename__ = "citizens"
    
    id = Column(Integer, primary_key=True, index=True)
    booth_id = Column(Integer, ForeignKey("booths.id"), nullable=False)
    street_id = Column(Integer, ForeignKey("streets.id"), nullable=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    occupation = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    language_preference = Column(String(20), default="English")
    segment_tags = Column(JSON, default=list)
    influence_score = Column(Float, default=0.0)
    influence_rank = Column(Integer, default=0)
    ai_segment_confidence = Column(Float, default=0.0)
    last_segmented_at = Column(DateTime, nullable=True)
    last_influence_updated = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    booth = relationship("Booth", back_populates="citizens")
    street = relationship("Street", back_populates="citizens")
    beneficiaries = relationship("Beneficiary", back_populates="citizen")
    issues = relationship("Issue", back_populates="citizen")
    sentiments = relationship("SentimentLog", back_populates="citizen")
    notifications = relationship("Notification", back_populates="citizen")
    activities = relationship("Activity", back_populates="citizen")

class GovernmentScheme(Base):
    __tablename__ = "government_schemes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    budget = Column(Float, default=0.0)
    start_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    beneficiaries = relationship("Beneficiary", back_populates="scheme")

class Beneficiary(Base):
    __tablename__ = "beneficiaries"
    
    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("government_schemes.id"), nullable=False)
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=False)
    enrolled_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(50), default="Active")
    
    scheme = relationship("GovernmentScheme", back_populates="beneficiaries")
    citizen = relationship("Citizen", back_populates="beneficiaries")

class CivicWork(Base):
    __tablename__ = "civic_works"
    
    id = Column(Integer, primary_key=True, index=True)
    booth_id = Column(Integer, ForeignKey("booths.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    budget = Column(Float, default=0.0)
    status = Column(String(50), default="Planned")
    start_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    affected_streets = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    booth = relationship("Booth", back_populates="civic_works")
    notifications = relationship("Notification", back_populates="work")

class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=False)
    booth_id = Column(Integer, ForeignKey("booths.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    status = Column(String(50), default="Open")
    priority = Column(String(20), default="Medium")
    reported_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    citizen = relationship("Citizen", back_populates="issues")
    booth = relationship("Booth", back_populates="issues")

class SentimentLog(Base):
    __tablename__ = "sentiment_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=False)
    booth_id = Column(Integer, ForeignKey("booths.id"), nullable=True)
    text = Column(Text, nullable=False)
    language = Column(String(20), default="English")
    sentiment_score = Column(Float, default=0.0)
    sentiment_label = Column(String(20), default="Neutral")
    keywords = Column(JSON, default=list)
    logged_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    citizen = relationship("Citizen", back_populates="sentiments")
    booth = relationship("Booth", backref="sentiment_logs")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=False)
    work_id = Column(Integer, ForeignKey("civic_works.id"), nullable=True)
    message = Column(Text, nullable=False)
    language = Column(String(20), default="English")
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    delivered = Column(Boolean, default=False)
    
    citizen = relationship("Citizen", back_populates="notifications")
    work = relationship("CivicWork", back_populates="notifications")

class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=False)
    activity_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    citizen = relationship("Citizen", back_populates="activities")

class Segment(Base):
    __tablename__ = "segments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    criteria = Column(JSON, default=dict)
    citizen_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class GraphEdge(Base):
    __tablename__ = "graph_edges"
    
    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(50), nullable=False)
    source_id = Column(Integer, nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(Integer, nullable=False)
    relationship = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))