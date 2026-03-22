from src.mcp.tools import analyze_stock_tool


TOOLS = {
    "analyze_stock": analyze_stock_tool,
}

def safe_json_dumps(obj):
    import json

    def default(o):
        if hasattr(o, "isoformat"):
            return o.isoformat()
        if hasattr(o, "item"):
            return o.item()
        return str(o)

    return json.dumps(obj, default=default)

def handle_request(request: dict):
    tool = request.get("tool")
    args = request.get("args", {})

    if tool not in TOOLS:
        return {"error": f"Unknown tool: {tool}"}

    return TOOLS[tool](args)


if __name__ == "__main__":
    import json
    import sys

    for line in sys.stdin:
        request = json.loads(line)
        response = handle_request(request)
        print(safe_json_dumps(response), flush=True)
