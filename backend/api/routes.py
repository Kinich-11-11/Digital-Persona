from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.schemas import ChatRequest, ChatResponse, RebuildResponse
from backend.config import get_settings
from backend.llm.client import LLMClient
from backend.pipeline import rebuild_all
from backend.rag.vector_store import LocalVectorStore
from backend.storage import read_json

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"ok": True, "service": "digital-persona"}


@router.get("/stats")
def stats() -> dict:
    settings = get_settings()
    return read_json(settings.stats_path, {"message_count": 0, "example_count": 0, "errors": ["尚未构建数据，请调用 POST /rebuild"]})


@router.post("/rebuild", response_model=RebuildResponse)
def rebuild() -> RebuildResponse:
    settings = get_settings()
    try:
        result = rebuild_all(settings)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RebuildResponse(ok=True, stats=result)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    profile = read_json(settings.profile_path, {})
    if not profile:
        rebuild_all(settings)
        profile = read_json(settings.profile_path, {})
    store = LocalVectorStore(settings.vector_store_dir)
    examples = store.search(request.message, request.top_k)
    reply = await LLMClient(settings).generate(request.message, profile, examples, request.context)
    return ChatResponse(reply=reply, retrieved_examples=examples, persona_ready=bool(profile))
