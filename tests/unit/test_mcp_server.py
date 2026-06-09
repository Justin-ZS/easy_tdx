from __future__ import annotations

import asyncio

import pandas as pd  # type: ignore[import-untyped]
from fastmcp import Client

from easy_tdx.mcp import facade
from easy_tdx.mcp.facade import service_health
from easy_tdx.mcp.server import create_server
from easy_tdx.models.enums import Market


class FakeMacClient:
    def __init__(self) -> None:
        self.stocks: list[tuple[int, str]] | None = None

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


def test_service_health_tool_registered() -> None:
    async def run() -> None:
        server = create_server()
        async with Client(server) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools}

            assert {"service_health", "a_share_realtime_quotes"}.issubset(names)

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
