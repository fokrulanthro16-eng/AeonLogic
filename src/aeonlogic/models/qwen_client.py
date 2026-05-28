from __future__ import annotations

from aeonlogic.models.budgets import ModelBudget

# ── Mock content: attempt 1 — intentional security weaknesses ─────────────────
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

# ── Mock content: attempt 2 — security-hardened after critique ────────────────
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
    """Deterministic mock — no real API calls. Returns task-aware content."""

    def complete(self, budget: ModelBudget, prompt: str) -> str:
        p = prompt.lower()

        # Auth / security task responses
        is_auth = any(kw in p for kw in ("auth", "authentication", "login", "token", "credential"))
        is_repair = "findings to address" in p

        if is_auth and is_repair:
            return _SECURE_AUTH_CODE
        if is_auth:
            return _WEAK_AUTH_CODE

        # Generic fallback responses
        if "decompose" in p or "classify" in p:
            return f"[{budget.model_name}] Task decomposed and risk classified."
        if "synthesize" in p or "learnings" in p:
            return f"[{budget.model_name}] Memory synthesized: pattern stored for future reference."
        return f"[{budget.model_name}] Processed: {prompt[:60]}..."


_client = MockQwenClient()


def get_client() -> MockQwenClient:
    return _client
