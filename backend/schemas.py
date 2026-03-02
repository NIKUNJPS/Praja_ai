from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str
    role: str = "PublicViewer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    name: str
    role: str
    created_at: datetime

class StateCreate(BaseModel):
    name: str
    code: str
    population: int = 0

class StateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    code: str
    population: int
    created_at: datetime

class ConstituencyCreate(BaseModel):
    state_id: int
    name: str
    code: str
    population: int = 0

class ConstituencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    state_id: int
    name: str
    code: str
    population: int
    created_at: datetime

class BoothCreate(BaseModel):
    constituency_id: int
    name: str
    code: str
    total_voters: int = 0
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class BoothResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    constituency_id: int
    name: str
    code: str
    total_voters: int
    latitude: Optional[float]
    longitude: Optional[float]
    health_score: float
    risk_level: str
    engagement_index: float
    created_at: datetime

class CitizenCreate(BaseModel):
    booth_id: int
    street_id: Optional[int] = None
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    phone: Optional[str] = None
    language_preference: str = "English"

class CitizenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    booth_id: int
    name: str
    age: Optional[int]
    gender: Optional[str]
    occupation: Optional[str]
    segment_tags: List
    influence_score: float
    language_preference: str

class SchemeCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    budget: float = 0.0

class SchemeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    category: str
    description: Optional[str]
    budget: float
    created_at: datetime

class CivicWorkCreate(BaseModel):
    booth_id: int
    title: str
    description: Optional[str] = None
    category: str
    budget: float = 0.0
    status: str = "Planned"
    affected_streets: List[int] = []

class CivicWorkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    booth_id: int
    title: str
    category: str
    budget: float
    status: str
    affected_streets: List
    created_at: datetime

class IssueCreate(BaseModel):
    citizen_id: int
    booth_id: int
    title: str
    description: Optional[str] = None
    category: str
    priority: str = "Medium"

class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    citizen_id: int
    booth_id: int
    title: str
    category: str
    status: str
    priority: str
    reported_date: datetime

class SentimentCreate(BaseModel):
    citizen_id: int
    text: str
    language: str = "English"

class SentimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    citizen_id: int
    text: str
    language: str
    sentiment_score: float
    sentiment_label: str
    keywords: List
    logged_at: datetime