from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime

# -------------------- Authentication --------------------
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_verified: Optional[bool] = None

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
    is_verified: bool
    created_at: datetime

class OTPRequest(BaseModel):
    email: EmailStr
    purpose: str          # "registration" or "password_reset"

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str
    purpose: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(min_length=6)

class SetNewPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=6)

class SuperLoginRequest(BaseModel):
    super_key: str
    email: Optional[str] = None   # optional, defaults to configured super email


# -------------------- Domain Models --------------------
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

class CitizenPatch(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    phone: Optional[str] = None
    booth_id: Optional[int] = None
    street_id: Optional[int] = None
    language_preference: Optional[str] = None


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

class CivicWorkDetailResponse(CivicWorkResponse):
    notifications_sent: int
    citizens_affected: int

class WorkStatusUpdate(BaseModel):
    status: str   # e.g., "Planned", "In Progress", "Completed", "On Hold"


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


# -------------------- Analytics --------------------
class BoothHealthResponse(BaseModel):
    booth_id: int
    booth_name: str
    booth_code: Optional[str] = None
    health_score: float
    risk_level: str
    sentiment_avg: float
    scheme_coverage: float
    civic_works_count: int
    engagement_score: float
    complaint_ratio: float
    citizens_count: int
    top_issues: List[Dict[str, Any]]

class DashboardStats(BaseModel):
    total_citizens: int
    total_booths: int
    total_civic_works: int
    avg_health_score: float
    active_beneficiaries: int
    open_issues: int
    sentiment_trend: float
    scheme_coverage_pct: float


# -------------------- Influence & Graph --------------------
class TopInfluencerResponse(BaseModel):
    citizen_id: int
    name: str
    influence_score: float
    influence_rank: int
    booth_id: int
    booth_name: str
    age: Optional[int]
    occupation: Optional[str]
    segments: List[str]
    activity_count: int
    beneficiary_count: int

class BoothInfluenceSummary(BaseModel):
    booth_id: int
    booth_name: str
    avg_influence: float
    citizens_count: int
    top_influencer: Dict[str, Any]


# -------------------- Notifications --------------------
class NotificationSummaryResponse(BaseModel):
    total_notifications: int
    last_24h_count: int
    delivered_count: int
    delivery_rate: float
    booth_breakdown: List[Dict[str, Any]]
    segment_breakdown: List[Dict[str, Any]]

class RecentNotificationResponse(BaseModel):
    notification_id: int
    citizen_name: str
    work_title: str
    work_category: str
    message: str
    language: str
    delivery_status: str
    sent_at: Optional[str]