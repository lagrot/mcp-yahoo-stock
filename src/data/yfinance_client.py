"""
Yahoo Finance API client with serialization helpers and caching.
"""

import datetime
from typing import Any

import yfinance as yf

from src.data.cache import get_cached_history, init_db, save_history


def _serialize_value(value: Any) -> Any:
    """
    Convert pandas/numpy types into JSON-safe values.

    This ensures compatibility with the MCP JSON-RPC protocol.
    """
    try:
        # pandas Timestamp → ISO string
        if hasattr(value, "isoformat"):
            return value.isoformat()

        # numpy types → native Python
        if hasattr(value, "item"):
            return value.item()

    except Exception:
        pass

    return value


def _serialize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Serialize a list of dictionaries for JSON compatibility."""
    return [{k: _serialize_value(v) for k, v in row.items()} for row in records]


def _serialize_dict(data: dict[Any, dict[Any, Any]]) -> dict[str, dict[str, Any]]:
    """
    Serialize nested dictionaries (used for financial statements).

    Handles non-string keys and complex values found in pandas outputs.
    """
    serialized: dict[str, dict[str, Any]] = {}

    for outer_key, inner_dict in data.items():
        safe_outer_key = str(outer_key)
        serialized[safe_outer_key] = {}

        for inner_key, value in inner_dict.items():
            # Convert Timestamp keys → string
            if hasattr(inner_key, "isoformat"):
                safe_inner_key = inner_key.isoformat()
            else:
                safe_inner_key = str(inner_key)
            serialized[safe_outer_key][safe_inner_key] = _serialize_value(value)

    return serialized


def get_ticker(symbol: str) -> yf.Ticker:
    """Return a yfinance Ticker object for the given symbol."""
    return yf.Ticker(symbol)


def get_current_price(symbol: str) -> float:
    """Fetch the latest price for a symbol (e.g., 'USDSEK=X')."""
    ticker = get_ticker(symbol)
    # Use fast_info if available, otherwise history
    try:
        return ticker.fast_info["lastPrice"]
    except Exception:
        df = ticker.history(period="1d")
        if df.empty:
            raise ValueError(f"Could not fetch price for {symbol}")
        return float(df["Close"].iloc[-1])


def get_market_info(symbol: str) -> dict[str, Any]:
    """Fetch market state and last trading time for a symbol."""
    ticker = get_ticker(symbol)
    try:
        # ticker.info is more reliable than fast_info for metadata on some systems
        info = ticker.info
        return {
            "market_state": info.get("marketState", "CLOSED"),
            "last_trade_time": info.get("regularMarketTime"),
            "currency": info.get("currency", "USD")
        }
    except Exception:
        return {"market_state": "CLOSED", "last_trade_time": None, "currency": "USD"}


def get_history(symbol: str, period: str = "3mo") -> list[dict[str, Any]]:
    """
    Fetch historical price data with SQLite caching.

    Refreshes automatically if the cached data is older than 1 day.
    """
    init_db()

    # 1. Check local cache
    cached = get_cached_history(symbol)
    if cached:
        last_date_str = cached[-1].get("Date")
        if last_date_str:
            try:
                last_date = datetime.datetime.fromisoformat(last_date_str)
                # Compare aware/naive dates safely
                now = (
                    datetime.datetime.now(last_date.tzinfo)
                    if last_date.tzinfo
                    else datetime.datetime.now()
                )
                if (now - last_date).days < 1:
                    return cached
            except (ValueError, TypeError):
                pass

    # 2. Fetch fresh data from Yahoo Finance
    ticker = get_ticker(symbol)
    df = ticker.history(period=period)

    if df.empty:
        raise ValueError(f"No historical data available for symbol: {symbol}")

    # Reset index to include 'Date' as a column, then serialize
    records = df.reset_index().to_dict(orient="records")
    serialized_records = _serialize_records(records)

    # 3. Update cache
    save_history(symbol, serialized_records)

    return serialized_records


def get_financials(symbol: str) -> dict[str, Any]:
    """Fetch income statement and balance sheet data."""
    ticker = get_ticker(symbol)

    try:
        income_stmt = ticker.financials
        balance_sheet = ticker.balance_sheet
    except Exception:
        # Indices and some small caps don't have fundamentals
        return {"income_statement": {}, "balance_sheet": {}}

    return {
        "income_statement": (
            _serialize_dict(income_stmt.to_dict()) if not income_stmt.empty else {}
        ),
        "balance_sheet": (
            _serialize_dict(balance_sheet.to_dict()) if not balance_sheet.empty else {}
        ),
    }


def get_recommendations(symbol: str) -> list[dict[str, Any]]:
    """Fetch recent analyst recommendations."""
    ticker = get_ticker(symbol)
    recs = ticker.recommendations

    if recs is None or recs.empty:
        return []

    # Get the 10 most recent recommendations
    records = recs.tail(10).reset_index().to_dict(orient="records")
    return _serialize_records(records)


def get_news(symbol: str) -> list[dict[str, Any]]:
    """Fetch recent news articles for the given symbol."""
    ticker = get_ticker(symbol)
    news = ticker.news or []

    return [{k: _serialize_value(v) for k, v in item.items()} for item in news]


def search_symbol(query: str) -> list[dict[str, Any]]:
    """Search for a stock ticker by company name or query."""
    # Use yfinance's internal search helper
    import requests

    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=5"
        res = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        )
        res.raise_for_status()
        data = res.json()
        
        # Format the relevant results
        results = []
        for quote in data.get("quotes", []):
            results.append({
                "symbol": quote.get("symbol"),
                "name": quote.get("shortname") or quote.get("longname"),
                "exchange": quote.get("exchange"),
                "type": quote.get("quoteType")
            })
        return results
    except Exception as e:
        import logging
        logging.error(f"Search failed for {query}: {e}")
        return []
