from pydantic import BaseModel, Field


class EvalCriterion(BaseModel):
    name: str
    description: str
    weight: float = 1.0


class EvalCase(BaseModel):
    id: str
    query: str
    expected_tools: list[str] = Field(default_factory=list)
    required_checks: list[str] = Field(default_factory=list)
    description: str = ""


class EvalDataset(BaseModel):
    name: str
    version: str = "1.0"
    cases: list[EvalCase] = Field(default_factory=list)
    criteria: list[EvalCriterion] = Field(default_factory=list)
