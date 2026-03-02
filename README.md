# Financial Document Analyzer

A comprehensive financial document analysis system that processes corporate reports, financial statements, and investment documents using AI-powered agents built with **CrewAI**.

## Features

- **Upload & Analyze** — Upload any financial PDF and get AI-powered analysis
- **Multi-Agent Pipeline** — 4 specialized agents (Verifier → Analyst → Advisor → Risk Assessor) work sequentially
- **Investment Recommendations** — Evidence-based, compliance-aware investment guidance
- **Risk Assessment** — Structured risk analysis with mitigation strategies
- **Web Interface** — Beautiful, dark-mode frontend UI with drag-and-drop PDF uploads and Markdown rendering
- **Async Processing** — Queue-based processing via Celery + Redis for concurrent requests
- **Result Storage** — SQLite database stores all analysis results and user queries
- **REST API** — FastAPI-powered endpoints for integration

---

## Bugs Found & Fixed

### Deterministic Bugs

| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | `tools.py` | `from crewai_tools import tools` — wrong import | Changed to `from crewai.tools import tool` + `from crewai_tools import SerperDevTool` |
| 2 | `tools.py` | `Pdf(file_path=path).load()` — `Pdf` class doesn't exist | Replaced with `PyPDFLoader` from `langchain_community.document_loaders` |
| 3 | `tools.py` | `async def read_data_tool` — async incompatible with CrewAI tool usage | Made synchronous, decorated with `@tool("read_financial_document")` |
| 4 | `tools.py` | Tool was a raw class method, not a CrewAI-compatible tool | Converted to standalone function with `@tool` decorator |
| 5 | `agents.py` | `from crewai.agents import Agent` — wrong import path | Changed to `from crewai import Agent` |
| 6 | `agents.py` | `llm = llm` — self-referencing undefined variable | Changed to `llm = "gemini/gemini-2.0-flash"` |
| 7 | `agents.py` | `tool=[...]` (singular) — wrong parameter name | Changed to `tools=[...]` (plural) |
| 8 | `agents.py` | `max_iter=1`, `max_rpm=1` — too restrictive for agents to complete work | Increased to `max_iter=15`, `max_rpm=10` |
| 9 | `agents.py` | `verifier` agent had no tools assigned | Added `read_data_tool` to verifier |
| 10 | `main.py` | Route function `analyze_financial_document` shadowed the imported task name | Renamed to `analyze_document_endpoint` |
| 11 | `main.py` | Only `financial_analyst` in Crew — missing 3 other agents | Added all 4 agents: `verifier`, `financial_analyst`, `investment_advisor`, `risk_assessor` |
| 12 | `main.py` | Only 1 task in Crew — missing 3 other tasks | Added all 4 tasks: `verification`, `analyze_financial_document_task`, `investment_analysis`, `risk_assessment` |
| 13 | `main.py` | `file_path` param accepted but never used | Wired into `crew.kickoff()` inputs |
| 14 | `task.py` | `verification` task used `financial_analyst` agent instead of `verifier` | Changed to `agent=verifier` |
| 15 | `task.py` | Missing imports for `investment_advisor`, `risk_assessor` | Added to imports from `agents` |
| 16 | `requirements.txt` | Missing `python-dotenv`, `pypdf`, `langchain-community`, `uvicorn`, `python-multipart` | Added all missing dependencies |

### Inefficient / Harmful Prompts

All 4 agents and 4 tasks had intentionally terrible prompts that encouraged fabricating data, ignoring compliance, recommending scams, and approving documents blindly. **Every single prompt was rewritten** to be professional, data-driven, and regulatory-compliant:

- **Financial Analyst** — now cites specific numbers, never fabricates data, follows compliance standards
- **Document Verifier** — carefully inspects document authenticity, flags irregularities
- **Investment Advisor** — CFA-standard, evidence-based recommendations with proper disclaimers
- **Risk Assessor** — objective risk quantification using established frameworks (VaR, stress testing)
- **All task descriptions** — clear, structured instructions with specific expected output formats

