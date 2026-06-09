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

    @mcp.tool(
        name="a_share_intraday_timeseries",
        description="Fetch A-share intraday minute-level time series for one known symbol.",
    )
    def a_share_intraday_timeseries(
        symbol: str | None = None,
        market: str | None = None,
        code: str | None = None,
        date: int | None = None,
        days: int = 1,
    ) -> dict[str, Any]:
        return facade.a_share_intraday_timeseries(
            symbol=symbol,
            market=market,
            code=code,
            date=date,
            days=days,
        )

    @mcp.tool(
        name="a_share_trade_ticks",
        description=(
            "Fetch A-share trade tick records for one known symbol. count defaults to 200 "
            "and maxes at 1000."
        ),
    )
    def a_share_trade_ticks(
        symbol: str | None = None,
        market: str | None = None,
        code: str | None = None,
        date: int | None = None,
        start: int = 0,
        count: int | None = 200,
    ) -> dict[str, Any]:
        return facade.a_share_trade_ticks(
            symbol=symbol,
            market=market,
            code=code,
            date=date,
            start=start,
            count=count,
        )

    @mcp.tool(
        name="a_share_sector_list",
        description="Fetch A-share sector definitions by sector type.",
    )
    def a_share_sector_list(
        sector_type: str = "all",
        count: int | None = 200,
    ) -> dict[str, Any]:
        return facade.a_share_sector_list(sector_type=sector_type, count=count)

    @mcp.tool(
        name="a_share_sector_members",
        description=(
            "Fetch realtime quote rows for members in one A-share sector. "
            "Use a known sector symbol such as 881001."
        ),
    )
    def a_share_sector_members(
        sector_symbol: str,
        count: int | None = 200,
        sort_by: str = "change_pct",
        ascending: bool = False,
    ) -> dict[str, Any]:
        return facade.a_share_sector_members(
            sector_symbol=sector_symbol,
            count=count,
            sort_by=sort_by,
            ascending=ascending,
        )

    @mcp.tool(
        name="a_share_sector_ranking",
        description=(
            "Fetch aggregated A-share sector ranking; top_n defaults to 30 and maxes at 100."
        ),
    )
    def a_share_sector_ranking(
        sector_type: str = "industry",
        top_n: int | None = 30,
        sort_by: str = "change_pct",
        ascending: bool = False,
    ) -> dict[str, Any]:
        return facade.a_share_sector_ranking(
            sector_type=sector_type,
            top_n=top_n,
            sort_by=sort_by,
            ascending=ascending,
        )

    @mcp.tool(
        name="a_share_market_events",
        description="Fetch A-share unusual market events for SH, SZ, or BJ.",
    )
    def a_share_market_events(
        market: str = "SH",
        start: int = 0,
        count: int | None = 100,
    ) -> dict[str, Any]:
        return facade.a_share_market_events(market=market, start=start, count=count)

    @mcp.tool(
        name="a_share_market_snapshot",
        description="Fetch A-share market breadth and capitalization snapshot.",
    )
    def a_share_market_snapshot() -> dict[str, Any]:
        return facade.a_share_market_snapshot()

    @mcp.tool(
        name="hk_realtime_quotes",
        description=(
            "Fetch Hong Kong realtime quotes. Bare codes default to HK_MAIN_BOARD; "
            "use market for HK_GEM, HK_INDEX, or HK_FUND."
        ),
    )
    def hk_realtime_quotes(
        symbols: list[str] | None = None,
        market: str | None = None,
        code: str | None = None,
    ) -> dict[str, Any]:
        return facade.hk_realtime_quotes(symbols=symbols, market=market, code=code)

    @mcp.tool(
        name="hk_kline_bars",
        description=(
            "Fetch Hong Kong K-line bars for one known symbol. count defaults "
            "to 200 and maxes at 1000."
        ),
    )
    def hk_kline_bars(
        symbol: str | None = None,
        market: str | None = None,
        code: str | None = None,
        period: str = "DAILY",
        count: int | None = 200,
        start: int = 0,
        adjust: str = "NONE",
    ) -> dict[str, Any]:
        return facade.hk_kline_bars(
            symbol=symbol,
            market=market,
            code=code,
            period=period,
            count=count,
            start=start,
            adjust=adjust,
        )

    @mcp.tool(
        name="hk_intraday_timeseries",
        description="Fetch Hong Kong intraday minute-level time series for one known symbol.",
    )
    def hk_intraday_timeseries(
        symbol: str | None = None,
        market: str | None = None,
        code: str | None = None,
        date: int | None = None,
    ) -> dict[str, Any]:
        return facade.hk_intraday_timeseries(
            symbol=symbol,
            market=market,
            code=code,
            date=date,
        )

    return mcp


def main() -> None:
    """Run the MCP server over stdio."""
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
