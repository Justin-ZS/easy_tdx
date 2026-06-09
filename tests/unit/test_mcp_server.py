from __future__ import annotations

import asyncio

from fastmcp import Client

from easy_tdx.mcp.facade import service_health
from easy_tdx.mcp.server import create_server


def test_service_health_facade() -> None:
    result = service_health()

    assert result["ok"] is True
    assert result["source"] == "easy_tdx"
    assert result["count"] == 1
    assert result["data"]["package"] == "easy-tdx"
    assert result["data"]["transport"] == "stdio"
    assert "MacClient" in result["data"]["clients"]


def test_service_health_tool_registered() -> None:
    async def run() -> None:
        server = create_server()
        async with Client(server) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools}

            assert "service_health" in names

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
