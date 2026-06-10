from __future__ import annotations

import asyncio
from datetime import date

import pandas as pd  # type: ignore[import-untyped]
from fastmcp import Client

from easy_tdx.exceptions import TdxError
from easy_tdx.mac.enums import Adjust, BoardType, ExMarket, Period, SortOrder, SortType
from easy_tdx.mcp import facade
from easy_tdx.mcp.facade import service_health
from easy_tdx.mcp.server import create_server
from easy_tdx.models.enums import Market


class FakeMacClient:
    def __init__(self) -> None:
        self.stocks: list[tuple[int, str]] | None = None
        self.kline_args: dict[str, object] | None = None
        self.tick_args: dict[str, object] | None = None
        self.trade_args: dict[str, object] | None = None
        self.board_args: dict[str, object] | None = None

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

    def get_board_list(
        self,
        board_type: BoardType = BoardType.ALL,
        count: int = 10000,
    ) -> pd.DataFrame:
        self.board_args = {"board_type": board_type, "count": count}
        return pd.DataFrame(
            [
                {
                    "code": "881001",
                    "name": "sample sector",
                    "price": 100.0,
                }
            ]
        )

    def get_board_members(
        self,
        board_symbol: str,
        count: int = 100000,
        sort_type: SortType = SortType.CHANGE_PCT,
        sort_order: SortOrder = SortOrder.DESC,
        fields: object = None,
        exclude_flags: list[object] | None = None,
    ) -> pd.DataFrame:
        self.board_args = {
            "board_symbol": board_symbol,
            "count": count,
            "sort_type": sort_type,
            "sort_order": sort_order,
            "fields": fields,
            "exclude_flags": exclude_flags,
        }
        return pd.DataFrame(
            [
                {
                    "market": int(Market.SH),
                    "code": "600519",
                    "name": "sample member",
                    "price": 100.0,
                    "change_pct": 1.2,
                }
            ]
        )

    def get_board_ranking(
        self,
        board_type: BoardType = BoardType.HY,
        top_n: int = 50,
        sort_by: str = "change_pct",
        ascending: bool = False,
    ) -> pd.DataFrame:
        self.board_args = {
            "board_type": board_type,
            "top_n": top_n,
            "sort_by": sort_by,
            "ascending": ascending,
        }
        return pd.DataFrame(
            [
                {
                    "code": "881001",
                    "name": "sample sector",
                    "change_pct": 1.2,
                    "amount": 1000000.0,
                    "vol": 10000,
                    "main_net_amount": 50000.0,
                    "up_count": 10,
                    "down_count": 2,
                    "member_count": 12,
                }
            ]
        )

    def get_unusual(
        self,
        market: int,
        start: int = 0,
        count: int = 0,
    ) -> pd.DataFrame:
        self.board_args = {"market": market, "start": start, "count": count}
        return pd.DataFrame(
            [
                {
                    "time": "10:30",
                    "code": "600519",
                    "name": "sample",
                    "event": "rapid_rise",
                }
            ]
        )


class FakeTdxClient:
    def __enter__(self) -> FakeTdxClient:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get_market_stat(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "up_count": 3000,
                    "down_count": 2000,
                    "neutral_count": 100,
                    "suspended_count": 50,
                    "total_count": 5150,
                    "total_amount": 1_000_000_000.0,
                    "total_volume": 10_000_000,
                    "total_market_cap": 90_000_000_000_000.0,
                    "limit_up_count": 80,
                    "limit_down_count": 20,
                }
            ]
        )


