"""
Core business logic for stock analysis and market overviews.
"""

import datetime
import logging
from typing import Any

from src.data import yfinance_client as yf_client


def _format_timestamp(ts: Any) -> str | None:
    """Safely convert various timestamp formats to ISO string."""
    if not ts:
        return None
    try:
        if isinstance(ts, (int, float)):
            return datetime.datetime.fromtimestamp(ts).isoformat()
        if hasattr(ts, "isoformat"):
            return ts.isoformat()
    except Exception:
        pass
    return str(ts)


def _extract_financial_metrics(financials: dict[str, Any]) -> dict[str, Any]:
    """
    Extract key metrics (Revenue, Net Income, Margins) from raw financials.
    """
    metrics = {
        "revenue": None,
        "net_income": None,
        "profit_margin_pct": None,
    }

    income_stmt = financials.get("income_statement", {})
    if not income_stmt:
        return metrics

    # Financials are keyed by date. We want the most recent one.
    dates = sorted(income_stmt.keys(), reverse=True)
    if not dates:
        return metrics

    latest_date = dates[0]
    latest_data = income_stmt[latest_date]

    # Map Yahoo's various naming conventions
    revenue = latest_data.get("Total Revenue") or latest_data.get("Operating Revenue")
    net_income = latest_data.get("Net Income")

    metrics["revenue"] = revenue
    metrics["net_income"] = net_income

    if revenue and net_income and revenue != 0:
        metrics["profit_margin_pct"] = round((net_income / revenue) * 100, 2)

    return metrics


def analyze_stock(symbol: str, period: str = "3mo") -> dict[str, Any]:
    """
    Perform a comprehensive analysis of a stock symbol.
    """
    logging.info(f"Analyzing stock: {symbol}")
    
    # 1. Fetch raw data + Market status
    history = yf_client.get_history(symbol, period)
    financials = yf_client.get_financials(symbol)
    recommendations = yf_client.get_recommendations(symbol)
    news = yf_client.get_news(symbol)
    market_info = yf_client.get_market_info(symbol)
    
    currency = market_info.get("currency", "USD")

    # 2. Extract price data
    closes = [row["Close"] for row in history if "Close" in row]
    if not closes:
        raise ValueError(f"No price data available for {symbol}")

    latest_close = closes[-1]
    first_close = closes[0]

    # Basic calculations
    price_change = latest_close - first_close
    price_change_pct = (price_change / first_close) * 100
    
    # 3. Currency Conversion (USD to SEK)
    sek_data = {}
    if currency == "USD":
        try:
            usdsek_rate = yf_client.get_current_price("USDSEK=X")
            sek_data = {
                "latest_close_sek": round(latest_close * usdsek_rate, 2),
                "usdsek_rate": round(usdsek_rate, 4)
            }
        except Exception as e:
            logging.error(f"Failed to fetch USDSEK rate: {e}")

    # 4. Financial extraction
    key_metrics = _extract_financial_metrics(financials)

    # 5. Simple sentiment
    positive_keywords = {"gain", "growth", "beat", "strong", "upgrade", "success"}
    sentiment_score = 0
    for article in news:
        title = article.get("title", "").lower()
        if any(k in title for k in positive_keywords):
            sentiment_score += 1

    return {
        "symbol": symbol.upper(),
        "currency": currency,
        "market_status": market_info.get("market_state", "CLOSED"),
        "last_trade_date": _format_timestamp(market_info.get("last_trade_time")),
        "summary": {
            "latest_close": round(latest_close, 2),
            "price_change_percent": round(price_change_pct, 2),
            "trend": "up" if price_change > 0 else "down",
            "news_sentiment": "positive" if sentiment_score > 0 else "neutral",
            **sek_data
        },
        "key_financials": key_metrics,
        "analyst_summary": {
            "total_recommendations": len(recommendations),
            "top_recs": recommendations[:3],
        },
        "recent_news": news[:3],
    }


def get_market_overview() -> dict[str, Any]:
    """
    Fetch status of major global and local (Swedish) indices.
    """
    indices = {
        "^OMX": "OMX Stockholm 30",
        "^OMXSPI": "OMX Stockholm PI",
        "^OMXSGI": "OMX Stockholm GI",
        "^GSPC": "S&P 500",
        "^IXIC": "Nasdaq Composite",
        "^GDAXI": "DAX (Germany)",
        "USDSEK=X": "USD/SEK Exchange Rate",
    }

    overview = []
    # Check OMX to get the general market state for the overview
    omx_info = yf_client.get_market_info("^OMX")
    
    for symbol, name in indices.items():
        try:
            # Get 5 days of history to calculate 1-day change
            history = yf_client.get_history(symbol, period="5d")
            if len(history) >= 2:
                latest = history[-1]["Close"]
                prev = history[-2]["Close"]
                change_pct = ((latest - prev) / prev) * 100
                
                overview.append({
                    "name": name,
                    "symbol": symbol,
                    "price": round(latest, 2),
                    "change_percent": round(change_pct, 2)
                })
        except Exception as e:
            logging.error(f"Failed to fetch index {symbol}: {e}")

    return {
        "market_status": omx_info.get("market_state", "CLOSED"),
        "last_trading_day": _format_timestamp(omx_info.get("last_trade_time")),
        "market_indices": overview
    }
