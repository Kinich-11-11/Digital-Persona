from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    context: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=10)


class ChatResponse(BaseModel):
    reply: str
    retrieved_examples: list[dict]
    persona_ready: bool


class RebuildResponse(BaseModel):
    ok: bool
    stats: dict
