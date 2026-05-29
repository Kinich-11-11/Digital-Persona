from backend.config import get_settings
from backend.llm.client import LLMClient
from backend.rag.vector_store import LocalVectorStore
from backend.storage import read_json


async def main() -> None:
    settings = get_settings()
    profile = read_json(settings.profile_path, {})
    examples = LocalVectorStore(settings.vector_store_dir).search("最近怎么样", 3)
    reply = await LLMClient(settings).generate("最近怎么样", profile, examples, [])
    print({"reply": reply, "examples": len(examples), "persona_ready": bool(profile)})


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