class FakeHkClient:
    def __init__(self) -> None:
        self.stocks: list[tuple[int, str]] | None = None
        self.kline_args: dict[str, object] | None = None
        self.tick_args: dict[str, object] | None = None

    def __enter__(self) -> FakeHkClient:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def goods_quotes(
        self,
        stocks: list[tuple[int, str]],
        fields: object = None,
    ) -> pd.DataFrame:
        self.stocks = stocks
        return pd.DataFrame(
            [
                {
                    "market": market,
                    "code": code,
                    "name": "sample hk",
                    "price": 300.0,
                }
                for market, code in stocks
            ]
        )

    def goods_kline(
        self,
        market: int,
        code: str,
        period: Period = Period.DAILY,
        start: int = 0,
        count: int = 800,
        adjust: Adjust = Adjust.NONE,
    ) -> pd.DataFrame:
        self.kline_args = {
            "market": market,
            "code": code,
            "period": period,
            "start": start,
            "count": count,
            "adjust": adjust,
        }
        return pd.DataFrame(
            [
                {
                    "datetime": pd.Timestamp("2026-06-09 10:00:00"),
                    "open": 300.0,
                    "close": 305.0,
                }
            ]
        )

    def goods_tick_chart(
        self,
        market: int,
        code: str,
        query_date: date | None = None,
    ) -> pd.DataFrame:
        self.tick_args = {"market": market, "code": code, "query_date": query_date}
        return pd.DataFrame(
            [
                {
                    "datetime": pd.Timestamp("2026-06-09 10:01:00"),
                    "price": 301.0,
                    "vol": 1000,
                }
            ]
        )


def _indicator_kline_rows(count: int, *, base: float = 10.0) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "datetime": pd.Timestamp("2026-06-09") + pd.Timedelta(days=i),
                "open": base + i,
                "close": base + 0.5 + i,
                "high": base + 0.8 + i,
                "low": base - 0.1 + i,
                "vol": 1000 + i,
            }
            for i in range(count)
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
    assert fake.kline_args is not None
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


