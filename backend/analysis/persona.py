from __future__ import annotations

from collections import Counter
from statistics import mean

from backend.models import ChatMessage


def _top_terms(texts: list[str], limit: int = 24) -> list[str]:
    counter: Counter[str] = Counter()
    stop = set("的是了我你他她它在就都而及与着或一个没有我们你们他们这个那个怎么什么不是还有因为所以如果但是然后可以".split())
    for text in texts:
        for token in _tokenize_zh(text):
            if token not in stop and len(token.strip()) >= 1:
                counter[token] += 1
    return [word for word, _ in counter.most_common(limit)]


def _tokenize_zh(text: str) -> list[str]:
    chunks = []
    current = ""
    for char in text:
        if "一" <= char <= "鿿":
            if current and not ("一" <= current[-1] <= "鿿"):
                chunks.append(current)
                current = ""
            current += char
            if len(current) >= 2:
                chunks.append(current)
                current = current[-1]
        elif char.isalnum():
            current += char.lower()
        else:
            if current:
                chunks.append(current)
                current = ""
    if current:
        chunks.append(current)
    return chunks


def analyze_persona(messages: list[ChatMessage], target_name: str) -> dict:
    target_messages = [m for m in messages if m.speaker == "target"]
    texts = [m.content for m in target_messages]
    lengths = [len(text) for text in texts] or [0]
    punctuation = Counter(char for text in texts for char in text if char in "。！？!?…~～（）()")
    short_ratio = sum(1 for n in lengths if n <= 12) / max(len(lengths), 1)
    question_ratio = sum(1 for text in texts if "?" in text or "？" in text) / max(len(texts), 1)
    exclaim_ratio = sum(1 for text in texts if "!" in text or "！" in text) / max(len(texts), 1)
    ellipsis_ratio = sum(1 for text in texts if "…" in text or "。。。" in text or "..." in text) / max(len(texts), 1)
    top_terms = _top_terms(texts)

    style = []
    if short_ratio > 0.55:
        style.append("偏短句、即时反应式回复，常用几个字表达态度")
    else:
        style.append("会使用中等长度句子解释想法")
    if ellipsis_ratio > 0.08:
        style.append("经常用省略号表达停顿、无语或吐槽")
    if question_ratio > 0.12:
        style.append("会用反问或追问推进对话")
    if exclaim_ratio > 0.08:
        style.append("情绪表达直接，偶尔用感叹号加强语气")

    return {
        "target_name": target_name,
        "message_count": len(target_messages),
        "overall_impression": "一个偏日常、轻吐槽、反应快的聊天人格。回复更像即时聊天而不是正式写作。",
        "tone_style": "；".join(style) or "自然口语化，避免书面腔。",
        "common_words": top_terms,
        "reply_length_preference": {
            "average_chars": round(mean(lengths), 1),
            "median_hint": "多数回复很短" if short_ratio > 0.55 else "短句和中等句混合",
        },
        "emotion_style": "用省略号、括号、短促回应表达无语、犹豫、吐槽或自嘲；不需要过度热情。",
        "humor_style": "偏冷吐槽、轻微自嘲、顺着上下文接梗。",
        "comfort_style": "安慰时保持口语和克制，不要突然鸡汤化，可以先认同再给一点轻建议。",
        "refusal_style": "拒绝时短而自然，可用‘算了’、‘不太行’一类表达，但避免攻击性。",
        "punctuation_profile": dict(punctuation.most_common(12)),
        "do_not_imitate_or_leak": [
            "不要声称自己就是目标人物本人",
            "不要输出手机号、邮箱、地址、验证码等隐私信息",
            "不要大段复述原始聊天记录",
            "不要编造确定性的私人经历或现实承诺",
        ],
        "behavior_rules": [
            "只模仿语言风格，不冒充真人身份",
            "优先生成简短、自然、带一点停顿感的中文回复",
            "缺少事实时用模糊但符合风格的表达",
            "避免过度解释系统、模型或数据来源",
        ],
    }
