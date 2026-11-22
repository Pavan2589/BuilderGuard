"""Working state for a single review run: tool activity log + limitations."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


@dataclass
class ToolActivity:
    tool: str
    status: str  # "success" | "error"
    detail: str | None = None
    at: float = field(default_factory=time.monotonic)


@dataclass
class ReviewSession:
    pr_url: str = ""
    id: str = field(default_factory=lambda: f"review-{uuid.uuid4().hex[:12]}")
    status: str = "running"
    tool_activity: list[ToolActivity] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def record_tool_call(self, tool: str, status: str, detail: str | None = None) -> None:
        self.tool_activity.append(ToolActivity(tool=tool, status=status, detail=detail))

    def add_limitation(self, message: str) -> None:
        if message not in self.limitations:
            self.limitations.append(message)
