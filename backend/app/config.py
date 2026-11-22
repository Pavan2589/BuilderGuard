"""Server configuration sourced from environment variables.

Credentials (GROQ_API_KEY, GITHUB_TOKEN) never leave this process: they are
read here and attached to outgoing request headers only, never echoed back
in any API response.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    groq_api_key: str | None
    groq_model: str
    github_token: str | None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    github_api_base: str = "https://api.github.com"
    request_timeout_seconds: float = 20.0
    max_agent_iterations: int = 8
    max_diff_bytes: int = 20_000
    max_files_considered: int = 25


def get_settings() -> Settings:
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY") or None,
        groq_model=os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b",
        github_token=os.getenv("GITHUB_TOKEN") or None,
    )
