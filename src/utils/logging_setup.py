"""
Centralized logging configuration.
"""

import contextlib
import logging
import os
import sys

LOG_FILE = "mcp_server.log"


def setup_logging(debug: bool = False):
    """Set up logging to both file and stderr."""
    level = logging.DEBUG if debug else logging.INFO

    # Remove existing log file if it exists to start fresh
    if os.path.exists(LOG_FILE):
        with contextlib.suppress(OSError):
            os.remove(LOG_FILE)

    # Create formatters and handlers
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)

    # Stream handler (logging to stderr is safe for MCP)
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Avoid adding duplicate handlers if setup_logging is called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)

    logging.info("MCP Server starting...")
