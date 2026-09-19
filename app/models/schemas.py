from pydantic import BaseModel, Field
from typing import Literal

class BrandProfile(BaseModel):
    name: str
    audience: str = "technology leaders"
    voice: str = "clear, authoritative, useful"
    banned_phrases: list[str] = []
    required_terms: list[str] = []

class CampaignRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    goal: str = "educate"
    channels: list[Literal["blog","linkedin","x","newsletter","visual_brief"]] = ["blog","linkedin"]
    keywords: list[str] = []
    brand: BrandProfile
    research_context: list[str] = []

class Artifact(BaseModel):
    channel: str
    title: str
    content: str
    score: float = 0
    metadata: dict = {}

class CampaignResponse(BaseModel):
    campaign_id: str
    artifacts: list[Artifact]
    evidence: list[str]
    quality: dict
