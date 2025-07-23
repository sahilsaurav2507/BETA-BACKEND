from pydantic import BaseModel, field_validator, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class BiggestHurdleEnum(str, Enum):
    A = "A"  # Time commitment
    B = "B"  # Simplifying topics
    C = "C"  # Audience reach
    D = "D"  # Ethics/compliance
    E = "E"  # Other

class PrimaryMotivationEnum(str, Enum):
    A = "A"  # Brand building
    B = "B"  # Client attraction
    C = "C"  # Revenue stream
    D = "D"  # Education/contribution

class TimeConsumingPartEnum(str, Enum):
    A = "A"  # Research
    B = "B"  # Drafting
    C = "C"  # Editing
    D = "D"  # Formatting

class ProfessionalFearEnum(str, Enum):
    A = "A"  # Losing clients
    B = "B"  # Becoming irrelevant
    C = "C"  # Being outdated
    D = "D"  # No fear

class FeedbackCreate(BaseModel):
    # Contact information
    email: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)

    # Multiple choice questions
    biggest_hurdle: BiggestHurdleEnum
    biggest_hurdle_other: Optional[str] = None
    primary_motivation: Optional[PrimaryMotivationEnum] = None
    time_consuming_part: Optional[TimeConsumingPartEnum] = None
    professional_fear: ProfessionalFearEnum

    # Short answer questions
    monetization_considerations: Optional[str] = Field(None, max_length=2000)
    professional_legacy: Optional[str] = Field(None, max_length=2000)
    platform_impact: str = Field(..., min_length=10, max_length=2000)

    @field_validator('monetization_considerations', 'professional_legacy')
    @classmethod
    def validate_optional_text_fields(cls, v):
        if v is not None and v.strip() and len(v.strip()) < 10:
            raise ValueError('Please enter at least 10 characters')
        return v
    
    @field_validator('biggest_hurdle_other')
    @classmethod
    def validate_biggest_hurdle_other(cls, v, info):
        values = info.data if info.data else {}
        if values.get('biggest_hurdle') == BiggestHurdleEnum.E and not v:
            raise ValueError('biggest_hurdle_other is required when biggest_hurdle is E')
        if values.get('biggest_hurdle') != BiggestHurdleEnum.E and v:
            raise ValueError('biggest_hurdle_other should only be provided when biggest_hurdle is E')
        return v
    
    @field_validator('monetization_considerations', 'professional_legacy', 'platform_impact')
    @classmethod
    def validate_text_fields(cls, v, info):
        field_name = info.field_name
        if not v or not v.strip():
            raise ValueError(f'{field_name} cannot be empty')

        # Basic validation - just ensure it's not empty and has reasonable length
        if len(v.strip()) < 10:
            raise ValueError(f'{field_name} must be at least 10 characters long')

        return v

class FeedbackResponse(BaseModel):
    id: int
    user_id: Optional[int]
    ip_address: Optional[str]

    # Contact information
    email: str
    name: str

    # Multiple choice responses
    biggest_hurdle: BiggestHurdleEnum
    biggest_hurdle_other: Optional[str]
    primary_motivation: Optional[PrimaryMotivationEnum]
    time_consuming_part: Optional[TimeConsumingPartEnum]
    professional_fear: ProfessionalFearEnum

    # Short answer responses
    monetization_considerations: Optional[str]
    professional_legacy: Optional[str]
    platform_impact: str

    # Metadata
    submitted_at: datetime
    updated_at: datetime

    # User info (if available)
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    
    class Config:
        from_attributes = True

class FeedbackListResponse(BaseModel):
    feedback: List[FeedbackResponse]
    pagination: Dict[str, int]

class FeedbackStatsResponse(BaseModel):
    total_responses: int
    
    # Breakdown by categories
    responses_by_hurdle: Dict[str, int]
    responses_by_motivation: Dict[str, int]
    responses_by_time_consuming_part: Dict[str, int]
    responses_by_fear: Dict[str, int]
    
    # Recent activity
    recent_responses: int
    responses_last_7_days: int
    responses_last_30_days: int
    
    # Date range
    first_response: Optional[datetime]
    latest_response: Optional[datetime]

class FeedbackSubmitResponse(BaseModel):
    success: bool
    message: str
    feedback_id: Optional[int] = None

class FeedbackFilters(BaseModel):
    search: Optional[str] = None
    biggest_hurdle: Optional[BiggestHurdleEnum] = None
    primary_motivation: Optional[PrimaryMotivationEnum] = None
    professional_fear: Optional[ProfessionalFearEnum] = None
    time_consuming_part: Optional[TimeConsumingPartEnum] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        values = info.data if info.data else {}
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

# Export format options
class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"

# Mapping for human-readable labels
HURDLE_LABELS = {
    "A": "Time commitment required for research and writing",
    "B": "Difficulty of simplifying complex legal topics",
    "C": "Uncertainty about reaching the right audience",
    "D": "Concerns about professional ethics and compliance",
    "E": "Other"
}

MOTIVATION_LABELS = {
    "A": "Build professional brand and thought leadership",
    "B": "Attract new, high-quality clients",
    "C": "Create additional revenue stream",
    "D": "Educate the public or contribute to legal community"
}

TIME_CONSUMING_LABELS = {
    "A": "Initial legal research and fact-checking",
    "B": "Actual drafting and structuring",
    "C": "Editing, proofreading, and simplifying language",
    "D": "Formatting, citations, and digital preparation"
}

FEAR_LABELS = {
    "A": "Losing potential clients to more visible competitors",
    "B": "Expertise becoming less relevant or discoverable",
    "C": "Being perceived as outdated by peers and clients",
    "D": "No significant fear about online presence"
}
