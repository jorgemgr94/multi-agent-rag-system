"""Briefing-related schemas."""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


class BriefingRequest(BaseModel):
    """Request to generate a deal briefing."""

    company_name: str = Field(..., description="Target company name")
    industry: str | None = Field(default=None, description="Industry vertical")
    company_size: str | None = Field(
        default=None, description="startup, mid-market, enterprise"
    )
    meeting_type: str | None = Field(
        default=None, description="initial_call, demo, negotiation, etc."
    )
    specific_questions: list[str] = Field(
        default_factory=list, description="Specific questions to address"
    )


class SimilarDeal(BaseModel):
    """A similar past deal."""

    company: str
    similarity_score: float
    outcome: str
    deal_value: int | str | None = None
    key_learnings: str
    source: str

    @field_validator("deal_value", mode="before")
    @classmethod
    def parse_deal_value(cls, v: Any) -> int | None:
        """Parse deal value from various formats."""
        if v is None:
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            # Remove currency symbols and parse
            cleaned = re.sub(r"[^\d]", "", v)
            if cleaned:
                return int(cleaned)
        return None


class CompetitivePositioning(BaseModel):
    """Competitive analysis section."""

    summary: str
    objection_responses: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class RecommendedApproach(BaseModel):
    """Recommended sales approach."""

    talking_points: list[str] = Field(default_factory=list)
    questions_to_ask: list[str] = Field(default_factory=list)
    pricing_guidance: str | None = None
    sources: list[str] = Field(default_factory=list)


class BriefingMetadata(BaseModel):
    """Metadata about the briefing generation."""

    generated_at: str
    documents_searched: int
    documents_cited: int
    confidence_score: float
    agents_used: list[str] = Field(default_factory=list)


class BriefingResponse(BaseModel):
    """Complete deal briefing response."""

    company_summary: dict[str, Any] = Field(default_factory=dict)
    similar_deals: list[SimilarDeal] = Field(default_factory=list)
    competitive_positioning: CompetitivePositioning | None = None
    recommended_approach: RecommendedApproach | None = None
    metadata: BriefingMetadata | None = None
