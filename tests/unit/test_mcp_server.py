from __future__ import annotations

import asyncio

import pandas as pd  # type: ignore[import-untyped]
from fastmcp import Client

from easy_tdx.mac.enums import Adjust, Period
from easy_tdx.mcp import facade
from easy_tdx.mcp.facade import service_health
from easy_tdx.mcp.server import create_server
from easy_tdx.models.enums import Market


class FakeMacClient:
    def __init__(self) -> None:
        self.stocks: list[tuple[int, str]] | None = None
        self.tick_args: dict[str, object] | None = None
        self.trade_args: dict[str, object] | None = None

    def __enter__(self) -> FakeMacClient:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get_stock_quotes(
        self,
        stocks: list[tuple[int, str]],
        fields: object = None,
    ) -> pd.DataFrame:
        self.stocks = stocks
        return pd.DataFrame(
            [
                {
                    "market": int(market),
                    "code": code,
                    "name": "sample",
                    "price": 12.3,
                    "datetime": pd.Timestamp("2026-06-09 10:00:00"),
                    "missing": float("nan"),
                }
                for market, code in stocks
            ]
        )

    def get_stock_kline(
        self,
        market: int,
        code: str,
        period: Period = Period.DAILY,
        start: int = 0,
        count: int = 800,
        times: int = 1,
        adjust: Adjust = Adjust.NONE,
    ) -> pd.DataFrame:
        self.kline_args = {
            "market": market,
            "code": code,
            "period": period,
            "start": start,
            "count": count,
            "times": times,
            "adjust": adjust,
        }
        return pd.DataFrame(
            [
                {
                    "datetime": pd.Timestamp("2026-06-09 10:00:00"),
                    "open": 10.0,
                    "close": 10.5,
                    "high": 10.8,
                    "low": 9.9,
                    "vol": 1000,
                }
            ]
        )

    def get_tick_chart(
        self,
        market: int,
        code: str,
        date: int | None = None,
    ) -> pd.DataFrame:
        self.tick_args = {"market": market, "code": code, "date": date, "days": 1}
        return pd.DataFrame(
            [
                {
                    "datetime": pd.Timestamp("2026-06-09 10:01:00"),
                    "price": 10.1,
                    "vol": 100,
                }
            ]
        )

    def get_tick_charts(
        self,
        market: int,
        code: str,
        date: int | None = None,
        days: int = 5,
    ) -> pd.DataFrame:
        self.tick_args = {"market": market, "code": code, "date": date, "days": days}
        return pd.DataFrame(
            [
                {
                    "datetime": pd.Timestamp("2026-06-09 10:01:00"),
                    "price": 10.1,
                    "vol": 100,
                }
            ]
        )

    def get_transactions(
        self,
        market: int,
        code: str,
        count: int = 2000,
        start: int = 0,
        date: int | None = None,
    ) -> pd.DataFrame:
        self.trade_args = {
            "market": market,
            "code": code,
            "count": count,
            "start": start,
            "date": date,
        }
        return pd.DataFrame(
            [
                {
                    "datetime": pd.Timestamp("2026-06-09 10:02:00"),
                    "price": 10.2,
                    "vol": 200,
                    "buyorsell": 0,
                }
            ]
        )


def test_service_health_facade() -> None:
    result = service_health()

    assert result["ok"] is True
    assert result["source"] == "easy_tdx"
    assert result["count"] == 1
    assert result["data"]["package"] == "easy-tdx"
    assert result["data"]["transport"] == "stdio"
    assert "MacClient" in result["data"]["clients"]


def test_a_share_realtime_quotes_facade() -> None:
    fake = FakeMacClient()
    result = facade.a_share_realtime_quotes(
        symbols=["SH600519", "SZ 000001"],
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert result["count"] == 2
    assert fake.stocks == [(int(Market.SH), "600519"), (int(Market.SZ), "000001")]
    assert result["rows"][0]["datetime"] == "2026-06-09T10:00:00"
    assert result["rows"][0]["missing"] is None


def test_a_share_realtime_quotes_rejects_bare_code() -> None:
    result = facade.a_share_realtime_quotes(symbols=["600519"])

    assert result["ok"] is False
    assert result["error"]["code"] == "SYMBOL_AMBIGUOUS"


def test_a_share_realtime_quotes_enforces_symbol_limit() -> None:
    result = facade.a_share_realtime_quotes(symbols=["SH600519"] * 81)

    assert result["ok"] is False
    assert result["error"]["code"] == "LIMIT_EXCEEDED"


def test_a_share_kline_bars_facade() -> None:
    fake = FakeMacClient()
    result = facade.a_share_kline_bars(
        symbol="SH600519",
        period="5MIN",
        count=20,
        adjust="QFQ",
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert result["count"] == 1
    assert fake.kline_args["market"] == int(Market.SH)
    assert fake.kline_args["code"] == "600519"
    assert fake.kline_args["period"] == Period.MIN_5
    assert fake.kline_args["count"] == 20
    assert fake.kline_args["adjust"] == Adjust.QFQ
    assert result["rows"][0]["datetime"] == "2026-06-09T10:00:00"


def test_a_share_kline_bars_enforces_limit() -> None:
    result = facade.a_share_kline_bars(symbol="SH600519", count=1001)

    assert result["ok"] is False
    assert result["error"]["code"] == "LIMIT_EXCEEDED"


def test_a_share_kline_bars_rejects_unknown_period() -> None:
    result = facade.a_share_kline_bars(symbol="SH600519", period="2HOUR")

    assert result["ok"] is False
    assert result["error"]["code"] == "INVALID_PERIOD"


def test_a_share_intraday_timeseries_facade() -> None:
    fake = FakeMacClient()
    result = facade.a_share_intraday_timeseries(
        symbol="SZ000001",
        days=3,
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.tick_args == {
        "market": int(Market.SZ),
        "code": "000001",
        "date": None,
        "days": 3,
    }
    assert result["rows"][0]["datetime"] == "2026-06-09T10:01:00"


def test_a_share_intraday_timeseries_rejects_days_over_limit() -> None:
    result = facade.a_share_intraday_timeseries(symbol="SH600519", days=6)

    assert result["ok"] is False
    assert result["error"]["code"] == "INVALID_LIMIT"


def test_a_share_trade_ticks_facade() -> None:
    fake = FakeMacClient()
    result = facade.a_share_trade_ticks(
        symbol="SH600519",
        count=50,
        start=10,
        date=20260609,
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.trade_args == {
        "market": int(Market.SH),
        "code": "600519",
        "count": 50,
        "start": 10,
        "date": 20260609,
    }


def test_service_health_tool_registered() -> None:
    async def run() -> None:
        server = create_server()
        async with Client(server) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools}

            assert {
                "service_health",
                "a_share_realtime_quotes",
                "a_share_kline_bars",
                "a_share_intraday_timeseries",
                "a_share_trade_ticks",
            }.issubset(names)

    asyncio.run(run())


def test_service_health_tool_call() -> None:
    async def run() -> None:
        server = create_server()
        async with Client(server) as client:
            result = await client.call_tool("service_health")

        payload = result.structured_content
        assert payload is not None
        assert payload["ok"] is True
        assert payload["data"]["transport"] == "stdio"

    asyncio.run(run())
