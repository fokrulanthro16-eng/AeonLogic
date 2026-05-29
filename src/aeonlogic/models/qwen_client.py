from __future__ import annotations

from typing import Protocol, runtime_checkable

from aeonlogic.models.budgets import ModelBudget


# ── Client protocol ───────────────────────────────────────────────────────────

@runtime_checkable
class ModelClientProtocol(Protocol):
    """Structural protocol satisfied by every model client implementation."""

    def complete(self, budget: ModelBudget, prompt: str) -> str:
        """Send a completion request; return the response text."""
        ...


# ── Mock client (deterministic, no API key required) ─────────────────────────

_WEAK_AUTH_CODE = """\
# auth.py - API authentication module (initial draft)
import jwt

SECRET_KEY = "dev-secret-2024"

def login(username, password):
    if username == "admin" and password == "admin123":
        token = jwt.encode({"user": username, "role": "admin"}, SECRET_KEY)
        return token
    return None

def validate_token(token):
    data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return data["user"]
"""

_SECURE_AUTH_CODE = """\
# auth.py - Security-hardened API authentication module
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY: str = os.environ["JWT_SECRET_KEY"]
TOKEN_TTL_HOURS: int = int(os.environ.get("TOKEN_TTL_HOURS", "1"))
MAX_FIELD_LEN: int = 128
_rate_tracker: dict[str, int] = {}
RATE_LIMIT: int = 5

def login(username: str, password: str, ip: str = "") -> Optional[str]:
    if not isinstance(username, str) or not isinstance(password, str):
        raise TypeError("username and password must be str")
    if len(username) > MAX_FIELD_LEN or len(password) > MAX_FIELD_LEN:
        raise ValueError("input exceeds maximum allowed length")
    if _rate_tracker.get(ip, 0) >= RATE_LIMIT:
        raise PermissionError("Rate limit exceeded. Try again later.")
    if not _check_credentials(username, password):
        _rate_tracker[ip] = _rate_tracker.get(ip, 0) + 1
        return None
    expiry = datetime.utcnow() + timedelta(hours=TOKEN_TTL_HOURS)
    return jwt.encode(
        {"sub": username, "exp": expiry, "iat": datetime.utcnow()},
        SECRET_KEY,
        algorithm="HS256",
    )

def validate_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return str(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc

def _check_credentials(username: str, password: str) -> bool:
    from myapp.credential_store import verify_password
    return verify_password(username, password)
"""


class MockQwenClient:
    """Deterministic mock — no API key required. Returns task-aware content."""

    def complete(self, budget: ModelBudget, prompt: str) -> str:
        p = prompt.lower()
        is_auth   = any(kw in p for kw in ("auth", "authentication", "login", "token", "credential"))
        is_repair = "findings to address" in p

        if is_auth and is_repair:
            return _SECURE_AUTH_CODE
        if is_auth:
            return _WEAK_AUTH_CODE
        if "decompose" in p or "classify" in p:
            return f"[{budget.model_name}] Task decomposed and risk classified."
        if "synthesize" in p or "learnings" in p:
            return f"[{budget.model_name}] Memory synthesized: pattern stored for future reference."
        return f"[{budget.model_name}] Processed: {prompt[:60]}..."


# ── Real Qwen client (OpenAI-compatible DashScope API) ────────────────────────

class QwenClient:
    """
    Production client for Qwen models via the DashScope OpenAI-compatible API.
    Requires QWEN_API_KEY to be configured. Instantiate only when is_real_qwen_mode=True.
    """

    def __init__(self, api_key: str, base_url: str) -> None:
        # Deferred import: openai is only imported when a real client is needed.
        from openai import OpenAI  # noqa: PLC0415

        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def complete(self, budget: ModelBudget, prompt: str) -> str:
        from aeonlogic.config.settings import get_settings  # avoid circular at import time
        settings = get_settings()
        model = settings.qwen_model.strip() or budget.model_name
        try:
            resp = self._client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=budget.max_tokens,
                temperature=budget.temperature,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            raise RuntimeError(
                f"Qwen API error (model={model}): {exc}"
            ) from exc


# ── Resilient wrapper — auto-fallback to mock on any exception ────────────────

class ResilientQwenClient:
    """
    Wraps a QwenClient and falls back to MockQwenClient on any exception.

    This ensures the pipeline never crashes due to a transient API failure or
    a misconfigured REAL mode. The module-level ``_active_mode`` is updated to
    ``"fallback"`` whenever a real call fails.
    """

    def __init__(self, real: QwenClient) -> None:
        self._real = real

    def complete(self, budget: ModelBudget, prompt: str) -> str:
        try:
            return self._real.complete(budget, prompt)
        except Exception:
            _set_active_mode("fallback")
            return _mock_client.complete(budget, prompt)


# ── Active mode tracking ──────────────────────────────────────────────────────
# Reflects what actually happened at runtime (may differ from config when
# AEONLOGIC_MODE=real but a call fails and falls back).

_active_mode: str = "mock"  # "mock" | "real" | "fallback"


def _set_active_mode(mode: str) -> None:
    global _active_mode
    _active_mode = mode


def get_client_mode_label() -> str:
    """Return the actual runtime mode label after the last get_client() call.

    Returns one of: REAL_MODEL_MODE | MOCK_MODEL_MODE | FALLBACK_MODE.
    Use this (rather than settings.client_mode_label) in UI code that should
    reflect what actually happened at runtime.
    """
    if _active_mode == "real":
        return "REAL_MODEL_MODE"
    if _active_mode == "fallback":
        return "FALLBACK_MODE"
    return "MOCK_MODEL_MODE"


# ── Factory ───────────────────────────────────────────────────────────────────

_mock_client = MockQwenClient()


def get_client() -> ModelClientProtocol:
    """
    Return the appropriate client for the current runtime configuration.

    Decision table:
    ┌──────────────────┬───────────────┬──────────────────────┬────────────────┐
    │  aeonlogic_mode  │  qwen_api_key │  result              │  _active_mode  │
    ├──────────────────┼───────────────┼──────────────────────┼────────────────┤
    │  mock            │  any          │  MockQwenClient      │  mock          │
    │  auto / real     │  absent       │  MockQwenClient      │  mock/fallback │
    │  auto / real     │  present      │  ResilientQwenClient │  real          │
    │  auto / real     │  present      │  MockQwenClient*     │  fallback      │
    └──────────────────┴───────────────┴──────────────────────┴────────────────┘
    * When openai package is missing or QwenClient init fails.
    """
    from aeonlogic.config.settings import get_settings

    settings = get_settings()
    mode = settings.aeonlogic_mode.strip().lower()

    if mode == "mock":
        _set_active_mode("mock")
        return _mock_client

    # auto or real: use real client if key is present
    if not settings.qwen_api_key.strip():
        # real explicitly requested but key absent → fallback indicator
        _set_active_mode("fallback" if mode == "real" else "mock")
        return _mock_client

    try:
        real = QwenClient(
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_base_url,
        )
        _set_active_mode("real")
        return ResilientQwenClient(real)
    except Exception:
        _set_active_mode("fallback")
        return _mock_client
