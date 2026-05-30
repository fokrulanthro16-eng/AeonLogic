# AeonLogic — Alibaba Cloud / Qwen Cloud Proof

> This document provides verifiable proof that AeonLogic integrates with Qwen Cloud (Alibaba Cloud DashScope) for real inference, with a safe mock fallback for offline demos.

See also: [ARCHITECTURE.md](ARCHITECTURE.md) for the full architecture diagram and component reference.

---

## Proof Summary

| Claim | Evidence |
|---|---|
| Uses Qwen Cloud / Alibaba Cloud API | `src/aeonlogic/models/qwen_client.py` — `QwenClient` posts to DashScope endpoint |
| QWEN_API_KEY handled via environment | `.env.example` line `QWEN_API_KEY=` — empty; never hardcoded |
| No API key is committed to VCS | `.env` is in `.gitignore`; only `.env.example` (empty) is tracked |
| Safe mock fallback works without key | `MockQwenClient` in `qwen_client.py` — deterministic, zero network calls |
| Dashboard shows Qwen Cloud status | `src/aeonlogic/app/streamlit_demo.py` — `build_qwen_cloud_status()` panel |
| Key is never displayed in UI | `mask_api_key()` in `qwen_client.py` — shows `sk-****...****` only |

---

## Real Mode: How It Works

### Step 1 — Configure credentials

Copy `.env.example` to `.env` (never commit `.env`):

```env
AEONLOGIC_MODE=real
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

`QWEN_API_KEY` is the Alibaba Cloud DashScope API key. It is read **only from the environment** — never hardcoded anywhere in the source tree.

### Step 2 — How the client is selected

**File:** `src/aeonlogic/models/qwen_client.py`

```python
# Simplified logic from get_or_create_client()
if settings.is_real_qwen_mode and settings.qwen_api_key:
    real = QwenClient(api_key=settings.qwen_api_key, base_url=settings.qwen_base_url)
    _client = ResilientQwenClient(real)   # auto-fallback on error
    _active_mode = "real"
else:
    _client = MockQwenClient()            # safe mock fallback
    _active_mode = "mock"
```

`QwenClient.complete()` calls the Alibaba Cloud DashScope endpoint using the `openai`-compatible SDK:

```python
# From src/aeonlogic/models/qwen_client.py — QwenClient.complete()
resp = self._client.chat.completions.create(
    model=model,                          # e.g. "qwen-plus"
    messages=[{"role": "user", "content": prompt}],
    max_tokens=budget.max_tokens,
    temperature=budget.temperature,
)
```

### Step 3 — Dashboard proof

**File:** `src/aeonlogic/app/streamlit_demo.py`

The Streamlit Command Center sidebar shows the Qwen Cloud status panel at all times. `build_qwen_cloud_status()` returns:

```python
{
    "runtime_mode":     "REAL_MODEL_MODE",        # or MOCK/FALLBACK
    "configured_model": "qwen-plus",
    "base_url_configured": True,
    "api_key_present":  True,
    "api_key_masked":   "sk-****...****",         # raw key NEVER returned
    "activation_note":  "...",
}
```

The raw API key value is **never included** in any return value, log, or UI element.

---

## Safe Mock Fallback

When `QWEN_API_KEY` is absent or `AEONLOGIC_MODE=mock`:

- `MockQwenClient` is instantiated — **no network call, no credentials needed**
- Returns deterministic task-aware code: weak auth on attempt 1, hardened auth on attempt 2
- The full self-healing repair loop executes identically to real mode
- The dashboard shows `● MOCK_MODEL_MODE` badge
- **All 457+ tests use mock mode** — no Qwen API key is needed in CI

When a live Qwen Cloud call fails mid-run:

- `ResilientQwenClient` catches the exception
- Silently falls back to `MockQwenClient.complete()` for that request
- Updates `_active_mode` to `"fallback"` — dashboard shows `● FALLBACK_MODE`
- Pipeline always completes — the safe mock fallback ensures zero crashes

---

## No API Key Is Committed

Verification checklist:

- [x] `QWEN_API_KEY` appears in `.env.example` with **empty value** (`QWEN_API_KEY=`)
- [x] `.env` (with real key) is listed in `.gitignore` — never tracked
- [x] No `QWEN_API_KEY` value appears in any `.py`, `.md`, `.toml`, or `.yaml` file
- [x] `mask_api_key()` in `qwen_client.py` is the only function that handles key display
- [x] `build_qwen_cloud_status()` in `streamlit_demo.py` returns `api_key_masked` only
- [x] CI runs with `MOCK_MODEL_MODE` — no key injection needed

---

## Environment Variables Reference

| Variable | Required for real mode | Description |
|---|---|---|
| `QWEN_API_KEY` | Yes | Alibaba Cloud DashScope API key |
| `QWEN_BASE_URL` | Recommended | DashScope international endpoint |
| `AEONLOGIC_MODE` | Recommended | `real` / `auto` / `mock` |
| `QWEN_MODEL` | Optional | Model override (e.g. `qwen-plus`, `qwen-max`) |
| `QWEN_FAST_MODEL` | Optional | Fast model for low-risk tasks (default: `qwen-turbo`) |
| `QWEN_DEEP_MODEL` | Optional | Strong model for high-risk tasks (default: `qwen-plus`) |

Full template: see `.env.example` in the repository root.

---

## Deployment Proof Checklist

Complete this checklist before submitting to Devpost:

- [ ] **Live demo URL**: `_______________________` *(Streamlit Community Cloud / Alibaba Cloud ECS)*
- [ ] **Demo video URL**: `_______________________` *(YouTube / Loom recording showing real Qwen Cloud run)*
- [ ] **GitHub repo URL**: `_______________________` *(public repo with `.env.example` visible)*
- [ ] **Qwen API-ready code path**: `src/aeonlogic/models/qwen_client.py` — `QwenClient.complete()`
- [ ] **Dashboard source path**: `src/aeonlogic/app/streamlit_demo.py` — `build_qwen_cloud_status()`
- [ ] **Environment template**: `.env.example` — `QWEN_API_KEY=` empty, safe to commit
- [ ] **Architecture diagram**: `docs/ARCHITECTURE.md` — Mermaid diagram with Alibaba Cloud endpoint shown
- [ ] **No secrets committed**: verify `git log --all --full-history -- '*.env'` shows no `.env` with key

---

## Code File Index

| File | Role |
|---|---|
| `src/aeonlogic/models/qwen_client.py` | Qwen Cloud / Alibaba Cloud client — `QwenClient`, `MockQwenClient`, `ResilientQwenClient`, `mask_api_key()` |
| `src/aeonlogic/app/streamlit_demo.py` | Streamlit Command Center — `build_qwen_cloud_status()`, Qwen Cloud status panel |
| `src/aeonlogic/config/settings.py` | `get_settings()` — reads `QWEN_API_KEY` and `AEONLOGIC_MODE` from environment |
| `.env.example` | Environment template — `QWEN_API_KEY=` empty, safe to commit |
| `docs/ARCHITECTURE.md` | Full architecture diagram (Mermaid) and component reference |
