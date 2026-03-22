"""
MCP Server implementation using FastMCP with robust logging and debug support.
"""

import argparse
import logging
import os
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from src.services.stock_service import analyze_stock

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
# We log to a file because stdout is reserved for the MCP protocol.
LOG_FILE = "mcp_server.log"

def setup_logging(debug: bool = False):
    """Set up file-based logging."""
    level = logging.DEBUG if debug else logging.INFO
    
    # Ensure the log file is recreatable
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except OSError:
            pass

    logging.basicConfig(
        filename=LOG_FILE,
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Redirect stderr to the log file as well to catch low-level crashes
    sys.stderr = open(LOG_FILE, "a", buffering=1)
    
    logging.info("MCP Server starting...")
    if debug:
        logging.debug("Debug mode enabled.")

# -----------------------------------------------------------------------------
# Server Setup
# -----------------------------------------------------------------------------
# Initialize FastMCP server
mcp = FastMCP("Stock-Analysis")

@mcp.tool()
def analyze_stock_tool(symbol: str, period: str = "3mo") -> dict[str, Any]:
    """
    Perform a comprehensive analysis of a stock ticker symbol.
    
    Returns recent price trends, volatility, financial statements, analyst 
    recommendations, and basic news sentiment analysis.
    
    Args:
        symbol: The stock ticker symbol to analyze (e.g., 'AAPL', 'TSLA', 'MSFT').
        period: The historical time range to analyze (e.g., '1mo', '3mo', '1y', '5y').
    """
    logging.info(f"Tool call: analyze_stock_tool(symbol={symbol}, period={period})")
    try:
        result = analyze_stock(symbol, period)
        logging.info("Analysis successful.")
        return result
    except Exception as e:
        logging.error(f"Error in analyze_stock_tool: {str(e)}", exc_info=True)
        return {"error": str(e), "symbol": symbol}

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
