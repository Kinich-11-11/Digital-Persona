from __future__ import annotations

import re

from openai import AsyncOpenAI

from backend.config import Settings
from backend.llm.prompts import build_system_prompt, build_user_prompt

SENSITIVE_RE = re.compile(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|(?:\+?86[-\s]?)?1[3-9]\d{9}|(?<!\d)\d{6}(?!\d))")


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key or "EMPTY", base_url=settings.openai_base_url)

    async def generate(self, user_input: str, persona_profile: dict, examples: list[dict], recent_context: list[str] | None = None) -> str:
        if not self.settings.openai_api_key:
            return self._fallback_reply(user_input, persona_profile, examples)
        response = await self.client.chat.completions.create(
            model=self.settings.model_name,
            messages=[
                {"role": "system", "content": build_system_prompt(persona_profile)},
                {"role": "user", "content": build_user_prompt(user_input, examples, recent_context)},
            ],
            temperature=self.settings.temperature,
            top_p=self.settings.top_p,
            max_tokens=self.settings.max_tokens,
        )
        text = response.choices[0].message.content or ""
        return self._redact(text.strip())

    def _fallback_reply(self, user_input: str, persona_profile: dict, examples: list[dict]) -> str:
        if examples:
            sample = examples[0].get("output", "")
            if sample and len(sample) <= 40:
                return self._redact(sample)
        words = persona_profile.get("common_words") or []
        if "怎么" in user_input or "?" in user_input or "？" in user_input:
            return "我也不太确定……先看看吧"
        if words:
            return f"{words[0]}……有点难说"
        return "嗯……差不多吧"

    @staticmethod
    def _redact(text: str) -> str:
        return SENSITIVE_RE.sub("[已隐藏]", text)
