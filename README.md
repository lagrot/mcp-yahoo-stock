# Stock MCP (Yahoo Finance + Claude)

A minimal, local MCP server for stock analysis using Yahoo Finance and Claude.

---

## 🚀 Features

* 📈 Historical stock prices
* 💾 SQLite caching (fast + persistent)
* 📊 Financial statements
* 🧠 Analyst recommendations
* 📰 News + basic sentiment analysis
* ⚡ AI-optimized summary output

---

## 🧱 Architecture

```text
src/
  data/        # Data fetching + caching
  services/    # Analysis logic
  mcp/         # MCP server
```

---

## ⚙️ Setup

```bash
uv venv
source .venv/bin/activate

uv add yfinance pydantic
```

---

## ▶️ Run

```bash
uv run python -m src.mcp.server
```

---

## 🧪 Example Request

```json
{"tool": "analyze_stock", "args": {"symbol": "AAPL"}}
```

---

## 📊 Output (Example)

```json
{
  "symbol": "AAPL",
  "summary": {
    "latest_close": 277.85,
    "price_change_percent": 2.3,
    "trend": "up",
    "average_volume": 50000000,
    "volatility": 0.012,
    "news_sentiment": "positive"
  }
}
```

---

## 💾 Caching

* Uses SQLite (`cache.db`)
* Caches historical prices only
* Automatically refreshes if data is older than 1 day

---

## 🧠 Design Philosophy

* Keep tools minimal
* Return structured insights (not raw data)
* Let Claude handle reasoning

---

## ⚠️ Limitations

* Uses unofficial Yahoo Finance API
* Data may be delayed or incomplete
* Not suitable for trading systems

---

## 🛠️ Roadmap

* [ ] Market overview tool
* [ ] Better financial metrics (revenue, profit)
* [ ] Technical indicators (RSI, SMA)
* [ ] Multi-stock comparison

---

## 🤖 Usage with Claude

Ask things like:

* "Analyze Apple stock"
* "Is Tesla trending up?"
* "What do analysts think about Nvidia?"

Claude will:

1. Call MCP tool
2. Interpret structured data
3. Provide insights

---

## 📄 License

MIT

