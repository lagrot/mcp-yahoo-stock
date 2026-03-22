# Stock MCP (Yahoo Finance + Claude/Gemini)

A local Model Context Protocol (MCP) server for stock analysis using Yahoo Finance and official SDKs. This server provides tools for LLMs (like Claude or Gemini) to fetch market data, financials, and sentiment analysis directly.

---

## 🚀 Features

* 📈 Historical stock prices
* 💾 SQLite caching (fast + persistent)
* 📊 Financial statements
* 🧠 Analyst recommendations
* 📰 News + basic sentiment analysis
* ⚡ AI-optimized summary output
* 🛠️ Official MCP SDK (Compatible with Claude Desktop & Gemini CLI)

---

## 🧱 Architecture

```text
src/
  data/        # Data fetching + caching
  services/    # Analysis logic
  mcp/         # MCP server (Standard JSON-RPC 2.0)
```

---

## ⚙️ Setup

```bash
# Install dependencies
uv sync
```

---

## 🧪 Standalone Testing (WSL / Linux)

Since this is an MCP server, it communicates via `stdin` and `stdout` using JSON-RPC 2.0. To verify the server is working correctly without an LLM client, use the included test script:

```bash
# Run the automated test client
uv run python test_mcp_client.py
```

This script performs the standard MCP handshake, lists tools, and calls the `analyze_stock_tool` for AAPL.

---

## 🤖 Usage with Gemini CLI

To use this with the [Gemini CLI](https://github.com/google/gemini-cli), add it as an MCP tool:

```bash
gemini mcp add stock-analysis "uv run python -m src.mcp.server" --trust -s project
```

Then, you can simply ask:
* "Analyze Apple stock"
* "How is NVIDIA performing compared to its recent history?"

---

## 🤖 Usage with Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/path/to/stock-mcp",
        "python",
        "-m",
        "src.mcp.server"
      ]
    }
  }
}
```

---

## 💾 Caching & Database

* **SQLite:** This project uses a local SQLite database (`cache.db`) for caching. You **do not** need to install SQLite on your system manually; it is included in the Python standard library.
* **Logic:** Caches historical prices only and refreshes data older than 1 day.

---

## 🛠️ Development

This project uses **Ruff** for linting and formatting.

```bash
# Check for issues
uv run ruff check .

# Fix and format
uv run ruff check --fix .
uv run ruff format .
```

---

## ⚠️ Limitations

* Uses unofficial Yahoo Finance API (`yfinance`)
* Data may be delayed or incomplete
* Not suitable for high-frequency trading

---

## 📄 License

MIT
