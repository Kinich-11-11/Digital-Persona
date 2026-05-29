from __future__ import annotations

from backend.models import ChatMessage, DialogueExample


def build_examples(messages: list[ChatMessage], limit: int = 500) -> list[DialogueExample]:
    examples: list[DialogueExample] = []
    for index, message in enumerate(messages):
        if message.speaker != "target":
            continue
        previous = []
        cursor = index - 1
        while cursor >= 0 and len(previous) < 3:
            item = messages[cursor]
            if item.conversation_id != message.conversation_id:
                break
            if item.content:
                previous.append(f"{item.speaker_name}: {item.content}")
            if item.speaker in {"user", "other"}:
                break
            cursor -= 1
        previous.reverse()
        if not previous:
            continue
        prompt = previous[-1].split(": ", 1)[-1]
        examples.append(DialogueExample(
            input=prompt,
            output=message.content,
            context=previous,
            source_file=message.source_file,
            time=message.time,
        ))
        if len(examples) >= limit:
            break
    return examples
