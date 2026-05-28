from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import uuid4


class CategoryEnum(str, Enum):
    ECONOMY = "экономика"
    POLITICS = "политика"
    SOCIAL = "соцсети"
    CELEBRITY = "селеба"
    SCANDAL = "скандал"
    BANK_TAX = "банки-налоги"
    FEAR = "страхи"


class TriggerEnum(str, Enum):
    MONEY = "деньги"
    CRISIS = "кризис"
    OPPORTUNITY = "возможность"
    FEAR = "страх"
    TRUST = "доверие"


class ExpiryEnum(str, Enum):
    URGENT_48H = "срочно 24-48ч"
    WEEK = "неделя"
    LONG = "более"


class SourceTypeEnum(str, Enum):
    TOP_MEDIA = "топовое СМИ"
    LOCAL_TABLOID = "локальный таблоид"
    TWITTER = "Twitter-тренд"
    TIKTOK = "TikTok"
    TELEGRAM = "Telegram-канал"
    FORUM = "форум"
    RSS = "RSS-лента"
    GOOGLE_NEWS = "Google News"


class PriorityEnum(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class CreativeTypeEnum(str, Enum):
    NEWS = "новостной"
    EMOTIONAL = "эмоциональный"
    EXPOSE = "разоблачение"
    PERSONAL = "личная история"


class HeadlineFormatEnum(str, Enum):
    QUESTION = "вопрос"
    SHOCK = "шок"
    NUMBER = "цифра"
    QUOTE = "цитата"
    INTRIGUE = "интрига"


class InfopovodCreate(BaseModel):
    title: str
    source_url: HttpUrl
    source_type: SourceTypeEnum
    date: datetime
    category: CategoryEnum
    description: str
    trigger: TriggerEnum
    expiry: ExpiryEnum
    geo: str
    raw_content: Optional[str] = None


class InfopovodResponse(InfopovodCreate):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AngleCreate(BaseModel):
    infopovod_id: str
    angle_text: str
    offer_connection: str
    pain_point: str
    creative_type: CreativeTypeEnum
    priority: PriorityEnum


class AngleResponse(AngleCreate):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class HeadlineCreate(BaseModel):
    angle_id: str
    text: str
    format: HeadlineFormatEnum
    length_chars: int


class HeadlineResponse(HeadlineCreate):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class RiskAssessment(BaseModel):
    infopovod_id: str
    legal_risks: List[str] = Field(default_factory=list)
    ban_risks: List[str] = Field(default_factory=list)
    audience_negativity_risk: str = "низкий"
    reputation_risk: str = "низкий"
    expiration: str = ""


class TestResult(BaseModel):
    headline_id: str
    geo: str
    date_tested: datetime
    ctr: Optional[float] = None
    conversion: Optional[float] = None
    verdict: str
    impressions: Optional[int] = None
    clicks: Optional[int] = None


class MonitoringRequest(BaseModel):
    geo: str
    force: bool = False
    offer_context: Optional[str] = "финансовые услуги, инвестиции, криптовалюта"


class FeedbackRequest(BaseModel):
    report_id: str
    geo: str
    feedback: List[Dict[str, Any]]


class ReportPreview(BaseModel):
    id: str
    geo: str
    generated_at: datetime
    infopovods_count: int
    angles_count: int
    headlines_count: int
    top_ideas: List[Dict[str, Any]]


# Internal Models
class RawNewsItem(BaseModel):
    title: str
    source_url: HttpUrl
    source_type: SourceTypeEnum
    date: datetime
    raw_content: str
    geo_hint: Optional[str] = None