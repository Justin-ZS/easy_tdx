"""Business facade for MCP tools.

FastMCP registration stays thin; parsing, conversion, limits, and client
selection live here so they can be tested without starting an MCP transport.
"""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import PackageNotFoundError, version
from types import TracebackType
from typing import Any, Protocol

import pandas as pd  # type: ignore[import-untyped]

from easy_tdx import __version__ as module_version
from easy_tdx.exceptions import TdxError
from easy_tdx.mac.client import MacClient
from easy_tdx.mac.enums import Adjust, Period
from easy_tdx.models.enums import Market

_PACKAGE_NAME = "easy-tdx"
_DEFAULT_ROW_LIMIT = 200
_MAX_ROW_LIMIT = 1000
_MAX_QUOTE_SYMBOLS = 80
_A_SHARE_MARKETS = {
    "SH": Market.SH,
    "SZ": Market.SZ,
    "BJ": Market.BJ,
}
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


QuoteClientFactory = Callable[[], QuoteClient]


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


def _default_mac_client_factory() -> MacClient:
    return MacClient.from_best_host()


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
    symbols = [symbol] if symbol else None
    normalized, error = _normalize_a_share_symbols(symbols=symbols, market=market, code=code)
    if error is not None:
        return error
    assert normalized is not None
    if len(normalized) != 1:
        return error_envelope(
            "INVALID_SYMBOL",
            "K-line query requires exactly one A-share symbol",
            query=query,
        )
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
    market_id, parsed_code = normalized[0]

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
