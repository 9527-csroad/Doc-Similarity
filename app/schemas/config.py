from pydantic import BaseModel, Field


class ThresholdConfig(BaseModel):
    threshold: float = Field(ge=0.0, le=1.0)


class ThresholdResponse(BaseModel):
    global_threshold: float
    source: str  # "global", "user", "request"
