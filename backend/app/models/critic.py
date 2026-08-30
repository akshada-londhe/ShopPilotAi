from pydantic import BaseModel, Field, computed_field, field_validator


class CriticFeedback(BaseModel):
    missing_data: list[str] = Field(default_factory=list)
    negative_prompts: list[str] = Field(default_factory=list)
    failed_criteria: list[str] = Field(default_factory=list)

    @field_validator(
        "missing_data", "negative_prompts", "failed_criteria", mode="before"
    )
    @classmethod
    def normalize_list_fields(cls, value: object) -> object:
        if isinstance(value, str):
            return [value]
        return value


class CriticVerdict(BaseModel):
    relevance: int = Field(ge=0, le=10)
    requirement_match: int = Field(ge=0, le=10)
    evidence_quality: int = Field(ge=0, le=10)
    completeness: int = Field(ge=0, le=10)
    contradiction_flag: bool
    feedback: CriticFeedback

    @computed_field
    @property
    def weighted_score(self) -> float:
        return round(
            0.3 * self.relevance
            + 0.3 * self.requirement_match
            + 0.25 * self.evidence_quality
            + 0.15 * self.completeness,
            2,
        )

    @computed_field
    @property
    def passed(self) -> bool:
        if self.contradiction_flag:
            return False
        # Primary gate: the PRD rubric (FR9).
        if self.weighted_score >= 7.0:
            return True
        # Relevance gate: prices/specs are frequently absent from Tavily's
        # scraped text (a data-source limit, not a bad match). A result that is
        # clearly the right product AND meets the buyer's requirements should
        # pass even when evidence_quality/completeness are dragged down by
        # missing price data. We do NOT let this bypass contradictions.
        return self.relevance >= 7 and self.requirement_match >= 7
