from __future__ import annotations

from collections import Counter

from backend.analysis.examples import build_examples
from backend.analysis.persona import analyze_persona
from backend.config import Settings
from backend.data.parser import load_chat_records
from backend.rag.vector_store import LocalVectorStore
from backend.storage import write_json, write_jsonl


def rebuild_all(settings: Settings) -> dict:
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    messages, errors = load_chat_records(settings.chat_records_dir, settings.target_person_name, settings.user_person_name)
    examples = build_examples(messages)
    profile = analyze_persona(messages, settings.target_person_name)

    write_jsonl(settings.normalized_messages_path, [message.to_dict() for message in messages])
    write_jsonl(settings.examples_path, [example.to_dict() for example in examples])
    write_json(settings.profile_path, profile)
    LocalVectorStore(settings.vector_store_dir).build(examples)

    by_speaker = Counter(message.speaker for message in messages)
    stats = {
        "chat_records_dir": str(settings.chat_records_dir),
        "target_name": settings.target_person_name,
        "user_name": settings.user_person_name,
        "message_count": len(messages),
        "target_message_count": by_speaker.get("target", 0),
        "user_message_count": by_speaker.get("user", 0),
        "other_message_count": by_speaker.get("other", 0),
        "example_count": len(examples),
        "source_files": sorted({message.source_file for message in messages if message.source_file}),
        "errors": errors,
    }
    write_json(settings.stats_path, stats)
    return stats
