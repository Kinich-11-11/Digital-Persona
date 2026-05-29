from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal


SpeakerRole = Literal["user", "target", "other"]


@dataclass(slots=True)
class ChatMessage:
    speaker: SpeakerRole
    speaker_name: str
    content: str
    time: str | None = None
    source_file: str | None = None
    conversation_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class DialogueExample:
    input: str
    output: str
    context: list[str]
    source_file: str | None = None
    time: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
