from pydantic import BaseModel, Field


class Budget(BaseModel):
    min: int = 0
    max: int
    currency: str = "INR"


class ClarificationContext(BaseModel):
    round: int
    previous_questions: list[str] = Field(default_factory=list)
    user_answers: list[str] = Field(default_factory=list)


class NormalizedQuery(BaseModel):
    intent: str
    category: str
    budget: Budget
    constraints: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    use_case: str | None = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    assumptions_made: list[str] = Field(default_factory=list)