def test_a_share_sector_list_facade() -> None:
    fake = FakeMacClient()
    result = facade.a_share_sector_list(
        sector_type="concept",
        count=20,
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.board_args == {"board_type": BoardType.GN, "count": 20}
    assert result["rows"][0]["code"] == "881001"


def test_a_share_sector_members_facade() -> None:
    fake = FakeMacClient()
    result = facade.a_share_sector_members(
        sector_symbol="881001",
        count=30,
        sort_by="amount",
        ascending=True,
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.board_args == {
        "board_symbol": "881001",
        "count": 30,
        "sort_type": SortType.TOTAL_AMOUNT,
        "sort_order": SortOrder.ASC,
        "fields": None,
        "exclude_flags": None,
    }


def test_a_share_sector_ranking_facade() -> None:
    fake = FakeMacClient()
    result = facade.a_share_sector_ranking(
        sector_type="industry",
        top_n=10,
        sort_by="amount",
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.board_args == {
        "board_type": BoardType.HY,
        "top_n": 10,
        "sort_by": "amount",
        "ascending": False,
    }


def test_a_share_sector_ranking_enforces_limit() -> None:
    result = facade.a_share_sector_ranking(top_n=101)

    assert result["ok"] is False
    assert result["error"]["code"] == "LIMIT_EXCEEDED"


def test_a_share_market_events_facade() -> None:
    fake = FakeMacClient()
    result = facade.a_share_market_events(
        market="SZ",
        start=5,
        count=50,
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.board_args == {"market": int(Market.SZ), "start": 5, "count": 50}


def test_a_share_market_events_enforces_limit() -> None:
    result = facade.a_share_market_events(market="SH", count=601)

    assert result["ok"] is False
    assert result["error"]["code"] == "LIMIT_EXCEEDED"


def test_a_share_market_snapshot_facade() -> None:
    result = facade.a_share_market_snapshot(client_factory=FakeTdxClient)

    assert result["ok"] is True
    assert result["count"] == 1
    assert result["rows"][0]["up_count"] == 3000
    assert result["rows"][0]["limit_down_count"] == 20


def test_technical_indicator_catalog_facade() -> None:
    result = facade.technical_indicator_catalog()

    assert result["ok"] is True
    names = {row["name"] for row in result["rows"]}
    assert {"MACD", "KDJ", "RSI", "BOLL", "MA", "EMA"}.issubset(names)


def test_a_share_technical_indicators_facade() -> None:
    class IndicatorFakeClient(FakeMacClient):
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
                        "datetime": pd.Timestamp("2026-06-09") + pd.Timedelta(days=i),
                        "open": 10.0 + i,
                        "close": 10.5 + i,
                        "high": 10.8 + i,
                        "low": 9.9 + i,
                        "vol": 1000 + i,
                    }
                    for i in range(count)
                ]
            )

    fake = IndicatorFakeClient()
    result = facade.a_share_technical_indicators(
        symbol="SH600519",
        count=20,
        indicators=["MACD", "RSI"],
        params={"RSI": {"N": 14}},
        keep_ohlcv=False,
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.kline_args is not None
    assert fake.kline_args["market"] == int(Market.SH)
    assert fake.kline_args["code"] == "600519"
    assert fake.kline_args["count"] == 200
    assert fake.kline_args["adjust"] == Adjust.QFQ
    assert result["metadata"] == {
        "fetch_count": 200,
        "warmup_rows": 120,
        "indicator_params": {"RSI": {"N": 14}},
    }
    assert "MACD_DIF" in result["rows"][0]
    assert "RSI" in result["rows"][0]
    assert "open" not in result["rows"][0]


def test_a_share_technical_indicators_uses_default_indicator_set() -> None:
    class IndicatorFakeClient(FakeMacClient):
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
            self.kline_args = {"count": count}
            return _indicator_kline_rows(count)

    fake = IndicatorFakeClient()
    result = facade.a_share_technical_indicators(
        symbol="SH600519",
        count=20,
        keep_ohlcv=False,
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.kline_args == {"count": 200}
    assert result["count"] == 20
    assert {"MACD_DIF", "KDJ_K", "RSI", "BOLL_UPPER", "ATR", "CCI", "OBV", "BIAS1"}.issubset(
        result["rows"][0]
    )


def test_a_share_technical_indicators_rejects_unknown_indicator() -> None:
    result = facade.a_share_technical_indicators(
        symbol="SH600519",
        indicators=["NO_SUCH_INDICATOR"],
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "UNKNOWN_INDICATOR"


def test_a_share_technical_indicators_maps_missing_input() -> None:
    class MissingHighLowClient(FakeMacClient):
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
            return pd.DataFrame([{"datetime": pd.Timestamp("2026-06-09"), "close": 10.0}])

    result = facade.a_share_technical_indicators(
        symbol="SH600519",
        indicators=["KDJ"],
        client_factory=MissingHighLowClient,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "INDICATOR_INPUT_MISSING"


def test_a_share_technical_indicators_enforces_return_limit() -> None:
    result = facade.a_share_technical_indicators(symbol="SH600519", count=1001)

    assert result["ok"] is False
    assert result["error"]["code"] == "LIMIT_EXCEEDED"


def test_a_share_market_analysis_facade() -> None:
    class AnalysisFakeClient(FakeMacClient):
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
                        "datetime": pd.Timestamp("2026-06-09") + pd.Timedelta(days=i),
                        "open": 10.0 + i,
                        "close": 10.5 + i,
                        "high": 10.8 + i,
                        "low": 9.9 + i,
                        "vol": 1000 + i,
                    }
                    for i in range(count)
                ]
            )

    fake = AnalysisFakeClient()
    result = facade.a_share_market_analysis(
        symbol="SH600519",
        count=20,
        indicators=["MA", "EMA"],
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert result["count"] == 1
    assert fake.stocks == [(int(Market.SH), "600519")]
    assert fake.kline_args is not None
    assert fake.kline_args["count"] == 200
    data = result["data"]
    assert data["quote"]["code"] == "600519"
    assert data["kline"]["count"] == 20
    assert data["indicators"]["count"] == 20
    assert "MA" in data["indicators"]["rows"][0]
    assert (
        data["metadata"]["warning"]
        == "technical indicators are derived data, not investment advice"
    )
    assert "errors" not in data


def test_a_share_market_analysis_keeps_partial_quote_error() -> None:
    class QuoteFailingClient(FakeMacClient):
        def get_stock_quotes(
            self,
            stocks: list[tuple[int, str]],
            fields: object = None,
        ) -> pd.DataFrame:
            raise TdxError("quote unavailable")

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
            return pd.DataFrame(
                [
                    {
                        "datetime": pd.Timestamp("2026-06-09") + pd.Timedelta(days=i),
                        "open": 10.0 + i,
                        "close": 10.5 + i,
                        "high": 10.8 + i,
                        "low": 9.9 + i,
                        "vol": 1000 + i,
                    }
                    for i in range(count)
                ]
            )

    result = facade.a_share_market_analysis(
        symbol="SH600519",
        count=20,
        indicators=["MA"],
        client_factory=QuoteFailingClient,
    )

    assert result["ok"] is True
    assert result["data"]["quote"] is None
    assert result["data"]["errors"] == [
        {"block": "quote", "code": "TDX_ERROR", "message": "quote unavailable"}
    ]


def test_a_share_market_analysis_fails_on_core_kline_error() -> None:
    class KlineFailingClient(FakeMacClient):
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
            raise TdxError("kline unavailable")

    result = facade.a_share_market_analysis(
        symbol="SH600519",
        client_factory=KlineFailingClient,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "TDX_ERROR"
    assert result["error"]["details"]["block"] == "kline"


def test_a_share_market_analysis_ignores_indicators_when_not_requested() -> None:
    result = facade.a_share_market_analysis(
        symbol="SH600519",
        include_indicators=False,
        indicators=["NO_SUCH_INDICATOR"],
        client_factory=FakeMacClient,
    )

    assert result["ok"] is True
    assert "indicators" not in result["data"]


def test_a_share_market_analysis_rejects_invalid_include_combinations() -> None:
    result = facade.a_share_market_analysis(
        symbol="SH600519",
        include_quote=False,
        include_kline=False,
        include_indicators=False,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "INVALID_ANALYSIS_REQUEST"

    result = facade.a_share_market_analysis(
        symbol="SH600519",
        include_quote=True,
        include_kline=False,
        include_indicators=False,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "INVALID_ANALYSIS_REQUEST"


def test_a_share_market_analysis_fails_on_core_indicator_error() -> None:
    class MissingHighLowClient(FakeMacClient):
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
            return pd.DataFrame([{"datetime": pd.Timestamp("2026-06-09"), "close": 10.0}])

    result = facade.a_share_market_analysis(
        symbol="SH600519",
        indicators=["KDJ"],
        client_factory=MissingHighLowClient,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "INDICATOR_INPUT_MISSING"
    assert result["error"]["details"]["block"] == "indicators"


def test_hk_realtime_quotes_facade() -> None:
    fake = FakeHkClient()
    result = facade.hk_realtime_quotes(
        symbols=["00700", "HK 00941"],
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.stocks == [
        (int(ExMarket.HK_MAIN_BOARD), "00700"),
        (int(ExMarket.HK_MAIN_BOARD), "00941"),
    ]
    assert result["rows"][0]["code"] == "00700"


def test_hk_realtime_quotes_enforces_symbol_limit() -> None:
    result = facade.hk_realtime_quotes(symbols=["00700"] * 81)

    assert result["ok"] is False
    assert result["error"]["code"] == "LIMIT_EXCEEDED"


def test_hk_realtime_quotes_rejects_unknown_market() -> None:
    result = facade.hk_realtime_quotes(market="US_STOCK", code="AAPL")

    assert result["ok"] is False
    assert result["error"]["code"] == "INVALID_MARKET"


def test_hk_kline_bars_facade() -> None:
    fake = FakeHkClient()
    result = facade.hk_kline_bars(
        market="HK_GEM",
        code="08000",
        period="DAILY",
        count=20,
        adjust="NONE",
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.kline_args == {
        "market": int(ExMarket.HK_GEM),
        "code": "08000",
        "period": Period.DAILY,
        "start": 0,
        "count": 20,
        "adjust": Adjust.NONE,
    }


def test_hk_technical_indicators_facade() -> None:
    class IndicatorFakeHkClient(FakeHkClient):
        def goods_kline(
            self,
            market: int,
            code: str,
            period: Period = Period.DAILY,
            start: int = 0,
            count: int = 800,
            adjust: Adjust = Adjust.NONE,
        ) -> pd.DataFrame:
            self.kline_args = {
                "market": market,
                "code": code,
                "period": period,
                "start": start,
                "count": count,
                "adjust": adjust,
            }
            return pd.DataFrame(
                [
                    {
                        "datetime": pd.Timestamp("2026-06-09") + pd.Timedelta(days=i),
                        "open": 300.0 + i,
                        "close": 301.0 + i,
                        "high": 302.0 + i,
                        "low": 299.0 + i,
                        "vol": 1000 + i,
                    }
                    for i in range(count)
                ]
            )

    fake = IndicatorFakeHkClient()
    result = facade.hk_technical_indicators(
        symbol="00700",
        count=20,
        indicators=["MA", "EMA"],
        keep_ohlcv=False,
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.kline_args == {
        "market": int(ExMarket.HK_MAIN_BOARD),
        "code": "00700",
        "period": Period.DAILY,
        "start": 0,
        "count": 200,
        "adjust": Adjust.QFQ,
    }
    assert result["metadata"] == {
        "fetch_count": 200,
        "warmup_rows": 120,
        "indicator_params": {},
    }
    assert "MA" in result["rows"][0]
    assert "EMA" in result["rows"][0]
    assert "close" not in result["rows"][0]


def test_hk_technical_indicators_uses_default_indicator_set() -> None:
    class IndicatorFakeHkClient(FakeHkClient):
        def goods_kline(
            self,
            market: int,
            code: str,
            period: Period = Period.DAILY,
            start: int = 0,
            count: int = 800,
            adjust: Adjust = Adjust.NONE,
        ) -> pd.DataFrame:
            self.kline_args = {"count": count}
            return _indicator_kline_rows(count, base=300.0)

    fake = IndicatorFakeHkClient()
    result = facade.hk_technical_indicators(
        symbol="00700",
        count=20,
        keep_ohlcv=False,
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.kline_args == {"count": 200}
    assert result["count"] == 20
    assert {"MACD_DIF", "KDJ_K", "RSI", "BOLL_UPPER", "ATR", "CCI", "OBV", "BIAS1"}.issubset(
        result["rows"][0]
    )


def test_hk_technical_indicators_rejects_unknown_market() -> None:
    result = facade.hk_technical_indicators(
        market="US_STOCK",
        code="AAPL",
        indicators=["MA"],
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "INVALID_MARKET"


def test_hk_market_analysis_facade() -> None:
    class AnalysisFakeHkClient(FakeHkClient):
        def goods_kline(
            self,
            market: int,
            code: str,
            period: Period = Period.DAILY,
            start: int = 0,
            count: int = 800,
            adjust: Adjust = Adjust.NONE,
        ) -> pd.DataFrame:
            self.kline_args = {
                "market": market,
                "code": code,
                "period": period,
                "start": start,
                "count": count,
                "adjust": adjust,
            }
            return pd.DataFrame(
                [
                    {
                        "datetime": pd.Timestamp("2026-06-09") + pd.Timedelta(days=i),
                        "open": 300.0 + i,
                        "close": 301.0 + i,
                        "high": 302.0 + i,
                        "low": 299.0 + i,
                        "vol": 1000 + i,
                    }
                    for i in range(count)
                ]
            )

    fake = AnalysisFakeHkClient()
    result = facade.hk_market_analysis(
        symbol="00700",
        count=20,
        indicators=["MA", "EMA"],
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert result["count"] == 1
    assert fake.stocks == [(int(ExMarket.HK_MAIN_BOARD), "00700")]
    assert fake.kline_args is not None
    assert fake.kline_args["count"] == 200
    data = result["data"]
    assert data["quote"]["code"] == "00700"
    assert data["kline"]["count"] == 20
    assert data["indicators"]["count"] == 20
    assert "EMA" in data["indicators"]["rows"][0]
    assert (
        data["metadata"]["warning"]
        == "technical indicators are derived data, not investment advice"
    )


def test_hk_market_analysis_keeps_partial_quote_error() -> None:
    class QuoteFailingHkClient(FakeHkClient):
        def goods_quotes(
            self,
            stocks: list[tuple[int, str]],
            fields: object = None,
        ) -> pd.DataFrame:
            raise TdxError("quote unavailable")

        def goods_kline(
            self,
            market: int,
            code: str,
            period: Period = Period.DAILY,
            start: int = 0,
            count: int = 800,
            adjust: Adjust = Adjust.NONE,
        ) -> pd.DataFrame:
            return pd.DataFrame(
                [
                    {
                        "datetime": pd.Timestamp("2026-06-09") + pd.Timedelta(days=i),
                        "open": 300.0 + i,
                        "close": 301.0 + i,
                        "high": 302.0 + i,
                        "low": 299.0 + i,
                        "vol": 1000 + i,
                    }
                    for i in range(count)
                ]
            )

    result = facade.hk_market_analysis(
        symbol="00700",
        count=20,
        indicators=["MA"],
        client_factory=QuoteFailingHkClient,
    )

    assert result["ok"] is True
    assert result["data"]["quote"] is None
    assert result["data"]["errors"] == [
        {"block": "quote", "code": "TDX_ERROR", "message": "quote unavailable"}
    ]


def test_hk_market_analysis_fails_on_core_kline_error() -> None:
    class KlineFailingHkClient(FakeHkClient):
        def goods_kline(
            self,
            market: int,
            code: str,
            period: Period = Period.DAILY,
            start: int = 0,
            count: int = 800,
            adjust: Adjust = Adjust.NONE,
        ) -> pd.DataFrame:
            raise TdxError("kline unavailable")

    result = facade.hk_market_analysis(
        symbol="00700",
        client_factory=KlineFailingHkClient,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "TDX_ERROR"
    assert result["error"]["details"]["block"] == "kline"


def test_hk_market_analysis_rejects_invalid_include_combinations() -> None:
    result = facade.hk_market_analysis(
        symbol="00700",
        include_quote=False,
        include_kline=False,
        include_indicators=False,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "INVALID_ANALYSIS_REQUEST"

    result = facade.hk_market_analysis(
        symbol="00700",
        include_quote=True,
        include_kline=False,
        include_indicators=False,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "INVALID_ANALYSIS_REQUEST"


def test_hk_market_analysis_fails_on_core_indicator_error() -> None:
    class MissingHighLowHkClient(FakeHkClient):
        def goods_kline(
            self,
            market: int,
            code: str,
            period: Period = Period.DAILY,
            start: int = 0,
            count: int = 800,
            adjust: Adjust = Adjust.NONE,
        ) -> pd.DataFrame:
            return pd.DataFrame([{"datetime": pd.Timestamp("2026-06-09"), "close": 10.0}])

    result = facade.hk_market_analysis(
        symbol="00700",
        indicators=["KDJ"],
        client_factory=MissingHighLowHkClient,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "INDICATOR_INPUT_MISSING"
    assert result["error"]["details"]["block"] == "indicators"


def test_hk_intraday_timeseries_facade() -> None:
    fake = FakeHkClient()
    result = facade.hk_intraday_timeseries(
        symbol="HK 00700",
        date=20260609,
        client_factory=lambda: fake,
    )

    assert result["ok"] is True
    assert fake.tick_args == {
        "market": int(ExMarket.HK_MAIN_BOARD),
        "code": "00700",
        "query_date": date(2026, 6, 9),
    }


def test_hk_intraday_timeseries_rejects_bad_date() -> None:
    result = facade.hk_intraday_timeseries(symbol="HK 00700", date=20261340)

    assert result["ok"] is False
    assert result["error"]["code"] == "INVALID_DATE"


def test_tool_exception_uses_error_envelope_without_traceback() -> None:
    class RaisingQuoteClient(FakeMacClient):
        def get_stock_quotes(
            self,
            stocks: list[tuple[int, str]],
            fields: object = None,
        ) -> pd.DataFrame:
            raise RuntimeError("boom")

    result = facade.a_share_realtime_quotes(
        symbols=["SH600519"],
        client_factory=RaisingQuoteClient,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "TOOL_ERROR"
    assert result["error"]["message"] == "boom"
    assert "Traceback" not in result["error"]["message"]


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
                "a_share_sector_list",
                "a_share_sector_members",
                "a_share_sector_ranking",
                "a_share_market_events",
                "a_share_market_snapshot",
                "technical_indicator_catalog",
                "a_share_technical_indicators",
                "a_share_market_analysis",
                "hk_realtime_quotes",
                "hk_kline_bars",
                "hk_technical_indicators",
                "hk_market_analysis",
                "hk_intraday_timeseries",
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