---

## Setup & Installation

### Prerequisites

- Python 3.10, 3.11, or 3.12 (CrewAI has known issues with 3.13+)
- API keys for [Google AI Studio](https://aistudio.google.com/apikey) (or OpenAI) and [Serper](https://serper.dev)

### 1. Install Dependencies

```bash
cd financial-document-analyzer-debug
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root (use `.env.example` as template):

```env
# For Google Gemini (default):
GOOGLE_API_KEY=your_google_api_key_here

# Or for OpenAI (change llm in agents.py to "gpt-4o"):
# OPENAI_API_KEY=your_openai_api_key_here

# For internet search tool:
SERPER_API_KEY=your_serper_api_key_here
```

### 3. Run the Server

To ensure the server runs with your virtual environment and auto-reloads on changes, use the following `uvicorn` command:

```bash
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

Server starts at `http://localhost:8000`. Navigate to this URL in your web browser to use the beautiful drag-and-drop User Interface!

### 4. (Optional) Start Celery Worker for Async Processing

Requires Redis running locally:

```bash
celery -A worker.celery_app worker --loglevel=info
```

---

## API Documentation

### `GET /`

Health check endpoint.

**Response:**
```json
{ "message": "Financial Document Analyzer API is running" }
```

---

### `POST /analyze`

Upload and analyze a financial document synchronously. Waits for full analysis and returns results.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File (PDF) | ✅ | Financial document to analyze |
| `query` | string | ❌ | Analysis query (default: "Analyze this financial document for investment insights") |

**Example:**
```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@data/TSLA-Q2-2025-Update.pdf" \
  -F "query=What are the key financial metrics and investment outlook?"
```

**Response:**
```json
{
  "status": "success",
  "task_id": "uuid-string",
  "query": "What are the key financial metrics...",
  "analysis": "Full analysis text...",
  "file_processed": "TSLA-Q2-2025-Update.pdf"
}
```

---

### `POST /analyze/async`

Submit a document for background processing via Celery queue. Returns immediately with a `task_id`.

**Request:** Same as `/analyze`

**Response:**
```json
{
  "status": "queued",
  "task_id": "uuid-string",
  "message": "Document submitted for analysis. Use GET /result/{task_id} to check status."
}
```

> ⚠️ Requires Redis + Celery worker running.

---

### `GET /result/{task_id}`

Retrieve analysis results by task ID. Works for both sync and async analyses.

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "success",
  "filename": "TSLA-Q2-2025-Update.pdf",
  "query": "What are the key financial metrics...",
  "analysis": "Full analysis text...",
  "error": null,
  "created_at": "2026-02-26 17:00:00",
  "completed_at": "2026-02-26 17:02:30"
}
```

**Status values:** `pending` → `processing` → `success` | `failed`

---

## Project Structure

```
financial-document-analyzer-debug/
├── main.py              # FastAPI app with all API endpoints
├── agents.py            # 4 CrewAI agents (analyst, verifier, advisor, risk assessor)
├── task.py              # 4 CrewAI tasks (analysis, investment, risk, verification)
├── tools.py             # PDF reader tool + search tool
├── database.py          # SQLAlchemy models + CRUD helpers (SQLite)
├── worker.py            # Celery worker for async queue processing
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── static/              # Web Frontend UI
│   ├── index.html       # Drag-and-drop web interface
│   └── style.css        # Premium dark-mode styling
├── data/                # PDF upload directory
│   └── TSLA-Q2-2025-Update.pdf
└── outputs/             # Analysis output directory
```

## Agent Pipeline

```
Document Upload
      ↓
┌─────────────────┐
│   Verifier      │  Confirms document is a legitimate financial report
└────────┬────────┘
         ↓
┌─────────────────┐
│ Financial       │  Extracts key metrics, trends, and financial data
│ Analyst         │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Investment      │  Provides evidence-based investment recommendations
│ Advisor         │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Risk Assessor   │  Identifies and quantifies financial risks
└────────┬────────┘
         ↓
   Final Report
```
