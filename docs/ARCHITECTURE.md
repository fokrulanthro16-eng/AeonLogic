# AeonLogic — Architecture

> Full architecture reference with Mermaid diagram, component breakdown, Qwen Cloud / Alibaba Cloud integration, and environment-based secret handling.

Standalone diagram file: [`docs/architecture-diagram.mmd`](architecture-diagram.mmd)

---

## Architecture Diagram

> **Devpost export:** paste `docs/architecture-diagram.mmd` into [https://mermaid.live](https://mermaid.live) → Actions → Export PNG → save as `media/screenshots/09-architecture-diagram.png`

```mermaid
%%{init: {"theme": "dark", "themeVariables": {"primaryColor": "#071828", "primaryTextColor": "#c0d4e8", "primaryBorderColor": "#00ccff", "lineColor": "#4090b8", "secondaryColor": "#060f1c", "background": "#050c18", "mainBkg": "#071828"}}}%%
flowchart TD
    classDef usr    fill:#050c18,stroke:#00ccff,color:#c0e8ff,stroke-width:2px
    classDef front  fill:#071828,stroke:#00ccff,color:#b8d8f0
    classDef eng    fill:#060f1c,stroke:#4090b8,color:#9ac0d8
    classDef qwen   fill:#071a10,stroke:#00ee88,color:#90e0a8
    classDef mem    fill:#1a1208,stroke:#ffaa00,color:#ffe8a0
    classDef out    fill:#0d0a1e,stroke:#9090ff,color:#c8c8ff
    classDef dash   fill:#071828,stroke:#00ccff,color:#b8d8f0,stroke-width:2px

    GH("📦 GitHub Repo\ngithub.com/user/aeonlogic"):::usr
    LD("🌐 Streamlit Live Demo\nyour-app.streamlit.app"):::usr

    subgraph FE["  🖥️  Streamlit Command Center  ·  streamlit_demo.py  "]
        INPUT["Mission input · Quick-task presets · Mode badge"]:::front
        QSTATUS["⚡ Qwen Cloud Status Panel\nRuntime mode · Model · API key masked"]:::front
    end

    GH & LD --> INPUT

    subgraph ENG["  🔁  AeonLogic Recursive Self-Healing Engine  ·  LangGraph  "]
        DISP["⚙️ Dispatcher\nClassify · Risk · Model tier"]:::eng
        GEN["✍️ Generator\nCandidate artifact via Qwen Cloud"]:::eng
        CRIT["🔍 Critic  /  Adversarial Auditor\nStructured Finding objects"]:::eng
        REPAIR["🔧 Repair Loop\nFindings injected back → regenerate"]:::eng
        EXEC["▶️ Executor\nRun · Validate · Block on critical"]:::eng
        SYNTH["💾 Memory Synthesizer\nWrite failure + success lessons"]:::eng

        DISP --> GEN --> CRIT
        CRIT -- "REJECTED\nfindings injected" --> REPAIR --> GEN
        CRIT -- "APPROVED" --> EXEC --> SYNTH
    end

    INPUT --> DISP

    subgraph QW["  ⚡  Qwen Cloud  ·  Alibaba Cloud Model Studio  "]
        ENVV["🔑 QWEN_API_KEY · QWEN_BASE_URL · QWEN_MODEL"]:::qwen
        QREAL["QwenClient\nDashScope OpenAI-compatible API\ndashscope-intl.aliyuncs.com"]:::qwen
        QRES["ResilientQwenClient\nauto-fallback wrapper"]:::qwen
        QMOCK["🔒 MockQwenClient\nMOCK_MODEL_MODE · no key required\ndeterministic offline fallback"]:::qwen

        ENVV --> QREAL --> QRES
        QRES -. "API error / no key" .-> QMOCK
    end

    GEN --> QREAL
    CRIT --> QREAL
    SYNTH --> QREAL
    QRES & QMOCK --> QSTATUS

    subgraph HMEM["  🧠  Hybrid Memory  ·  HybridMemoryStore  "]
        CHROMA["ChromaDB\nSemantic embeddings · Episodic memory"]:::mem
        NEO4J["Neo4j  ✦  graph-ready\nTask → Artifact → Lesson\nSafe no-op when absent"]:::mem
    end

    SYNTH --> CHROMA & NEO4J

    EXEC  --> VERDICT["✅ / ✗  Final Verdict"]:::out
    SYNTH --> ARTPREV["📄 Artifact Preview\nbuild_artifact_preview_html()"]:::out
    SYNTH --> DLREP["⬇️ Downloadable Report\nbuild_demo_summary_text()"]:::out
    CHROMA & NEO4J --> MEMEV["🧩 Memory Evidence Panel\nChroma · Neo4j · Hybrid · lesson counts"]:::out

    VERDICT & ARTPREV & DLREP & MEMEV --> DASH["📊 Streamlit Dashboard · command center\nTimeline · Critic Findings · Memory Writes · Verdict · Download"]:::dash
```

---

## Diagram Export Instructions

### Export as PNG for Devpost / screenshots

1. Open [https://mermaid.live](https://mermaid.live) in your browser
2. Delete the default content in the left editor panel
3. Open `docs/architecture-diagram.mmd` and paste its full contents into the editor
4. The diagram renders live in the right panel — verify it looks correct
5. Click **Actions** (top-right menu) → **Export PNG**
6. Save the downloaded file as:
   ```
   media/screenshots/09-architecture-diagram.png
   ```
   Create the `media/screenshots/` directory first if it does not exist:
   ```powershell
   New-Item -ItemType Directory -Force media/screenshots
   ```
7. Use this PNG in your Devpost submission image gallery

### Render locally (optional)

```powershell
# Install Mermaid CLI (one-time)
npm install -g @mermaid-js/mermaid-cli

# Export to PNG
mmdc -i docs/architecture-diagram.mmd -o media/screenshots/09-architecture-diagram.png -t dark -b "#050c18"
```

---

## Component Reference

### Streamlit Command Center
**File:** `src/aeonlogic/app/streamlit_demo.py`

Pure consumer of the AeonLogic engine — no domain logic lives in the dashboard. All display helpers (`_build_summary`, `build_artifact_preview_html`, `build_memory_evidence_html`, `build_qwen_cloud_status`) are pure functions testable without a Streamlit runtime.

Key panels:
| Panel | Helper function |
|---|---|
| Agent timeline | `_timeline_html()` |
| Qwen Cloud status | `build_qwen_cloud_status()` |
| Artifact Preview | `build_artifact_preview_html()` |
| Memory Evidence | `build_memory_evidence_html()` |
| Run telemetry | `_build_summary()` |

---

### Qwen Cloud Client
**File:** `src/aeonlogic/models/qwen_client.py`

Three-class design:

| Class | Role |
|---|---|
| `QwenClient` | Production client — OpenAI-compatible DashScope API (Alibaba Cloud) |
| `MockQwenClient` | Deterministic offline fallback — zero API calls |
| `ResilientQwenClient` | Wraps `QwenClient`, auto-falls back to `MockQwenClient` on any exception |

Runtime mode is selected by `get_or_create_client()` at startup:
- `AEONLOGIC_MODE=real` + `QWEN_API_KEY` set → `ResilientQwenClient(QwenClient(...))`
- `AEONLOGIC_MODE=auto` + key present → `ResilientQwenClient(QwenClient(...))`
- `AEONLOGIC_MODE=mock` or no key → `MockQwenClient()`

The safe mock fallback ensures no pipeline crash on transient API errors or missing credentials.

---

### ChromaDB Memory
**File:** `src/aeonlogic/memory/chroma_store.py` / `src/aeonlogic/memory/hybrid_store.py`

`HybridMemoryStore` coordinates ChromaDB (authoritative) and Neo4j (best-effort):
- ChromaDB: persistent semantic embeddings — lessons retrieved by cosine similarity
- Neo4j: structured knowledge graph of `Task → Artifact → Lesson` edges
- If ChromaDB is unavailable: `MockMemoryStore` (in-process dict) takes over
- If Neo4j is unavailable: write is silently swallowed; pipeline always completes

---

### Neo4j Graph Interface
**File:** `src/aeonlogic/memory/neo4j_store.py`

Optional dependency — the entire pipeline runs correctly with Neo4j absent. `Neo4jMemoryStore` checks `self._available` before every operation; no URI configured → `NOT CONFIGURED` (not an error).

---

## Qwen Cloud / Alibaba Cloud Integration

### Required Environment Variables

```env
# Copy .env.example → .env and fill in real values.
# The .env file is never committed to VCS — only .env.example is tracked.

AEONLOGIC_MODE=real              # real | auto | mock
QWEN_API_KEY=sk-...              # Alibaba Cloud DashScope API key (QWEN_API_KEY)
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus             # or qwen-turbo, qwen-max
```

The `QWEN_API_KEY` environment variable is **never hardcoded** in any source file. It is read exclusively from the environment at runtime via `aeonlogic.config.settings`. The `.env` file is listed in `.gitignore`; only `.env.example` (with empty key value) is committed to the repository. **No API key is committed to VCS.**

### Real Mode Code Path

```
settings.py          AEONLOGIC_MODE=real + QWEN_API_KEY
      │
      ▼
qwen_client.py       get_or_create_client()
      │                → QwenClient(api_key, base_url)
      │                → wrapped in ResilientQwenClient
      ▼
agents/generator.py  client.complete(budget, prompt)
      │                → POST https://dashscope-intl.aliyuncs.com/.../chat/completions
      ▼
agents/critic.py     client.complete(budget, adversarial_prompt)
      │
      ▼
Qwen Cloud response  parsed → candidate_artifact / critic_verdict / Finding objects
```

### Safe Mock Fallback

When `QWEN_API_KEY` is absent or `AEONLOGIC_MODE=mock`:
- `MockQwenClient` is used — returns deterministic, task-aware code strings
- No network call is made; no credentials are needed
- The full repair loop still executes: attempt 1 returns intentionally weak code, attempt 2 returns the hardened version
- The dashboard shows `● MOCK_MODEL_MODE` badge

When a real call fails at runtime:
- `ResilientQwenClient` catches the exception, calls `_set_active_mode("fallback")`
- Falls back to `MockQwenClient.complete()` for that request
- Dashboard shows `● FALLBACK_MODE` badge
- No crash; pipeline completes

---

## Deployment Targets

### Local (development)

```powershell
# Windows
$env:PYTHONPATH = "src"; $env:AEONLOGIC_MODE = "real"; $env:QWEN_API_KEY = "sk-..."
streamlit run src/aeonlogic/app/streamlit_demo.py
```

### Alibaba Cloud / Streamlit Community Cloud

AeonLogic is designed to deploy on any Python-hosting platform:
- Set `QWEN_API_KEY` as a **platform secret / environment variable** (never in source)
- Set `AEONLOGIC_MODE=real`
- Set `QWEN_BASE_URL` to the DashScope international endpoint
- `streamlit run src/aeonlogic/app/streamlit_demo.py` is the entry point

Alibaba Cloud Function Compute or ECS can host the Streamlit process. The DashScope API key is injected via the platform's secret management — never via the repository.

---

## Environment-Based Secret Handling

| Principle | Implementation |
|---|---|
| No secrets in source | `QWEN_API_KEY` read from env only; `.env` in `.gitignore` |
| Masked display | `mask_api_key()` in `qwen_client.py` — shows `sk-****...****` only |
| Key never logged | `build_qwen_cloud_status()` returns `api_key_masked`, never `api_key_raw` |
| Template committed | `.env.example` has empty `QWEN_API_KEY=` — safe to commit |
| Test isolation | All tests use `MockQwenClient`; `QWEN_API_KEY` is never needed in CI |
