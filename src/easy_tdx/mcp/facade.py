"""Business facade for MCP tools.

FastMCP registration stays thin; parsing, conversion, limits, and client
selection live here so they can be tested without starting an MCP transport.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any

from easy_tdx import __version__ as module_version

_PACKAGE_NAME = "easy-tdx"


def _package_version() -> str:
    try:
        return version(_PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"


def envelope(
    *,
    source: str,
    query: dict[str, Any] | None = None,
    rows: list[dict[str, Any]] | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create the common MCP response envelope."""
    count = len(rows) if rows is not None else (1 if data is not None else 0)
    result: dict[str, Any] = {
        "ok": True,
        "source": source,
        "query": query or {},
        "count": count,
    }
    if rows is not None:
        result["rows"] = rows
    if data is not None:
        result["data"] = data
    return result


def service_health() -> dict[str, Any]:
    """Return a non-network health payload for the MCP server."""
    return envelope(
        source="easy_tdx",
        data={
            "package": _PACKAGE_NAME,
            "package_version": _package_version(),
            "module_version": module_version,
            "transport": "stdio",
            "clients": [
                "MacClient",
                "MacExClient",
                "TdxClient",
                "UnifiedTdxClient",
            ],
        },
    )
