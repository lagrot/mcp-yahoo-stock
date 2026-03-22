"""
JSON serialization helpers for Pandas and NumPy types.
"""

from typing import Any


def serialize_value(value: Any) -> Any:
    """
    Convert pandas/numpy types into JSON-safe values.

    This ensures compatibility with the MCP JSON-RPC protocol.
    """
    try:
        # pandas Timestamp → ISO string
        if hasattr(value, "isoformat"):
            return value.isoformat()

        # numpy types → native Python
        if hasattr(value, "item"):
            return value.item()

    except Exception:
        pass

    return value


def serialize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Serialize a list of dictionaries for JSON compatibility."""
    return [{k: serialize_value(v) for k, v in row.items()} for row in records]


def serialize_dict(data: dict[Any, dict[Any, Any]]) -> dict[str, dict[str, Any]]:
    """
    Serialize nested dictionaries (used for financial statements).

    Handles non-string keys and complex values found in pandas outputs.
    """
    serialized: dict[str, dict[str, Any]] = {}

    for outer_key, inner_dict in data.items():
        safe_outer_key = str(outer_key)
        serialized[safe_outer_key] = {}

        for inner_key, value in inner_dict.items():
            # Convert Timestamp keys → string
            if hasattr(inner_key, "isoformat"):
                safe_inner_key = inner_key.isoformat()
            else:
                safe_inner_key = str(inner_key)
            serialized[safe_outer_key][safe_inner_key] = serialize_value(value)

    return serialized
