"""
MCP Server implementation using FastMCP with robust logging and debug support.
"""

import argparse
import contextlib
import logging
import os
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from src.data import yfinance_client
from src.services import stock_service

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
LOG_FILE = "mcp_server.log"


def setup_logging(debug: bool = False):
    """Set up file-based logging."""
    level = logging.DEBUG if debug else logging.INFO

    if os.path.exists(LOG_FILE):
        with contextlib.suppress(OSError):
            os.remove(LOG_FILE)

    logging.basicConfig(
        filename=LOG_FILE,
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Note: We keep the file open for the duration of the process to capture stderr.
    # ruff: noqa: SIM115
    sys.stderr = open(LOG_FILE, "a", buffering=1)
    logging.info("MCP Server starting...")


# -----------------------------------------------------------------------------
# Server Setup
# -----------------------------------------------------------------------------
mcp = FastMCP("Stock-Analysis")


@mcp.tool()
def search_symbol_tool(query: str) -> dict[str, Any]:
    """
    Search for a stock ticker by company name or query.
    
    Use this if you are not sure about the exact ticker symbol or exchange.
    """
    logging.info(f"Tool call: search_symbol_tool(query={query})")
    try:
        results = yfinance_client.search_symbol(query)
        return {"query": query, "results": results}
    except Exception as e:
        logging.error(f"Error in search_symbol_tool: {str(e)}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def analyze_stock_tool(symbol: str, period: str = "3mo") -> dict[str, Any]:
    """
    Perform a deep dive analysis on a SPECIFIC individual company ticker.
    
    Returns price trends, volatility, key financials (Revenue, Net Income, Margins), 
    analyst recommendations, and current MARKET STATUS (OPEN/CLOSED).
    
    Note: If market_status is 'CLOSED', the data refers to the 'Last Close'.
    """
    logging.info(f"Tool call: analyze_stock_tool(symbol={symbol})")
    try:
        return stock_service.analyze_stock(symbol, period)
    except Exception as e:
        logging.error(f"Error in analyze_stock_tool: {str(e)}", exc_info=True)
        return {"error": str(e), "symbol": symbol}


@mcp.tool()
def get_market_overview_tool() -> dict[str, Any]:
    """
    Show the general market situation (Stockholm, USA, Germany) and USD/SEK rate.
    
    Provides status for major indices and explicitly states if markets are OPEN or CLOSED.
    Always check 'market_status' before describing the market as "up" or "down" today.
    """
    logging.info("Tool call: get_market_overview_tool")
    try:
        return stock_service.get_market_overview()
    except Exception as e:
        logging.error(f"Error in get_market_overview_tool: {str(e)}", exc_info=True)
        return {"error": str(e)}


# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Stock Analysis MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(debug=args.debug)

    try:
        logging.info("Running MCP server on stdio...")
        mcp.run()
    except Exception as e:
        logging.critical(f"Server crashed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
