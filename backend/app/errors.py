"""Domain exceptions for the review pipeline.

Deliberately free of any FastAPI import: this module (and the agent that
raises these exceptions) must stay usable outside an HTTP context, e.g. when
the Security Lab imports the agent function directly with its own adapter.
"""
from __future__ import annotations


class BuilderGuardError(Exception):
    status_code = 500


class InvalidPRUrlError(BuilderGuardError):
    status_code = 400


class PRNotFoundError(BuilderGuardError):
    status_code = 404


class GitHubAPIError(BuilderGuardError):
    status_code = 502


class DiffTooLargeError(BuilderGuardError):
    status_code = 413


class ProviderError(BuilderGuardError):
    status_code = 502


class AgentTimeoutError(BuilderGuardError):
    status_code = 504


class MalformedLLMOutputError(BuilderGuardError):
    status_code = 502
