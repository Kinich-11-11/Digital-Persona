from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from backend.models import ChatMessage, SpeakerRole

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?86[-\s]?)?1[3-9]\d{9}(?!\d)")
CODE_RE = re.compile(r"(?<!\d)\d{4,8}(?!\d)")
MEDIA_RE = re.compile(r"\[(图片|语音|视频|表情|文件|动画表情|位置|链接|音乐|小程序)\]")
ONLY_PUNCT_RE = re.compile(r"^[\s。．.，,、!！?？~～…·\-—_=+（）()【】\[\]{}<>《》|/\\:：;；'\"“”‘’]+$")
QUOTE_RE = re.compile(r"\[引用\s+([^：:]+)[：:](.*?)\]$", re.S)


def clean_content(raw: str) -> str:
    text = str(raw or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = QUOTE_RE.sub("", text)
    text = MEDIA_RE.sub(" ", text)
    text = URL_RE.sub("[链接]", text)
    text = EMAIL_RE.sub("[邮箱]", text)
    text = PHONE_RE.sub("[手机号]", text)
    text = CODE_RE.sub(lambda m: "[数字]" if len(m.group(0)) >= 6 else m.group(0), text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_meaningful(text: str) -> bool:
    if not text:
        return False
    if len(text) <= 1:
        return False
    if ONLY_PUNCT_RE.match(text):
        return False
    if text in {"[链接]", "[邮箱]", "[手机号]", "[数字]"}:
        return False
    return True


def speaker_role(name: str, is_send: Any, target_name: str, user_name: str) -> SpeakerRole:
    if name == target_name:
        return "target"
    if name == user_name:
        return "user"
    if user_name in {"我", "me", "Me"} and is_send == 1 and name != target_name:
        return "user"
    return "other"


def parse_weflow_json(path: Path, payload: dict, target_name: str, user_name: str) -> list[ChatMessage]:
    session = payload.get("session") or {}
    conversation_id = session.get("displayName") or session.get("nickname") or path.stem
    messages = []
    seen = set()
    for item in payload.get("messages", []):
        if item.get("type") not in {"文本消息", "引用消息"}:
            continue
        content = clean_content(item.get("content", ""))
        if not is_meaningful(content):
            continue
        dedupe_key = (item.get("senderDisplayName"), content, item.get("formattedTime"))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        name = item.get("senderDisplayName") or item.get("senderUsername") or "unknown"
        messages.append(ChatMessage(
            speaker=speaker_role(name, item.get("isSend"), target_name, user_name),
            speaker_name=name,
            content=content,
            time=item.get("formattedTime") or str(item.get("createTime") or "") or None,
            source_file=path.name,
            conversation_id=conversation_id,
        ))
    return messages


def parse_telegram_json(path: Path, payload: dict, target_name: str, user_name: str) -> list[ChatMessage]:
    messages = []
    for item in payload.get("messages", []):
        raw = item.get("text", "")
        if isinstance(raw, list):
            raw = "".join(part if isinstance(part, str) else part.get("text", "") for part in raw)
        content = clean_content(str(raw))
        if not is_meaningful(content):
            continue
        name = item.get("from") or item.get("actor") or "unknown"
        messages.append(ChatMessage(
            speaker=speaker_role(name, None, target_name, user_name),
            speaker_name=name,
            content=content,
            time=item.get("date"),
            source_file=path.name,
            conversation_id=payload.get("name") or path.stem,
        ))
    return messages


def parse_text_export(path: Path, target_name: str, user_name: str) -> list[ChatMessage]:
    patterns = [
        re.compile(r"^\[?(?P<time>\d{4}[-/]\d{1,2}[-/]\d{1,2}[^\]]{0,20})\]?\s*(?P<name>[^:：]{1,40})[:：]\s*(?P<content>.+)$"),
        re.compile(r"^(?P<name>[^:：]{1,40})[:：]\s*(?P<content>.+)$"),
    ]
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        match = next((m for p in patterns if (m := p.match(line))), None)
        if not match:
            continue
        content = clean_content(match.group("content"))
        if not is_meaningful(content):
            continue
        name = match.group("name").strip()
        rows.append(ChatMessage(
            speaker=speaker_role(name, None, target_name, user_name),
            speaker_name=name,
            content=content,
            time=match.groupdict().get("time"),
            source_file=path.name,
            conversation_id=path.stem,
        ))
    return rows


def parse_file(path: Path, target_name: str, user_name: str) -> list[ChatMessage]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "weflow" in payload and "messages" in payload:
            return parse_weflow_json(path, payload, target_name, user_name)
        if isinstance(payload, dict) and "messages" in payload:
            return parse_telegram_json(path, payload, target_name, user_name)
        raise ValueError(f"无法识别 JSON 聊天格式：{path.name}")
    if suffix in {".txt", ".log", ".md"}:
        return parse_text_export(path, target_name, user_name)
    return []


def load_chat_records(records_dir: Path, target_name: str, user_name: str) -> tuple[list[ChatMessage], list[str]]:
    errors = []
    messages = []
    if not records_dir.exists():
        return [], [f"聊天记录目录不存在：{records_dir}"]
    for path in sorted(records_dir.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        try:
            messages.extend(parse_file(path, target_name, user_name))
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
    messages.sort(key=lambda item: (item.conversation_id or "", item.time or ""))
    return messages, errors
