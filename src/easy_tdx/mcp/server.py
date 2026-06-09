"""FastMCP stdio server for easy-tdx."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from . import facade


def create_server() -> FastMCP:
    """Create the FastMCP server and register tools."""
    mcp = FastMCP("easy-tdx")

    @mcp.tool(
        name="service_health",
        description="Return easy-tdx MCP server health and version metadata without network IO.",
    )
    def service_health() -> dict[str, Any]:
        return facade.service_health()

    return mcp


def main() -> None:
    """Run the MCP server over stdio."""
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
