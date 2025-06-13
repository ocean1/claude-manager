"""Data models for Claude Manager."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Project:
    """Represents a Claude Code project."""

    path: str
    allowed_tools: list[str] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    mcp_servers: dict[str, Any] = field(default_factory=dict)
    enabled_mcpjson_servers: list[str] = field(default_factory=list)
    disabled_mcpjson_servers: list[str] = field(default_factory=list)
    enable_all_project_mcp_servers: bool = False
    has_trust_dialog_accepted: bool = False
    ignore_patterns: list[str] = field(default_factory=list)
    project_onboarding_seen_count: int = 0
    has_claude_md_external_includes_approved: bool = False
    has_claude_md_external_includes_warning_shown: bool = False
    dont_crawl_directory: bool = False
    mcp_context_uris: list[str] = field(default_factory=list)

    @property
    def history_count(self) -> int:
        """Get the number of history entries."""
        return len(self.history)

    @property
    def last_accessed(self) -> str | None:
        """Returns the last accessed command/display from history."""
        if self.history:
            return str(self.history[-1].get("display", "N/A"))
        return None

    @property
    def directory_exists(self) -> bool:
        """Check if the project directory still exists."""
        return Path(self.path).exists()

    def get_size_estimate(self) -> int:
        """Estimate the size of project data in bytes."""
        return len(json.dumps(self.to_dict()))

    def to_dict(self) -> dict[str, Any]:
        """Convert project to dictionary format for JSON serialization."""
        return {
            "allowedTools": self.allowed_tools,
            "history": self.history,
            "mcpServers": self.mcp_servers,
            "enabledMcpjsonServers": self.enabled_mcpjson_servers,
            "disabledMcpjsonServers": self.disabled_mcpjson_servers,
            "enableAllProjectMcpServers": self.enable_all_project_mcp_servers,
            "hasTrustDialogAccepted": self.has_trust_dialog_accepted,
            "ignorePatterns": self.ignore_patterns,
            "projectOnboardingSeenCount": self.project_onboarding_seen_count,
            "hasClaudeMdExternalIncludesApproved": self.has_claude_md_external_includes_approved,
            "hasClaudeMdExternalIncludesWarningShown": self.has_claude_md_external_includes_warning_shown,
            "dontCrawlDirectory": self.dont_crawl_directory,
            "mcpContextUris": self.mcp_context_uris,
        }

    @classmethod
    def from_dict(cls, path: str, data: dict[str, Any]) -> Project:
        """Create a Project instance from dictionary data."""
        return cls(
            path=path,
            allowed_tools=data.get("allowedTools", []),
            history=data.get("history", []),
            mcp_servers=data.get("mcpServers", {}),
            enabled_mcpjson_servers=data.get("enabledMcpjsonServers", []),
            disabled_mcpjson_servers=data.get("disabledMcpjsonServers", []),
            enable_all_project_mcp_servers=data.get("enableAllProjectMcpServers", False),
            has_trust_dialog_accepted=data.get("hasTrustDialogAccepted", False),
            ignore_patterns=data.get("ignorePatterns", []),
            project_onboarding_seen_count=data.get("projectOnboardingSeenCount", 0),
            has_claude_md_external_includes_approved=data.get(
                "hasClaudeMdExternalIncludesApproved", False
            ),
            has_claude_md_external_includes_warning_shown=data.get(
                "hasClaudeMdExternalIncludesWarningShown", False
            ),
            dont_crawl_directory=data.get("dontCrawlDirectory", False),
            mcp_context_uris=data.get("mcpContextUris", []),
        )
