"""
Formatting utilities for timestamps and data.
"""

import datetime
from typing import Any


def format_timestamp(ts: Any) -> str | None:
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
