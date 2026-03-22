import yfinance as yf
import datetime
from src.data.cache import get_cached_history, save_history, init_db

# -------------------------
# Internal helpers
# -------------------------

def _serialize_value(value):
    """Convert pandas/numpy types into JSON-safe values."""
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


def _serialize_records(records: list[dict]) -> list[dict]:
    """Serialize list of dicts."""
    return [
        {k: _serialize_value(v) for k, v in row.items()}
        for row in records
    ]


def _serialize_dict(data: dict) -> dict:
    """Serialize nested dict (for financials) with safe keys + values."""
    serialized = {}

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


# -------------------------
# Public API
# -------------------------

def get_ticker(symbol: str):
    return yf.Ticker(symbol)

def get_history(symbol: str, period: str = "3mo"):
    init_db()

    # 1. Try cache
    cached = get_cached_history(symbol)

    if cached:
        last_date = cached[-1]["Date"]
        try:
            last_date_obj = datetime.datetime.fromisoformat(last_date)
            # If data is less than 1 day old → use cache
            # Note: yfinance history often has timezone info
            now = datetime.datetime.now(last_date_obj.tzinfo) if last_date_obj.tzinfo else datetime.datetime.now()
            if (now - last_date_obj).days < 1:
                return cached
        except (ValueError, TypeError):
            # If date parsing fails, just fetch fresh
            pass

    # 2. Fetch from Yahoo
    ticker = get_ticker(symbol)
    df = ticker.history(period=period)

    if df.empty:
        raise ValueError(f"No historical data for {symbol}")

    records = df.reset_index().to_dict(orient="records")
    records = _serialize_records(records)

    # 3. Save to cache
    save_history(symbol, records)

    return records

def get_financials(symbol: str):
    ticker = get_ticker(symbol)

    income_stmt = ticker.financials
    balance_sheet = ticker.balance_sheet

    return {
        "income_statement": _serialize_dict(income_stmt.to_dict())
        if not income_stmt.empty else {},
        "balance_sheet": _serialize_dict(balance_sheet.to_dict())
        if not balance_sheet.empty else {},
    }


def get_recommendations(symbol: str):
    ticker = get_ticker(symbol)
    recs = ticker.recommendations

    if recs is None or recs.empty:
        return []

    records = recs.tail(10).reset_index().to_dict(orient="records")
    return _serialize_records(records)


def get_news(symbol: str):
    ticker = get_ticker(symbol)
    news = ticker.news or []

    # news is already mostly JSON-safe, but normalize anyway
    return [
        {k: _serialize_value(v) for k, v in item.items()}
        for item in news
    ]
