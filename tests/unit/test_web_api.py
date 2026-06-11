"""Web API schemas and error handling tests (offline, no network)."""

from __future__ import annotations

import pytest


def test_market_enum_values():
    """MarketEnum should map string names to int values matching Market enum."""
    pytest.importorskip("fastapi")
    from easy_tdx.web.schemas import MarketEnum

    assert MarketEnum.SZ == 0
    assert MarketEnum.SH == 1
    assert MarketEnum.BJ == 2


def test_kline_category_enum():
    """KlineCategoryEnum should map string names to int values."""
    pytest.importorskip("fastapi")
    from easy_tdx.web.schemas import KlineCategoryEnum

    assert KlineCategoryEnum.MIN_5 == 0
    assert KlineCategoryEnum.DAY == 4
    assert KlineCategoryEnum.WEEK == 5


def test_quote_request_validation():
    """QuoteRequest should validate stocks list."""
    pytest.importorskip("fastapi")
    from easy_tdx.web.schemas import QuoteRequest

    req = QuoteRequest(stocks=[{"market": "SZ", "code": "000001"}])
    assert len(req.stocks) == 1
    assert req.stocks[0].market == "SZ"
    assert req.stocks[0].code == "000001"


def test_chanlun_request_defaults():
    """ChanlunRequest should have sensible defaults."""
    pytest.importorskip("fastapi")
    from easy_tdx.web.schemas import ChanlunRequest

    req = ChanlunRequest(market="SZ", code="000001")
    assert req.category == "DAY"
    assert req.count == 800


def test_api_error_response():
    """ApiErrorResponse should serialize correctly."""
    pytest.importorskip("fastapi")
    from easy_tdx.web.errors import ApiErrorResponse

    err = ApiErrorResponse(error="test error", detail="some detail")
    d = err.model_dump()
    assert d["error"] == "test error"
    assert d["detail"] == "some detail"
