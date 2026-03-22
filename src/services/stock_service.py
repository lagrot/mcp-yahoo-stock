from src.data import yfinance_client as yf_client


def analyze_stock(symbol: str, period: str = "3mo"):
    history = yf_client.get_history(symbol, period)
    financials = yf_client.get_financials(symbol)
    recommendations = yf_client.get_recommendations(symbol)
    news = yf_client.get_news(symbol)

    closes = [row["Close"] for row in history if "Close" in row]
    volumes = [row.get("Volume", 0) for row in history]

    if not closes:
        raise ValueError("No price data available")

    latest_close = closes[-1]
    first_close = closes[0]

    # --- Metrics ---
    price_change = latest_close - first_close
    price_change_pct = (price_change / first_close) * 100

    trend = "up" if price_change > 0 else "down"

    avg_volume = sum(volumes) / len(volumes)

    # --- Volatility (simple but useful) ---
    returns = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        curr = closes[i]
        returns.append((curr - prev) / prev)

    volatility = sum(abs(r) for r in returns) / len(returns) if returns else 0

    # --- Analyst sentiment (very basic) ---
    analyst_summary = {
        "total": len(recommendations),
        "recent": recommendations[:3],
    }

    # --- News sentiment (very naive MVP) ---
    positive_keywords = ["gain", "growth", "beat", "strong", "upgrade"]
    negative_keywords = ["loss", "drop", "weak", "downgrade", "miss"]

    sentiment_score = 0

    for article in news:
        title = article.get("title", "").lower()

        if any(k in title for k in positive_keywords):
            sentiment_score += 1
        if any(k in title for k in negative_keywords):
            sentiment_score -= 1

    sentiment = "positive" if sentiment_score > 0 else "negative" if sentiment_score < 0 else "neutral"

    return {
        "symbol": symbol,

        # 🔥 THIS is what Claude will rely on
        "summary": {
            "latest_close": latest_close,
            "price_change": price_change,
            "price_change_percent": price_change_pct,
            "trend": trend,
            "average_volume": avg_volume,
            "volatility": volatility,
            "news_sentiment": sentiment,
        },

        # trimmed data
        "history": history[-20:],
        "analyst_summary": analyst_summary,
        "top_news": news[:5],

        # keep raw for deeper reasoning
        "financials": financials,
    }
