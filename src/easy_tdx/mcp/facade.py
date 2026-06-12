"""Business facade for MCP tools.

FastMCP registration stays thin; parsing, conversion, limits, and client
selection live here so they can be tested without starting an MCP transport.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from importlib.metadata import PackageNotFoundError, version
from types import TracebackType
from typing import Any, Protocol, cast

import pandas as pd

from easy_tdx import __version__ as module_version
from easy_tdx.client import TdxClient
from easy_tdx.ex.mac_client import MacExClient
from easy_tdx.exceptions import TdxError
from easy_tdx.indicator import compute_indicators, list_indicators
from easy_tdx.mac.client import MacClient
from easy_tdx.mac.enums import Adjust, BoardType, ExMarket, Period, SortOrder, SortType
from easy_tdx.models.enums import Market

_PACKAGE_NAME = "easy-tdx"
_DEFAULT_ROW_LIMIT = 200
_MAX_ROW_LIMIT = 1000
_MAX_QUOTE_SYMBOLS = 80
_DEFAULT_RANKING_LIMIT = 30
_MAX_RANKING_LIMIT = 100
_DEFAULT_EVENT_LIMIT = 100
_MAX_EVENT_LIMIT = 600
_DEFAULT_INDICATOR_ROW_LIMIT = 120
_MAX_INDICATOR_ROW_LIMIT = 1000
_DEFAULT_INDICATOR_WARMUP_ROWS = 120
_MAX_INDICATOR_FETCH_ROWS = 1200
_DEFAULT_TECHNICAL_INDICATORS = ["MACD", "KDJ", "RSI", "BOLL", "ATR", "CCI", "OBV", "BIAS"]
_DEFAULT_ANALYSIS_INDICATORS = ["MACD", "KDJ", "RSI", "BOLL", "MA", "EMA"]
_ANALYSIS_WARNING = "technical indicators are derived data, not investment advice"
_A_SHARE_MARKETS = {
    "SH": Market.SH,
    "SZ": Market.SZ,
    "BJ": Market.BJ,
}
_HK_MARKET_ALIASES = {
    "HK": ExMarket.HK_MAIN_BOARD,
    "HK_MAIN_BOARD": ExMarket.HK_MAIN_BOARD,
    "MAIN": ExMarket.HK_MAIN_BOARD,
    "MAIN_BOARD": ExMarket.HK_MAIN_BOARD,
    "HK_GEM": ExMarket.HK_GEM,
    "GEM": ExMarket.HK_GEM,
    "HK_INDEX": ExMarket.HK_INDEX,
    "INDEX": ExMarket.HK_INDEX,
    "HK_FUND": ExMarket.HK_FUND,
    "FUND": ExMarket.HK_FUND,
}
_SECTOR_TYPE_ALIASES = {
    "ALL": BoardType.ALL,
    "INDUSTRY": BoardType.HY,
    "INDUSTRY_LEVEL1": BoardType.HY,
    "INDUSTRY_LEVEL2": BoardType.HY2,
    "CONCEPT": BoardType.GN,
    "STYLE": BoardType.FG,
    "REGION": BoardType.DQ,
}
_MEMBER_SORT_ALIASES = {
    "CHANGE_PCT": SortType.CHANGE_PCT,
    "AMOUNT": SortType.TOTAL_AMOUNT,
    "TOTAL_AMOUNT": SortType.TOTAL_AMOUNT,
    "VOLUME": SortType.VOLUME,
    "CODE": SortType.CODE,
    "PRICE": SortType.PRICE,
}
_RANKING_SORT_FIELDS = {"change_pct", "amount", "main_net_amount", "vol"}
_PERIOD_ALIASES = {
    "1MIN": Period.MIN_1,
    "MIN1": Period.MIN_1,
    "MIN_1": Period.MIN_1,
    "5MIN": Period.MIN_5,
    "MIN5": Period.MIN_5,
    "MIN_5": Period.MIN_5,
    "15MIN": Period.MIN_15,
    "MIN15": Period.MIN_15,
    "MIN_15": Period.MIN_15,
    "30MIN": Period.MIN_30,
    "MIN30": Period.MIN_30,
    "MIN_30": Period.MIN_30,
    "60MIN": Period.MIN_60,
    "MIN60": Period.MIN_60,
    "MIN_60": Period.MIN_60,
    "DAY": Period.DAILY,
    "DAILY": Period.DAILY,
    "WEEK": Period.WEEKLY,
    "WEEKLY": Period.WEEKLY,
    "MONTH": Period.MONTHLY,
    "MONTHLY": Period.MONTHLY,
}
_ADJUST_ALIASES = {
    "NONE": Adjust.NONE,
    "QFQ": Adjust.QFQ,
    "HFQ": Adjust.HFQ,
}


class QuoteClient(Protocol):
    def __enter__(self) -> QuoteClient: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    def get_stock_quotes(
        self,
        stocks: list[tuple[int, str]],
        fields: object = None,
    ) -> pd.DataFrame: ...

    def get_stock_kline(
        self,
        market: int,
        code: str,
        period: Period = Period.DAILY,
        start: int = 0,
        count: int = 800,
        times: int = 1,
        adjust: Adjust = Adjust.NONE,
    ) -> pd.DataFrame: ...

    def get_tick_chart(
        self,
        market: int,
        code: str,
        date: int | None = None,
    ) -> pd.DataFrame: ...

    def get_tick_charts(
        self,
        market: int,
        code: str,
        date: int | None = None,
        days: int = 5,
    ) -> pd.DataFrame: ...

    def get_transactions(
        self,
        market: int,
        code: str,
        count: int = 2000,
        start: int = 0,
        date: int | None = None,
    ) -> pd.DataFrame: ...

    def get_board_list(
        self,
        board_type: BoardType = BoardType.ALL,
        count: int = 10000,
    ) -> pd.DataFrame: ...

    def get_board_members(
        self,
        board_symbol: str,
        count: int = 100000,
        sort_type: SortType = SortType.CHANGE_PCT,
        sort_order: SortOrder = SortOrder.DESC,
        fields: object = None,
        exclude_flags: list[object] | None = None,
    ) -> pd.DataFrame: ...

    def get_board_ranking(
        self,
        board_type: BoardType = BoardType.HY,
        top_n: int = 50,
        sort_by: str = "change_pct",
        ascending: bool = False,
    ) -> pd.DataFrame: ...

    def get_unusual(
        self,
        market: int,
        start: int = 0,
        count: int = 0,
    ) -> pd.DataFrame: ...


QuoteClientFactory = Callable[[], QuoteClient]


class SnapshotClient(Protocol):
    def __enter__(self) -> SnapshotClient: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    def get_market_stat(self) -> pd.DataFrame: ...


SnapshotClientFactory = Callable[[], SnapshotClient]


class HkQuoteClient(Protocol):
    def __enter__(self) -> HkQuoteClient: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    def goods_quotes(
        self,
        stocks: list[tuple[int, str]],
        fields: object = None,
    ) -> pd.DataFrame: ...

    def goods_kline(
        self,
        market: int,
        code: str,
        period: Period = Period.DAILY,
        start: int = 0,
        count: int = 800,
        adjust: Adjust = Adjust.NONE,
    ) -> pd.DataFrame: ...

    def goods_tick_chart(
        self,
        market: int,
        code: str,
        query_date: date | None = None,
    ) -> pd.DataFrame: ...


HkQuoteClientFactory = Callable[[], HkQuoteClient]
IndicatorParams = dict[str, dict[str, int | float]]


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


def error_envelope(
    code: str,
    message: str,
    *,
    query: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create the common MCP error envelope."""
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {
        "ok": False,
        "source": "easy_tdx",
        "query": query or {},
        "count": 0,
        "error": error,
    }


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def dataframe_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame to JSON-safe row dictionaries."""
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    return [{str(k): _json_safe(v) for k, v in row.items()} for row in records]


def _split_symbol(symbol: str) -> tuple[str | None, str]:
    cleaned = symbol.strip().upper().replace(".", " ")
    if not cleaned:
        return None, ""
    parts = cleaned.split()
    if len(parts) == 2:
        return parts[0], parts[1]
    for prefix in _A_SHARE_MARKETS:
        if cleaned.startswith(prefix) and len(cleaned) > len(prefix):
            return prefix, cleaned[len(prefix) :]
    return None, cleaned


def _split_hk_symbol(symbol: str) -> tuple[str | None, str]:
    cleaned = symbol.strip().upper().replace(".", " ")
    if not cleaned:
        return None, ""
    parts = cleaned.split()
    if len(parts) == 2:
        return parts[0], parts[1]
    if cleaned.startswith("HK") and len(cleaned) > 2 and cleaned[2].isdigit():
        return "HK", cleaned[2:]
    return None, cleaned


def _coerce_positive_limit(
    value: int | None,
    *,
    default: int = _DEFAULT_ROW_LIMIT,
    maximum: int = _MAX_ROW_LIMIT,
    query: dict[str, Any],
) -> tuple[int | None, dict[str, Any] | None]:
    count = default if value is None else value
    if count <= 0:
        return None, error_envelope(
            "INVALID_LIMIT",
            "count must be positive",
            query=query,
            details={"count": count},
        )
    if count > maximum:
        return None, error_envelope(
            "LIMIT_EXCEEDED",
            f"count supports at most {maximum} rows",
            query=query,
            details={"max": maximum, "actual": count},
        )
    return count, None


def _parse_period(
    value: str,
    *,
    query: dict[str, Any],
) -> tuple[Period | None, dict[str, Any] | None]:
    key = value.strip().upper().replace("-", "_")
    if key in _PERIOD_ALIASES:
        return _PERIOD_ALIASES[key], None
    return None, error_envelope(
        "INVALID_PERIOD",
        "unsupported period",
        query=query,
        details={"period": value, "supported": sorted(_PERIOD_ALIASES)},
    )


def _parse_adjust(
    value: str,
    *,
    query: dict[str, Any],
) -> tuple[Adjust | None, dict[str, Any] | None]:
    key = value.strip().upper()
    if key in _ADJUST_ALIASES:
        return _ADJUST_ALIASES[key], None
    return None, error_envelope(
        "INVALID_ADJUST",
        "adjust must be NONE, QFQ, or HFQ",
        query=query,
        details={"adjust": value},
    )


def _parse_a_share_market(
    value: str,
    *,
    query: dict[str, Any],
) -> tuple[int | None, dict[str, Any] | None]:
    key = value.strip().upper()
    if key in _A_SHARE_MARKETS:
        return int(_A_SHARE_MARKETS[key]), None
    return None, error_envelope(
        "INVALID_MARKET",
        "A-share market must be SH, SZ, or BJ",
        query=query,
        details={"market": value},
    )


def _parse_sector_type(
    value: str,
    *,
    query: dict[str, Any],
) -> tuple[BoardType | None, dict[str, Any] | None]:
    key = value.strip().upper().replace("-", "_")
    if key in _SECTOR_TYPE_ALIASES:
        return _SECTOR_TYPE_ALIASES[key], None
    return None, error_envelope(
        "INVALID_SECTOR_TYPE",
        "unsupported A-share sector type",
        query=query,
        details={"sector_type": value, "supported": sorted(_SECTOR_TYPE_ALIASES)},
    )


def _parse_member_sort_type(
    value: str,
    *,
    query: dict[str, Any],
) -> tuple[SortType | None, dict[str, Any] | None]:
    key = value.strip().upper().replace("-", "_")
    if key in _MEMBER_SORT_ALIASES:
        return _MEMBER_SORT_ALIASES[key], None
    return None, error_envelope(
        "INVALID_SORT",
        "unsupported A-share sector member sort field",
        query=query,
        details={"sort_by": value, "supported": sorted(_MEMBER_SORT_ALIASES)},
    )


def _parse_hk_market(
    value: str,
    *,
    query: dict[str, Any],
) -> tuple[int | None, dict[str, Any] | None]:
    key = value.strip().upper().replace("-", "_").replace(" ", "_")
    if key in _HK_MARKET_ALIASES:
        return int(_HK_MARKET_ALIASES[key]), None
    return None, error_envelope(
        "INVALID_MARKET",
        "Hong Kong market must be HK_MAIN_BOARD, HK_GEM, HK_INDEX, or HK_FUND",
        query=query,
        details={"market": value, "supported": sorted(_HK_MARKET_ALIASES)},
    )


def _normalize_single_a_share_symbol(
    *,
    symbol: str | None = None,
    market: str | None = None,
    code: str | None = None,
    query: dict[str, Any],
) -> tuple[tuple[int, str] | None, dict[str, Any] | None]:
    symbols = [symbol] if symbol else None
    normalized, error = _normalize_a_share_symbols(symbols=symbols, market=market, code=code)
    if error is not None:
        return None, error
    assert normalized is not None
    if len(normalized) != 1:
        return None, error_envelope(
            "INVALID_SYMBOL",
            "query requires exactly one A-share symbol",
            query=query,
        )
    return normalized[0], None


def _normalize_a_share_symbols(
    *,
    symbols: list[str] | None = None,
    market: str | None = None,
    code: str | None = None,
) -> tuple[list[tuple[int, str]] | None, dict[str, Any] | None]:
    query: dict[str, Any] = {"symbols": symbols or [], "market": market, "code": code}
    raw_symbols = list(symbols or [])
    if market is not None or code is not None:
        if not market or not code:
            return None, error_envelope(
                "INVALID_SYMBOL",
                "market and code must be provided together",
                query=query,
            )
        raw_symbols.append(f"{market} {code}")
    if not raw_symbols:
        return None, error_envelope(
            "INVALID_SYMBOL",
            "at least one A-share symbol is required",
            query=query,
        )
    if len(raw_symbols) > _MAX_QUOTE_SYMBOLS:
        return None, error_envelope(
            "LIMIT_EXCEEDED",
            f"symbols supports at most {_MAX_QUOTE_SYMBOLS} items",
            query=query,
            details={"max": _MAX_QUOTE_SYMBOLS, "actual": len(raw_symbols)},
        )

    normalized: list[tuple[int, str]] = []
    for raw in raw_symbols:
        prefix, parsed_code = _split_symbol(raw)
        if prefix is None:
            return None, error_envelope(
                "SYMBOL_AMBIGUOUS",
                "A-share symbols must include market prefix SH, SZ, or BJ",
                query=query,
                details={"symbol": raw},
            )
        if prefix not in _A_SHARE_MARKETS:
            return None, error_envelope(
                "INVALID_MARKET",
                "A-share market must be SH, SZ, or BJ",
                query=query,
                details={"symbol": raw, "market": prefix},
            )
        if not parsed_code.isdigit() or len(parsed_code) != 6:
            return None, error_envelope(
                "INVALID_SYMBOL",
                "A-share code must be a 6-digit code",
                query=query,
                details={"symbol": raw, "code": parsed_code},
            )
        normalized.append((int(_A_SHARE_MARKETS[prefix]), parsed_code))
    return normalized, None


def _normalize_single_hk_symbol(
    *,
    symbol: str | None = None,
    market: str | None = None,
    code: str | None = None,
    query: dict[str, Any],
) -> tuple[tuple[int, str] | None, dict[str, Any] | None]:
    symbols = [symbol] if symbol else None
    normalized, error = _normalize_hk_symbols(symbols=symbols, market=market, code=code)
    if error is not None:
        return None, error
    assert normalized is not None
    if len(normalized) != 1:
        return None, error_envelope(
            "INVALID_SYMBOL",
            "query requires exactly one Hong Kong symbol",
            query=query,
        )
    return normalized[0], None


def _normalize_hk_symbols(
    *,
    symbols: list[str] | None = None,
    market: str | None = None,
    code: str | None = None,
) -> tuple[list[tuple[int, str]] | None, dict[str, Any] | None]:
    query: dict[str, Any] = {"symbols": symbols or [], "market": market, "code": code}
    raw_symbols = list(symbols or [])
    if market is not None or code is not None:
        if not code:
            return None, error_envelope(
                "INVALID_SYMBOL",
                "code is required when market is provided",
                query=query,
            )
        raw_symbols.append(f"{market or 'HK_MAIN_BOARD'} {code}")
    if not raw_symbols:
        return None, error_envelope(
            "INVALID_SYMBOL",
            "at least one Hong Kong symbol is required",
            query=query,
        )
    if len(raw_symbols) > _MAX_QUOTE_SYMBOLS:
        return None, error_envelope(
            "LIMIT_EXCEEDED",
            f"symbols supports at most {_MAX_QUOTE_SYMBOLS} items",
            query=query,
            details={"max": _MAX_QUOTE_SYMBOLS, "actual": len(raw_symbols)},
        )

    normalized: list[tuple[int, str]] = []
    for raw in raw_symbols:
        prefix, parsed_code = _split_hk_symbol(raw)
        market_id, error = _parse_hk_market(prefix or "HK_MAIN_BOARD", query=query)
        if error is not None:
            return None, error
        assert market_id is not None
        clean_code = parsed_code.strip().upper()
        if not clean_code:
            return None, error_envelope(
                "INVALID_SYMBOL",
                "Hong Kong code is required",
                query=query,
                details={"symbol": raw},
            )
        normalized.append((market_id, clean_code))
    return normalized, None


def _parse_query_date(
    value: int | None,
    *,
    query: dict[str, Any],
) -> tuple[date | None, dict[str, Any] | None]:
    if value is None:
        return None, None
    raw = str(value)
    try:
        return datetime.strptime(raw, "%Y%m%d").date(), None
    except ValueError:
        return None, error_envelope(
            "INVALID_DATE",
            "date must use YYYYMMDD format",
            query=query,
            details={"date": value},
        )


def _supported_indicator_names() -> set[str]:
    return {str(item["name"]).upper() for item in list_indicators()}


def _normalize_indicator_names(
    indicators: list[str] | None,
    *,
    query: dict[str, Any],
    default: list[str] = _DEFAULT_TECHNICAL_INDICATORS,
) -> tuple[list[str] | None, dict[str, Any] | None]:
    raw_names = default if indicators is None else indicators
    names = [name.strip().upper() for name in raw_names if name.strip()]
    if not names:
        return None, error_envelope(
            "INVALID_INDICATOR",
            "at least one technical indicator is required",
            query=query,
        )
    supported = _supported_indicator_names()
    unknown = [name for name in names if name not in supported]
    if unknown:
        return None, error_envelope(
            "UNKNOWN_INDICATOR",
            "unsupported technical indicator",
            query=query,
            details={"unknown": unknown, "supported": sorted(supported)},
        )
    return names, None


def _indicator_limits(
    count: int | None,
    *,
    query: dict[str, Any],
) -> tuple[tuple[int, int] | None, dict[str, Any] | None]:
    limit, error = _coerce_positive_limit(
        count,
        default=_DEFAULT_INDICATOR_ROW_LIMIT,
        maximum=_MAX_INDICATOR_ROW_LIMIT,
        query=query,
    )
    if error is not None:
        return None, error
    assert limit is not None
    fetch_count = min(
        max(limit + _DEFAULT_INDICATOR_WARMUP_ROWS, 200),
        _MAX_INDICATOR_FETCH_ROWS,
    )
    if fetch_count > _MAX_INDICATOR_FETCH_ROWS:
        return None, error_envelope(
            "LIMIT_EXCEEDED",
            f"indicator fetch_count supports at most {_MAX_INDICATOR_FETCH_ROWS} rows",
            query=query,
            details={"max": _MAX_INDICATOR_FETCH_ROWS, "actual": fetch_count},
        )
    return (limit, fetch_count), None


def _indicator_error_envelope(
    exc: Exception,
    *,
    query: dict[str, Any],
) -> dict[str, Any]:
    message = str(exc)
    if isinstance(exc, ValueError):
        if "未知指标" in message:
            return error_envelope("UNKNOWN_INDICATOR", message, query=query)
        if "缺少必要列" in message:
            return error_envelope("INDICATOR_INPUT_MISSING", message, query=query)
        return error_envelope("INVALID_INDICATOR_PARAM", message, query=query)
    if isinstance(exc, TypeError):
        return error_envelope("INVALID_INDICATOR_PARAM", message, query=query)
    return error_envelope("TOOL_ERROR", message, query=query)


def _error_with_block(result: dict[str, Any], block: str) -> dict[str, Any]:
    error = result.get("error")
    if isinstance(error, dict):
        details = error.setdefault("details", {})
        if isinstance(details, dict):
            details["block"] = block
    return result


def _partial_error(code: str, message: str, *, block: str) -> dict[str, Any]:
    return {"block": block, "code": code, "message": message}


def _default_mac_client_factory() -> QuoteClient:
    return cast(QuoteClient, MacClient.from_best_host())


def _default_tdx_client_factory() -> SnapshotClient:
    return cast(SnapshotClient, TdxClient.from_best_host())


def _default_hk_client_factory() -> HkQuoteClient:
    return cast(HkQuoteClient, MacExClient.from_best_host())


def a_share_realtime_quotes(
    *,
    symbols: list[str] | None = None,
    market: str | None = None,
    code: str | None = None,
    client_factory: QuoteClientFactory = _default_mac_client_factory,
) -> dict[str, Any]:
    """Fetch A-share realtime quotes for known symbols."""
    normalized, error = _normalize_a_share_symbols(symbols=symbols, market=market, code=code)
    query = {"symbols": symbols or [], "market": market, "code": code}
    if error is not None:
        return error
    assert normalized is not None
    try:
        with client_factory() as client:
            df = client.get_stock_quotes(normalized)
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)

    rows = dataframe_rows(df)
    return envelope(source="easy_tdx", query=query, rows=rows)


def a_share_kline_bars(
    *,
    symbol: str | None = None,
    market: str | None = None,
    code: str | None = None,
    period: str = "DAILY",
    count: int | None = _DEFAULT_ROW_LIMIT,
    start: int = 0,
    adjust: str = "NONE",
    client_factory: QuoteClientFactory = _default_mac_client_factory,
) -> dict[str, Any]:
    """Fetch A-share K-line bars for a known symbol."""
    query = {
        "symbol": symbol,
        "market": market,
        "code": code,
        "period": period,
        "count": count,
        "start": start,
        "adjust": adjust,
    }
    if start < 0:
        return error_envelope(
            "INVALID_OFFSET",
            "start must be non-negative",
            query=query,
            details={"start": start},
        )
    normalized, error = _normalize_single_a_share_symbol(
        symbol=symbol, market=market, code=code, query=query
    )
    if error is not None:
        return error
    assert normalized is not None
    limit, error = _coerce_positive_limit(count, query=query)
    if error is not None:
        return error
    assert limit is not None
    parsed_period, error = _parse_period(period, query=query)
    if error is not None:
        return error
    assert parsed_period is not None
    parsed_adjust, error = _parse_adjust(adjust, query=query)
    if error is not None:
        return error
    assert parsed_adjust is not None
    market_id, parsed_code = normalized

    try:
        with client_factory() as client:
            df = client.get_stock_kline(
                market_id,
                parsed_code,
                period=parsed_period,
                start=start,
                count=limit,
                adjust=parsed_adjust,
            )
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)

    return envelope(source="easy_tdx", query=query, rows=dataframe_rows(df))


def a_share_intraday_timeseries(
    *,
    symbol: str | None = None,
    market: str | None = None,
    code: str | None = None,
    date: int | None = None,
    days: int = 1,
    client_factory: QuoteClientFactory = _default_mac_client_factory,
) -> dict[str, Any]:
    """Fetch A-share intraday minute-level time series."""
    query = {"symbol": symbol, "market": market, "code": code, "date": date, "days": days}
    if days <= 0 or days > 5:
        return error_envelope(
            "INVALID_LIMIT",
            "days must be between 1 and 5",
            query=query,
            details={"days": days, "max": 5},
        )
    normalized, error = _normalize_single_a_share_symbol(
        symbol=symbol, market=market, code=code, query=query
    )
    if error is not None:
        return error
    assert normalized is not None
    market_id, parsed_code = normalized
    try:
        with client_factory() as client:
            if days == 1:
                df = client.get_tick_chart(market_id, parsed_code, date=date)
            else:
                df = client.get_tick_charts(market_id, parsed_code, date=date, days=days)
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)
    return envelope(source="easy_tdx", query=query, rows=dataframe_rows(df))


def a_share_trade_ticks(
    *,
    symbol: str | None = None,
    market: str | None = None,
    code: str | None = None,
    date: int | None = None,
    start: int = 0,
    count: int | None = _DEFAULT_ROW_LIMIT,
    client_factory: QuoteClientFactory = _default_mac_client_factory,
) -> dict[str, Any]:
    """Fetch A-share trade tick records."""
    query = {
        "symbol": symbol,
        "market": market,
        "code": code,
        "date": date,
        "start": start,
        "count": count,
    }
    if start < 0:
        return error_envelope(
            "INVALID_OFFSET",
            "start must be non-negative",
            query=query,
            details={"start": start},
        )
    limit, error = _coerce_positive_limit(count, query=query)
    if error is not None:
        return error
    assert limit is not None
    normalized, error = _normalize_single_a_share_symbol(
        symbol=symbol, market=market, code=code, query=query
    )
    if error is not None:
        return error
    assert normalized is not None
    market_id, parsed_code = normalized
    try:
        with client_factory() as client:
            df = client.get_transactions(
                market_id,
                parsed_code,
                count=limit,
                start=start,
                date=date,
            )
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)
    return envelope(source="easy_tdx", query=query, rows=dataframe_rows(df))


def a_share_sector_list(
    *,
    sector_type: str = "all",
    count: int | None = _DEFAULT_ROW_LIMIT,
    client_factory: QuoteClientFactory = _default_mac_client_factory,
) -> dict[str, Any]:
    """Fetch A-share sector definitions."""
    query = {"sector_type": sector_type, "count": count}
    limit, error = _coerce_positive_limit(count, query=query)
    if error is not None:
        return error
    assert limit is not None
    parsed_type, error = _parse_sector_type(sector_type, query=query)
    if error is not None:
        return error
    assert parsed_type is not None
    try:
        with client_factory() as client:
            df = client.get_board_list(board_type=parsed_type, count=limit)
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)
    return envelope(source="easy_tdx", query=query, rows=dataframe_rows(df))


def a_share_sector_members(
    *,
    sector_symbol: str,
    count: int | None = _DEFAULT_ROW_LIMIT,
    sort_by: str = "change_pct",
    ascending: bool = False,
    client_factory: QuoteClientFactory = _default_mac_client_factory,
) -> dict[str, Any]:
    """Fetch realtime quotes for members in one A-share sector."""
    query = {
        "sector_symbol": sector_symbol,
        "count": count,
        "sort_by": sort_by,
        "ascending": ascending,
    }
    if not sector_symbol.strip():
        return error_envelope("INVALID_SYMBOL", "sector_symbol is required", query=query)
    limit, error = _coerce_positive_limit(count, query=query)
    if error is not None:
        return error
    assert limit is not None
    parsed_sort, error = _parse_member_sort_type(sort_by, query=query)
    if error is not None:
        return error
    assert parsed_sort is not None
    sort_order = SortOrder.ASC if ascending else SortOrder.DESC
    try:
        with client_factory() as client:
            df = client.get_board_members(
                sector_symbol.strip(),
                count=limit,
                sort_type=parsed_sort,
                sort_order=sort_order,
            )
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)
    return envelope(source="easy_tdx", query=query, rows=dataframe_rows(df))


def a_share_sector_ranking(
    *,
    sector_type: str = "industry",
    top_n: int | None = _DEFAULT_RANKING_LIMIT,
    sort_by: str = "change_pct",
    ascending: bool = False,
    client_factory: QuoteClientFactory = _default_mac_client_factory,
) -> dict[str, Any]:
    """Fetch aggregated A-share sector ranking."""
    query = {
        "sector_type": sector_type,
        "top_n": top_n,
        "sort_by": sort_by,
        "ascending": ascending,
    }
    limit, error = _coerce_positive_limit(
        top_n,
        default=_DEFAULT_RANKING_LIMIT,
        maximum=_MAX_RANKING_LIMIT,
        query=query,
    )
    if error is not None:
        return error
    assert limit is not None
    parsed_type, error = _parse_sector_type(sector_type, query=query)
    if error is not None:
        return error
    assert parsed_type is not None
    normalized_sort = sort_by.strip().lower()
    if normalized_sort not in _RANKING_SORT_FIELDS:
        return error_envelope(
            "INVALID_SORT",
            "unsupported A-share sector ranking sort field",
            query=query,
            details={"sort_by": sort_by, "supported": sorted(_RANKING_SORT_FIELDS)},
        )
    try:
        with client_factory() as client:
            df = client.get_board_ranking(
                board_type=parsed_type,
                top_n=limit,
                sort_by=normalized_sort,
                ascending=ascending,
            )
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)
    return envelope(source="easy_tdx", query=query, rows=dataframe_rows(df))


def a_share_market_events(
    *,
    market: str = "SH",
    start: int = 0,
    count: int | None = _DEFAULT_EVENT_LIMIT,
    client_factory: QuoteClientFactory = _default_mac_client_factory,
) -> dict[str, Any]:
    """Fetch A-share unusual market events."""
    query = {"market": market, "start": start, "count": count}
    if start < 0:
        return error_envelope(
            "INVALID_OFFSET",
            "start must be non-negative",
            query=query,
            details={"start": start},
        )
    limit, error = _coerce_positive_limit(
        count,
        default=_DEFAULT_EVENT_LIMIT,
        maximum=_MAX_EVENT_LIMIT,
        query=query,
    )
    if error is not None:
        return error
    assert limit is not None
    market_id, error = _parse_a_share_market(market, query=query)
    if error is not None:
        return error
    assert market_id is not None
    try:
        with client_factory() as client:
            df = client.get_unusual(market_id, start=start, count=limit)
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)
    return envelope(source="easy_tdx", query=query, rows=dataframe_rows(df))


def a_share_market_snapshot(
    *,
    client_factory: SnapshotClientFactory = _default_tdx_client_factory,
) -> dict[str, Any]:
    """Fetch A-share market breadth and capitalization snapshot."""
    query: dict[str, Any] = {}
    try:
        with client_factory() as client:
            df = client.get_market_stat()
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)
    return envelope(source="easy_tdx", query=query, rows=dataframe_rows(df))


def technical_indicator_catalog() -> dict[str, Any]:
    """Return technical indicator metadata without network IO."""
    return envelope(source="easy_tdx", rows=dataframe_rows(pd.DataFrame(list_indicators())))


def a_share_technical_indicators(
    *,
    symbol: str | None = None,
    market: str | None = None,
    code: str | None = None,
    period: str = "DAILY",
    count: int | None = _DEFAULT_INDICATOR_ROW_LIMIT,
    adjust: str = "QFQ",
    indicators: list[str] | None = None,
    params: IndicatorParams | None = None,
    keep_ohlcv: bool = True,
    client_factory: QuoteClientFactory = _default_mac_client_factory,
) -> dict[str, Any]:
    """Fetch A-share K-line bars and calculate technical indicators."""
    query = {
        "symbol": symbol,
        "market": market,
        "code": code,
        "period": period,
        "count": count,
        "adjust": adjust,
        "indicators": indicators or list(_DEFAULT_TECHNICAL_INDICATORS),
        "params": params or {},
        "keep_ohlcv": keep_ohlcv,
    }
    normalized, error = _normalize_single_a_share_symbol(
        symbol=symbol, market=market, code=code, query=query
    )
    if error is not None:
        return error
    assert normalized is not None
    limits, error = _indicator_limits(count, query=query)
    if error is not None:
        return error
    assert limits is not None
    limit, fetch_count = limits
    parsed_period, error = _parse_period(period, query=query)
    if error is not None:
        return error
    assert parsed_period is not None
    parsed_adjust, error = _parse_adjust(adjust, query=query)
    if error is not None:
        return error
    assert parsed_adjust is not None
    indicator_names, error = _normalize_indicator_names(indicators, query=query)
    if error is not None:
        return error
    assert indicator_names is not None
    market_id, parsed_code = normalized

    try:
        with client_factory() as client:
            df = client.get_stock_kline(
                market_id,
                parsed_code,
                period=parsed_period,
                count=fetch_count,
                adjust=parsed_adjust,
            )
        result = compute_indicators(
            df,
            indicator_names,
            params=params or {},
            keep_ohlcv=keep_ohlcv,
            tail=limit,
        )
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except (ValueError, TypeError) as exc:
        return _indicator_error_envelope(exc, query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)

    response = envelope(source="easy_tdx", query=query, rows=dataframe_rows(result))
    response["metadata"] = {
        "fetch_count": fetch_count,
        "warmup_rows": _DEFAULT_INDICATOR_WARMUP_ROWS,
        "indicator_params": params or {},
    }
    return response


def a_share_market_analysis(
    *,
    symbol: str | None = None,
    market: str | None = None,
    code: str | None = None,
    period: str = "DAILY",
    count: int | None = _DEFAULT_INDICATOR_ROW_LIMIT,
    adjust: str = "QFQ",
    indicators: list[str] | None = None,
    params: IndicatorParams | None = None,
    include_quote: bool = True,
    include_kline: bool = True,
    include_indicators: bool = True,
    client_factory: QuoteClientFactory = _default_mac_client_factory,
) -> dict[str, Any]:
    """Return quote, K-line, and indicator blocks for agent analysis."""
    query = {
        "symbol": symbol,
        "market": market,
        "code": code,
        "period": period,
        "count": count,
        "adjust": adjust,
        "indicators": indicators or list(_DEFAULT_ANALYSIS_INDICATORS),
        "params": params or {},
        "include_quote": include_quote,
        "include_kline": include_kline,
        "include_indicators": include_indicators,
    }
    if not (include_quote or include_kline or include_indicators):
        return error_envelope(
            "INVALID_ANALYSIS_REQUEST",
            "at least one analysis block must be requested",
            query=query,
        )
    if not (include_kline or include_indicators):
        return error_envelope(
            "INVALID_ANALYSIS_REQUEST",
            "analysis requires kline or indicators as a core block",
            query=query,
        )
    normalized, error = _normalize_single_a_share_symbol(
        symbol=symbol, market=market, code=code, query=query
    )
    if error is not None:
        return error
    assert normalized is not None
    limits, error = _indicator_limits(count, query=query)
    if error is not None:
        return error
    assert limits is not None
    limit, fetch_count = limits
    parsed_period, error = _parse_period(period, query=query)
    if error is not None:
        return error
    assert parsed_period is not None
    parsed_adjust, error = _parse_adjust(adjust, query=query)
    if error is not None:
        return error
    assert parsed_adjust is not None
    indicator_names: list[str] = []
    if include_indicators:
        parsed_indicator_names, error = _normalize_indicator_names(
            indicators,
            query=query,
            default=_DEFAULT_ANALYSIS_INDICATORS,
        )
        if error is not None:
            return error
        assert parsed_indicator_names is not None
        indicator_names = parsed_indicator_names
    market_id, parsed_code = normalized

    quote_row: dict[str, Any] | None = None
    partial_errors: list[dict[str, Any]] = []

    try:
        with client_factory() as client:
            if include_quote:
                try:
                    quote_rows = dataframe_rows(client.get_stock_quotes([(market_id, parsed_code)]))
                    quote_row = quote_rows[0] if quote_rows else None
                except TdxError as exc:
                    partial_errors.append(_partial_error("TDX_ERROR", str(exc), block="quote"))
                except Exception as exc:
                    partial_errors.append(_partial_error("TOOL_ERROR", str(exc), block="quote"))

            df = client.get_stock_kline(
                market_id,
                parsed_code,
                period=parsed_period,
                count=fetch_count,
                adjust=parsed_adjust,
            )
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query, details={"block": "kline"})
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query, details={"block": "kline"})

    kline_rows = dataframe_rows(df.iloc[-limit:].reset_index(drop=True)) if include_kline else []
    indicator_rows: list[dict[str, Any]] = []
    if include_indicators:
        try:
            indicator_df = compute_indicators(
                df,
                indicator_names,
                params=params or {},
                keep_ohlcv=True,
                tail=limit,
            )
            indicator_rows = dataframe_rows(indicator_df)
        except (ValueError, TypeError) as exc:
            return _error_with_block(_indicator_error_envelope(exc, query=query), "indicators")
        except Exception as exc:
            return error_envelope(
                "TOOL_ERROR",
                str(exc),
                query=query,
                details={"block": "indicators"},
            )

    data: dict[str, Any] = {
        "metadata": {
            "period": period,
            "adjust": adjust,
            "indicator_params": params or {},
            "fetch_count": fetch_count,
            "warmup_rows": _DEFAULT_INDICATOR_WARMUP_ROWS,
            "warning": _ANALYSIS_WARNING,
        }
    }
    if include_quote:
        data["quote"] = quote_row
    if include_kline:
        data["kline"] = {"count": len(kline_rows), "rows": kline_rows}
    if include_indicators:
        data["indicators"] = {"count": len(indicator_rows), "rows": indicator_rows}
    if partial_errors:
        data["errors"] = partial_errors
    return envelope(source="easy_tdx", query=query, data=data)


def hk_realtime_quotes(
    *,
    symbols: list[str] | None = None,
    market: str | None = None,
    code: str | None = None,
    client_factory: HkQuoteClientFactory = _default_hk_client_factory,
) -> dict[str, Any]:
    """Fetch Hong Kong quote rows for known symbols.

    The upstream Hong Kong feed is delayed by 15 minutes; callers should inspect returned
    timestamps or server update fields before treating data as live.
    """
    query = {"symbols": symbols or [], "market": market, "code": code}
    normalized, error = _normalize_hk_symbols(symbols=symbols, market=market, code=code)
    if error is not None:
        return error
    assert normalized is not None
    try:
        with client_factory() as client:
            df = client.goods_quotes(normalized)
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)
    return envelope(source="easy_tdx", query=query, rows=dataframe_rows(df))


def hk_kline_bars(
    *,
    symbol: str | None = None,
    market: str | None = None,
    code: str | None = None,
    period: str = "DAILY",
    count: int | None = _DEFAULT_ROW_LIMIT,
    start: int = 0,
    adjust: str = "NONE",
    client_factory: HkQuoteClientFactory = _default_hk_client_factory,
) -> dict[str, Any]:
    """Fetch Hong Kong K-line bars for one known symbol.

    Intraday Hong Kong bars inherit the 15-minute upstream delay; callers should
    inspect the latest returned datetime when freshness matters.
    """
    query = {
        "symbol": symbol,
        "market": market,
        "code": code,
        "period": period,
        "count": count,
        "start": start,
        "adjust": adjust,
    }
    if start < 0:
        return error_envelope(
            "INVALID_OFFSET",
            "start must be non-negative",
            query=query,
            details={"start": start},
        )
    normalized, error = _normalize_single_hk_symbol(
        symbol=symbol, market=market, code=code, query=query
    )
    if error is not None:
        return error
    assert normalized is not None
    limit, error = _coerce_positive_limit(count, query=query)
    if error is not None:
        return error
    assert limit is not None
    parsed_period, error = _parse_period(period, query=query)
    if error is not None:
        return error
    assert parsed_period is not None
    parsed_adjust, error = _parse_adjust(adjust, query=query)
    if error is not None:
        return error
    assert parsed_adjust is not None
    market_id, parsed_code = normalized
    try:
        with client_factory() as client:
            df = client.goods_kline(
                market_id,
                parsed_code,
                period=parsed_period,
                start=start,
                count=limit,
                adjust=parsed_adjust,
            )
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)
    return envelope(source="easy_tdx", query=query, rows=dataframe_rows(df))


def hk_technical_indicators(
    *,
    symbol: str | None = None,
    market: str | None = None,
    code: str | None = None,
    period: str = "DAILY",
    count: int | None = _DEFAULT_INDICATOR_ROW_LIMIT,
    adjust: str = "QFQ",
    indicators: list[str] | None = None,
    params: IndicatorParams | None = None,
    keep_ohlcv: bool = True,
    client_factory: HkQuoteClientFactory = _default_hk_client_factory,
) -> dict[str, Any]:
    """Fetch Hong Kong K-line bars and calculate technical indicators.

    Indicators computed on intraday Hong Kong bars inherit the 15-minute upstream delay.
    """
    query = {
        "symbol": symbol,
        "market": market,
        "code": code,
        "period": period,
        "count": count,
        "adjust": adjust,
        "indicators": indicators or list(_DEFAULT_TECHNICAL_INDICATORS),
        "params": params or {},
        "keep_ohlcv": keep_ohlcv,
    }
    normalized, error = _normalize_single_hk_symbol(
        symbol=symbol, market=market, code=code, query=query
    )
    if error is not None:
        return error
    assert normalized is not None
    limits, error = _indicator_limits(count, query=query)
    if error is not None:
        return error
    assert limits is not None
    limit, fetch_count = limits
    parsed_period, error = _parse_period(period, query=query)
    if error is not None:
        return error
    assert parsed_period is not None
    parsed_adjust, error = _parse_adjust(adjust, query=query)
    if error is not None:
        return error
    assert parsed_adjust is not None
    indicator_names, error = _normalize_indicator_names(indicators, query=query)
    if error is not None:
        return error
    assert indicator_names is not None
    market_id, parsed_code = normalized

    try:
        with client_factory() as client:
            df = client.goods_kline(
                market_id,
                parsed_code,
                period=parsed_period,
                count=fetch_count,
                adjust=parsed_adjust,
            )
        result = compute_indicators(
            df,
            indicator_names,
            params=params or {},
            keep_ohlcv=keep_ohlcv,
            tail=limit,
        )
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except (ValueError, TypeError) as exc:
        return _indicator_error_envelope(exc, query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)

    response = envelope(source="easy_tdx", query=query, rows=dataframe_rows(result))
    response["metadata"] = {
        "fetch_count": fetch_count,
        "warmup_rows": _DEFAULT_INDICATOR_WARMUP_ROWS,
        "indicator_params": params or {},
    }
    return response


def hk_market_analysis(
    *,
    symbol: str | None = None,
    market: str | None = None,
    code: str | None = None,
    period: str = "DAILY",
    count: int | None = _DEFAULT_INDICATOR_ROW_LIMIT,
    adjust: str = "QFQ",
    indicators: list[str] | None = None,
    params: IndicatorParams | None = None,
    include_quote: bool = True,
    include_kline: bool = True,
    include_indicators: bool = True,
    client_factory: HkQuoteClientFactory = _default_hk_client_factory,
) -> dict[str, Any]:
    """Return Hong Kong quote, K-line, and indicator blocks for agent analysis.

    Hong Kong quote and intraday data are delayed by 15 minutes.
    """
    query = {
        "symbol": symbol,
        "market": market,
        "code": code,
        "period": period,
        "count": count,
        "adjust": adjust,
        "indicators": indicators or list(_DEFAULT_ANALYSIS_INDICATORS),
        "params": params or {},
        "include_quote": include_quote,
        "include_kline": include_kline,
        "include_indicators": include_indicators,
    }
    if not (include_quote or include_kline or include_indicators):
        return error_envelope(
            "INVALID_ANALYSIS_REQUEST",
            "at least one analysis block must be requested",
            query=query,
        )
    if not (include_kline or include_indicators):
        return error_envelope(
            "INVALID_ANALYSIS_REQUEST",
            "analysis requires kline or indicators as a core block",
            query=query,
        )
    normalized, error = _normalize_single_hk_symbol(
        symbol=symbol, market=market, code=code, query=query
    )
    if error is not None:
        return error
    assert normalized is not None
    limits, error = _indicator_limits(count, query=query)
    if error is not None:
        return error
    assert limits is not None
    limit, fetch_count = limits
    parsed_period, error = _parse_period(period, query=query)
    if error is not None:
        return error
    assert parsed_period is not None
    parsed_adjust, error = _parse_adjust(adjust, query=query)
    if error is not None:
        return error
    assert parsed_adjust is not None
    indicator_names: list[str] = []
    if include_indicators:
        parsed_indicator_names, error = _normalize_indicator_names(
            indicators,
            query=query,
            default=_DEFAULT_ANALYSIS_INDICATORS,
        )
        if error is not None:
            return error
        assert parsed_indicator_names is not None
        indicator_names = parsed_indicator_names
    market_id, parsed_code = normalized

    quote_row: dict[str, Any] | None = None
    partial_errors: list[dict[str, Any]] = []

    try:
        with client_factory() as client:
            if include_quote:
                try:
                    quote_rows = dataframe_rows(client.goods_quotes([(market_id, parsed_code)]))
                    quote_row = quote_rows[0] if quote_rows else None
                except TdxError as exc:
                    partial_errors.append(_partial_error("TDX_ERROR", str(exc), block="quote"))
                except Exception as exc:
                    partial_errors.append(_partial_error("TOOL_ERROR", str(exc), block="quote"))

            df = client.goods_kline(
                market_id,
                parsed_code,
                period=parsed_period,
                count=fetch_count,
                adjust=parsed_adjust,
            )
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query, details={"block": "kline"})
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query, details={"block": "kline"})

    kline_rows = dataframe_rows(df.iloc[-limit:].reset_index(drop=True)) if include_kline else []
    indicator_rows: list[dict[str, Any]] = []
    if include_indicators:
        try:
            indicator_df = compute_indicators(
                df,
                indicator_names,
                params=params or {},
                keep_ohlcv=True,
                tail=limit,
            )
            indicator_rows = dataframe_rows(indicator_df)
        except (ValueError, TypeError) as exc:
            return _error_with_block(_indicator_error_envelope(exc, query=query), "indicators")
        except Exception as exc:
            return error_envelope(
                "TOOL_ERROR",
                str(exc),
                query=query,
                details={"block": "indicators"},
            )

    data: dict[str, Any] = {
        "metadata": {
            "period": period,
            "adjust": adjust,
            "indicator_params": params or {},
            "fetch_count": fetch_count,
            "warmup_rows": _DEFAULT_INDICATOR_WARMUP_ROWS,
            "warning": _ANALYSIS_WARNING,
        }
    }
    if include_quote:
        data["quote"] = quote_row
    if include_kline:
        data["kline"] = {"count": len(kline_rows), "rows": kline_rows}
    if include_indicators:
        data["indicators"] = {"count": len(indicator_rows), "rows": indicator_rows}
    if partial_errors:
        data["errors"] = partial_errors
    return envelope(source="easy_tdx", query=query, data=data)


def hk_intraday_timeseries(
    *,
    symbol: str | None = None,
    market: str | None = None,
    code: str | None = None,
    date: int | None = None,
    client_factory: HkQuoteClientFactory = _default_hk_client_factory,
) -> dict[str, Any]:
    """Fetch Hong Kong intraday minute-level time series.

    The upstream Hong Kong feed is delayed by 15 minutes.
    """
    query = {"symbol": symbol, "market": market, "code": code, "date": date}
    normalized, error = _normalize_single_hk_symbol(
        symbol=symbol, market=market, code=code, query=query
    )
    if error is not None:
        return error
    assert normalized is not None
    query_date, error = _parse_query_date(date, query=query)
    if error is not None:
        return error
    market_id, parsed_code = normalized
    try:
        with client_factory() as client:
            df = client.goods_tick_chart(market_id, parsed_code, query_date=query_date)
    except TdxError as exc:
        return error_envelope("TDX_ERROR", str(exc), query=query)
    except Exception as exc:
        return error_envelope("TOOL_ERROR", str(exc), query=query)
    return envelope(source="easy_tdx", query=query, rows=dataframe_rows(df))


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
