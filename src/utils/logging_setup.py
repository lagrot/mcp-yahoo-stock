"""
Centralized logging configuration.
"""

import contextlib
import logging
import os
import sys

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
    # In this specific context, assigning to sys.stderr is a standard practice for redirection.
    # ruff: noqa: SIM115
    sys.stderr = open(LOG_FILE, "a", buffering=1)
    logging.info("MCP Server starting...")
