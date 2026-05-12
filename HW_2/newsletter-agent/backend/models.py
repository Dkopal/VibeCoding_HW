from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    topics: list[str] = Field(min_length=1, max_length=10)
    style: str = Field(default="casual", pattern="^(casual|formal)$")
    language: str = Field(default="EN", pattern="^(EN|CZ)$")


class ResearchResult(BaseModel):
    topic: str
    summary: str
    sources: list[str]
    found: bool


class SupervisorTask(BaseModel):
    topic: str
    search_query: str
    priority: int
