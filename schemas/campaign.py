from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Product(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    asset_path: Optional[str] = None


class Brand(BaseModel):
    logo_path: str
    primary_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    font_name: str
    theme: str
    domain: str


class CampaignBrief(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    campaign_id: str = Field(..., min_length=1)
    products: List[Product] = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    target_audience: str = Field(..., min_length=1)
    campaign_message: str = Field(..., min_length=1, max_length=500)
    brand: Brand


class CampaignOutput(BaseModel):
    campaign_id: str
    product_name: str
    aspect_ratio: str
    output_path: str
    language: str
    translated_message: str
    asset_generated: bool
    compliance_passed: bool
    legal_flags: List[str]
    generation_time_seconds: float


class ComplianceResult(BaseModel):
    logo_detected: bool
    logo_confidence: float
    primary_color_present: bool
    primary_color_percentage: float
    secondary_color_present: bool
    secondary_color_percentage: float
    passed: bool
    violations: List[str]


class LegalCheckResult(BaseModel):
    prohibited_words_found: List[str]
    severity: str
    blocked: bool
    details: str
