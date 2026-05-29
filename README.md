# Digital Persona

Digital Persona 是一个本地优先的 AI 数字人格 MVP。它从当前项目的 `聊天记录/` 目录读取聊天数据，清洗并标准化消息，分析目标人物的语言风格，提取典型对话样例，构建本地 RAG 检索库，然后通过 OpenAI-compatible API 生成接近目标人物风格的回复。

## 安全声明

本项目只用于个人、授权和本地研究场景。系统提示词内置以下边界：

- 只模仿说话风格，不声称自己就是目标人物本人。
- 不泄露或大段复述原始聊天记录。
- 不输出手机号、邮箱、地址、验证码等隐私信息。
- 不编造确定性的私人经历、关系、承诺或现实行动。
- 不协助冒充真人进行欺骗、诈骗或操控。

## 项目结构

```text
backend/
  app.py                    FastAPI 入口
  config.py                 环境变量配置
  pipeline.py               rebuild 主流程
  data/parser.py            聊天记录解析与清洗
  analysis/persona.py       persona_profile 生成
  analysis/examples.py      典型样例提取
  rag/vector_store.py       本地 TF-IDF 检索库
  llm/client.py             OpenAI-compatible 调用
  llm/prompts.py            安全 Prompt Builder
  scripts/rebuild.py        构建数据脚本
  scripts/smoke_chat.py     本地冒烟验证
frontend/
  app/page.tsx              Next.js 聊天界面
  app/globals.css           design.md 风格实现
聊天记录/                     原始聊天记录
DESIGN.md                    视觉设计参考
```

## 支持的数据格式

当前已实现：

- WeFlow 微信导出 JSON（本项目样例格式）
- Telegram Export JSON 的基础兼容
- 简单文本格式：`时间 昵称: 内容` 或 `昵称: 内容`

如果某个文件无法自动识别，`POST /rebuild` 和 `GET /stats` 会返回清晰错误。你可以在 `backend/data/parser.py` 中增加新的 `parse_*` 函数。

## 配置 API

复制后端配置示例：

```powershell
Copy-Item backend\.env.example backend\.env
```

编辑 `backend/.env`：

```env
OPENAI_API_KEY=你的 key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
TEMPERATURE=0.75
TOP_P=0.9
MAX_TOKENS=500
TARGET_PERSON_NAME=浅羽悠真
USER_PERSON_NAME=我
CHAT_RECORDS_DIR=../聊天记录
DATA_DIR=./data
```

### 接 OpenAI / DeepSeek / Qwen

只要服务兼容 OpenAI Chat Completions API，就改这三项：

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=...
MODEL_NAME=...
```

示例：

- OpenAI：`OPENAI_BASE_URL=https://api.openai.com/v1`
- DeepSeek：使用 DeepSeek 控制台给出的 OpenAI-compatible base URL 和模型名
- Qwen：使用 DashScope/OpenAI-compatible 网关给出的 base URL 和模型名

没有配置 `OPENAI_API_KEY` 时，后端会使用本地 fallback 回复，方便验证完整链路，但效果不代表真实模型效果。

## 准备聊天记录

把原始文件放到：

```text
./聊天记录/
```

目标人物和用户名称通过 `.env` 指定：

```env
TARGET_PERSON_NAME=浅羽悠真
USER_PERSON_NAME=我
```

在 WeFlow JSON 中，系统会优先使用 `senderDisplayName` 判断目标人物；`isSend=1` 且不是目标人物时会归为用户。

## 安装与运行后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m backend.scripts.rebuild
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

如果你从仓库根目录运行，也可以：

```powershell
python -m backend.scripts.rebuild
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

## 清洗数据、生成 persona、构建向量库

一条命令完成：

```powershell
python -m backend.scripts.rebuild
```

输出文件：

- `backend/data/normalized_messages.jsonl`
- `backend/data/persona_profile.json`
- `backend/data/examples.jsonl`
- `backend/data/vector_store/tfidf_store.pkl`
- `backend/data/stats.json`

清洗规则包括空消息、多媒体占位符、URL、手机号、邮箱、验证码、明显重复内容和无意义短内容。

## API

### GET /health

健康检查。

### GET /stats

返回消息数、样例数、目标人物发言数、来源文件和解析错误。

### POST /rebuild

重新读取 `聊天记录/`，生成标准化消息、persona_profile、样例和本地检索库。

### POST /chat

请求：

```json
{
  "message": "最近怎么样？",
  "context": [],
  "top_k": 5
}
```

响应：

```json
{
  "reply": "……还行吧，老样子",
  "retrieved_examples": [],
  "persona_ready": true
}
```

## 运行前端

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

打开 Next.js 输出的本地地址，默认连接 `http://localhost:8000`。

页面包含：

- 聊天输入框
- 消息展示
- loading 状态
- API 错误提示
- 当前 persona 状态
- 重新构建数据入口

## 验证

后端基础验证：

```powershell
python -m backend.scripts.rebuild
python -m backend.scripts.smoke_chat
python -m pytest backend/tests
```

前端验证：

```powershell
cd frontend
npm run build
```

## 常见问题

### 为什么不用微调或 GPU？

MVP 使用 persona_profile + 样例 RAG + OpenAI-compatible API，不训练模型，不依赖 GPU。

### 会不会把完整聊天记录发给模型？

不会主动发送完整记录。`/chat` 只发送 persona_profile、少量检索样例和当前问题。仍建议只在可信 API 或本地兼容服务上使用。

### 检索库为什么不是 ChromaDB？

MVP 使用 scikit-learn TF-IDF 本地检索，安装简单、无需服务进程。后续可以在 `backend/rag/vector_store.py` 后面替换为 ChromaDB 或其他向量库，API 层无需大改。

### 如何支持新的聊天导出格式？

在 `backend/data/parser.py` 中新增解析函数，并在 `parse_file()` 中按后缀或结构分发。

### 生成回复不像目标人物怎么办？

确认：

1. `TARGET_PERSON_NAME` 与聊天记录中的 `senderDisplayName` 一致。
2. `python -m backend.scripts.rebuild` 后 `target_message_count` 足够多。
3. 配置了真实可用的 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 和 `MODEL_NAME`。
4. 必要时调整 `backend/analysis/persona.py` 或 `backend/llm/prompts.py`。
