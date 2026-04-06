"""
Centralized logging configuration.
"""

import contextlib
import logging
import os
import sys
from pathlib import Path

# Get the project root relative to this file's location
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
LOG_FILE = PROJECT_ROOT / "mcp_server.log"


class FlushHandler(logging.FileHandler):
    """KISS: A FileHandler that flushes after every emit."""
    def emit(self, record):
        super().emit(record)
        self.flush()


def setup_logging(debug: bool = False):
    """Set up logging to both file and stderr with zero buffering."""
    level = logging.DEBUG if debug else logging.INFO

    # Use basicConfig for the absolute simplest root logger setup
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            FlushHandler(LOG_FILE, mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stderr)
        ],
        force=True
    )
    
    # Silence extremely noisy libraries even in debug mode
    logging.getLogger("yfinance").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("mcp").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.info("--- mcp-yahoo-stock: Session Started ---")
