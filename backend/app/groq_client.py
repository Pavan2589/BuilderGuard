"""Thin wrapper around Groq's OpenAI-compatible chat completions endpoint.

Uses httpx directly (no groq SDK dependency). GROQ_API_KEY is read once at
Settings construction time and only ever sent as an outgoing Authorization
header; it is never included in any response this service returns.
"""
from __future__ import annotations

from typing import Any

import httpx

from .config import Settings
from .errors import AgentTimeoutError, MalformedLLMOutputError, ProviderError


class GroqClient:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        """Send one chat completion request. Returns the assistant message dict."""
        if not self._settings.groq_api_key:
            raise ProviderError("GROQ_API_KEY is not configured on the server")

        url = f"{self._settings.groq_base_url}/chat/completions"
        payload = {
            "model": self._settings.groq_model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
                resp = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise AgentTimeoutError("Groq API request timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Groq API request failed: {exc}") from exc

        if resp.status_code == 401:
            raise ProviderError("Groq API rejected the configured credentials")
        if resp.status_code == 429:
            raise ProviderError("Groq API rate limit exceeded")
        if resp.status_code >= 400:
            raise ProviderError(f"Groq API returned HTTP {resp.status_code}: {resp.text[:300]}")

        try:
            data = resp.json()
        except ValueError as exc:
            raise MalformedLLMOutputError("Groq API returned a non-JSON response") from exc

        try:
            return data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise MalformedLLMOutputError("Groq API response was missing a message") from exc
