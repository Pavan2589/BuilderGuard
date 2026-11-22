"""Tool schemas offered to the LLM, and the server-side permission allowlist.

The allowlist is enforced in agent.py: a tool_call name is only ever
dispatched if it appears in ALLOWED_TOOL_NAMES, regardless of what the model
asks for. All non-terminal tools are strictly read-only GitHub lookups.
"""
from __future__ import annotations

TOOL_SPECS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_pull_request",
            "description": (
                "Fetch pull request metadata: title, description, author, "
                "base/head branches, and change counts."
            ),
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_changed_files",
            "description": (
                "List files changed in the pull request, with status, "
                "+/- line counts, and a unified diff patch per file."
            ),
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_content",
            "description": (
                "Fetch the full content of one file at the PR's head commit, "
                "for context beyond what a diff hunk shows. Use sparingly."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Repo-relative file path"}
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_findings",
            "description": (
                "Submit the final structured code review. Call this exactly "
                "once, only after you have inspected the PR, to end the review."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "findings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "severity": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high", "critical"],
                                },
                                "file": {"type": "string"},
                                "line": {"type": "integer"},
                                "title": {"type": "string"},
                                "explanation": {"type": "string"},
                                "evidence": {"type": "string"},
                                "suggestion": {"type": "string"},
                            },
                            "required": ["severity", "title", "explanation"],
                            "additionalProperties": False,
                        },
                    },
                    "limitations": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["summary", "findings"],
                "additionalProperties": False,
            },
        },
    },
]

READ_ONLY_TOOL_NAMES = frozenset({"get_pull_request", "list_changed_files", "get_file_content"})
TERMINAL_TOOL_NAME = "submit_findings"
ALLOWED_TOOL_NAMES = READ_ONLY_TOOL_NAMES | {TERMINAL_TOOL_NAME}
