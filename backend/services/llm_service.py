"""
LLM Service - thin wrapper over the Anthropic API (Claude) and GLM (Zhipu).

Both providers are optional and fail soft: if a key is missing or a call errors,
``complete`` returns ``None`` and callers fall back to deterministic behaviour.
This keeps the app fully functional offline while enabling live agent calls when
credentials are configured.
"""

import logging
from typing import Optional

import httpx

try:  # anthropic is installed in the backend venv; guard just in case
    import anthropic
except Exception:  # pragma: no cover
    anthropic = None  # type: ignore

from core.config import settings

logger = logging.getLogger("llm_service")

# GLM-4 (Zhipu) OpenAI-compatible chat completions endpoint.
GLM_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


class LLMService:
    """Routes a prompt to Claude or GLM based on the agent's assigned model."""

    def __init__(self) -> None:
        self._anthropic = None
        if anthropic is not None and settings.ANTHROPIC_API_KEY:
            # Short timeout + a single retry so a slow/unreachable provider can't
            # stall a request (the SDK default is a 10 minute timeout).
            self._anthropic = anthropic.AsyncAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                timeout=20.0,
                max_retries=1,
            )
        self._glm_key = settings.GLM_API_KEY if settings.ENABLE_GLM else ""

    def available(self) -> dict:
        """Report which providers are configured."""
        return {"anthropic": self._anthropic is not None, "glm": bool(self._glm_key)}

    @staticmethod
    def provider_for(model_label: str) -> str:
        """Map an agent's model label ('Claude Opus', 'GLM', …) to a provider."""
        return "glm" if model_label.upper().startswith("GLM") else "anthropic"

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        model_label: str = "Claude Opus",
        max_tokens: int = 400,
    ) -> Optional[str]:
        """Return the model's text response, or ``None`` on any failure."""
        provider = self.provider_for(model_label)
        try:
            if provider == "glm":
                return await self._glm_complete(prompt, system, max_tokens)
            return await self._anthropic_complete(prompt, system, model_label, max_tokens)
        except Exception as exc:  # fail soft — callers have deterministic fallbacks
            logger.warning("LLM call failed via %s: %s", provider, exc)
            return None

    # ------------------------------------------------------------------
    # Providers
    # ------------------------------------------------------------------
    async def _anthropic_complete(
        self, prompt: str, system: Optional[str], model_label: str, max_tokens: int
    ) -> Optional[str]:
        if self._anthropic is None:
            return None
        # 'Claude Haiku' agents use the fast model; everything else the default.
        model = (
            settings.ANTHROPIC_MODEL_FAST
            if "haiku" in model_label.lower()
            else settings.ANTHROPIC_MODEL_DEFAULT
        )
        # NOTE: do not pass temperature/top_p/budget_tokens — Opus 4.8 / Haiku 4.5
        # reject those parameters.
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        resp = await self._anthropic.messages.create(**kwargs)
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        return text or None

    async def _glm_complete(
        self, prompt: str, system: Optional[str], max_tokens: int
    ) -> Optional[str]:
        if not self._glm_key:
            return None
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": settings.GLM_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._glm_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(GLM_ENDPOINT, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            text = (data["choices"][0]["message"]["content"] or "").strip()
            return text or None
