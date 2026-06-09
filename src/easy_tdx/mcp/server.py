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

    @mcp.tool(
        name="a_share_realtime_quotes",
        description=(
            "Fetch A-share realtime quotes. Use symbols like SH600519 or SZ000001; "
            "bare 6-digit codes are rejected as ambiguous."
        ),
    )
    def a_share_realtime_quotes(
        symbols: list[str] | None = None,
        market: str | None = None,
        code: str | None = None,
    ) -> dict[str, Any]:
        return facade.a_share_realtime_quotes(symbols=symbols, market=market, code=code)

    @mcp.tool(
        name="a_share_kline_bars",
        description=(
            "Fetch A-share K-line bars for one known symbol. Use symbol like SH600519 "
            "or provide market/code. count defaults to 200 and maxes at 1000."
        ),
    )
    def a_share_kline_bars(
        symbol: str | None = None,
        market: str | None = None,
        code: str | None = None,
        period: str = "DAILY",
        count: int | None = 200,
        start: int = 0,
        adjust: str = "NONE",
    ) -> dict[str, Any]:
        return facade.a_share_kline_bars(
            symbol=symbol,
            market=market,
            code=code,
            period=period,
            count=count,
            start=start,
            adjust=adjust,
        )

    return mcp


def main() -> None:
    """Run the MCP server over stdio."""
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
