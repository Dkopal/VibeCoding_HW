# AI Newsletter Generator

A multi-agent system that researches topics in parallel and assembles a personalized newsletter, demonstrating four orchestration patterns: **Supervisor**, **Parallel**, **Loop**, and **Conditional**.

---

## Architecture

```
User Input (topics, style, language)
        │
        ▼
┌──────────────────┐
│  SUPERVISOR      │  Plans research tasks, assigns search queries
│  AGENT           │  → SSE: supervisor:plan_ready
└────────┬─────────┘
         │  asyncio.gather() — one worker per topic
         ▼
┌────────────────────────────────────┐
│         PARALLEL RESEARCH          │
│  [Worker 1]  [Worker 2]  [Worker N]│  Web search tool per topic
│  → SSE: research:started / done    │
└────────────────┬───────────────────┘
                 │  conditional check
                 ▼
         ┌───────────────┐
         │ CONDITIONAL   │  found=false → skip + warn
         │ GATE          │  → SSE: research:skipped
         └───────┬───────┘
                 │
                 ▼
        ┌─────────────────┐
        │  WRITER AGENT   │  Markdown draft per topic section
        │                 │  → SSE: writer:draft_ready
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  EDITOR LOOP    │  Checks: length, tone, coverage,
        │  (max 3 iter.)  │  no repetition. Loops back to
        │                 │  writer with instructions if needed.
        │                 │  → SSE: editor:iteration:{n}
        │                 │  → SSE: editor:approved
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  OUTPUT         │  Markdown → styled HTML
        │  FORMATTER      │  → SSE: output:ready
        └─────────────────┘
```

---

## Orchestration Patterns

| Pattern | Where | Implementation |
|---|---|---|
| **Supervisor** | Top-level | `agents/supervisor.py` — plans tasks, assigns search queries per topic |
| **Parallel** | Research | `asyncio.gather()` in `agents/researcher.py` — all workers run concurrently |
| **Loop** | Editor | `agents/editor.py` — max 3 iterations, exits early on `APPROVED` |
| **Conditional** | After research | `orchestrator.py` — skips topics where `found=false` |

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ · FastAPI · Uvicorn |
| AI | Anthropic SDK · `claude-haiku-4-5-20251001` · web search tool |
| Streaming | Server-Sent Events (SSE) |
| Frontend | React 19 · TypeScript · Tailwind CSS · Vite |

---

## Project Structure

```
newsletter-agent/
├── backend/
│   ├── main.py              # FastAPI app — POST /generate → SSE stream
│   ├── orchestrator.py      # Wires all agents, emits SSE events
│   ├── models.py            # Pydantic request/response models
│   ├── agents/
│   │   ├── supervisor.py    # Plans research tasks from topic list
│   │   ├── researcher.py    # Parallel web-search workers
│   │   ├── writer.py        # Draft writer (style + language aware)
│   │   └── editor.py        # Quality-check loop (max 3 iterations)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── InputForm.tsx   # Tag input, style/language selectors
│   │   │   ├── AgentLog.tsx    # Live colour-coded event stream
│   │   │   └── Newsletter.tsx  # Iframe preview + copy/download
│   │   └── hooks/
│   │       └── useSSE.ts       # SSE fetch hook with cancel support
│   └── package.json
├── .env.example
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone & configure

```bash
git clone <repo-url>
cd newsletter-agent
cp ../.env.example ../.env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## Usage

1. Open `http://localhost:5173`
2. Type a topic and press **Enter** to add it (up to 10 topics)
3. Choose **Style** (Casual / Formal) and **Language** (English / Czech)
4. Click **Generate Newsletter**
5. Watch the **Agent Log** stream in real time as each agent runs
6. The finished newsletter appears below — **Copy HTML** or **Download**

---

## SSE Event Reference

| Event | Payload | Meaning |
|---|---|---|
| `supervisor:plan_ready` | `{tasks[]}` | Research plan ready |
| `research:started` | `{topic}` | Worker begun for topic |
| `research:done` | `{topic, summary, sources, found}` | Worker finished |
| `research:skipped` | `{topic}` | No results — topic excluded |
| `writer:draft_ready` | `{length}` | Draft character count |
| `editor:iteration:{n}` | `{iteration}` | Editor pass number |
| `editor:approved` | `{iterations, forced?}` | Draft accepted |
| `output:ready` | `{html}` | Final HTML newsletter |
| `error` | `{message}` | Pipeline error |

---

## Key Technical Decisions

**Why `asyncio.gather()` for research?**  
Topics are fully independent — no reason to wait. With 5 topics and ~2 s per search, parallel cuts wall time from ~10 s to ~2 s.

**Why SSE instead of WebSockets?**  
Generation is unidirectional (server → client). SSE is simpler, works over plain HTTP/1.1, and reconnects automatically in browsers.

**Why a hard `max_iterations=3` on the editor?**  
Unbounded loops burn tokens and wall time. Three passes are enough to catch most quality issues; the editor marks forced approvals so the client knows.

**Why Haiku?**  
Speed and cost. Haiku handles structured JSON tasks (supervisor, researcher) and light editorial passes well. Swap `MODEL` in each agent file to upgrade.
