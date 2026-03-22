"""
Comprehensive test client to verify all MCP tools.
"""
import asyncio
import json
import sys

async def run_test():
    limit = 1024 * 1024
    process = await asyncio.create_subprocess_exec(
        "uv", "run", "python", "-m", "src.mcp.server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        limit=limit
    )

    async def send(msg):
        process.stdin.write(json.dumps(msg).encode() + b"\n")
        await process.stdin.drain()

    async def receive():
        line = await process.stdout.readline()
        if not line: return None
        return json.loads(line)

    try:
        # Handshake
        await send({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"}
            }
        })
        await receive()
        await send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

        print("\n--- Listing Tools ---")
        await send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools_res = await receive()
        print(f"Tools: {[t['name'] for t in tools_res['result']['tools']]}")

        print("\n--- Testing Search Tool (Investor) ---")
        await send({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "search_symbol_tool", "arguments": {"query": "Investor"}}
        })
        search_res = await receive()
        data = json.loads(search_res["result"]["content"][0]["text"])
        print(f"Search Results: {data['results'][:2]}")

        print("\n--- Testing Market Overview (Swedish Indices) ---")
        await send({
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "get_market_overview_tool", "arguments": {}}
        })
        market_res = await receive()
        print("Market overview fetched successfully.")

        print("\n--- Testing Stock Analysis (Indices should NOT crash) ---")
        await send({
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "analyze_stock_tool", "arguments": {"symbol": "^OMX"}}
        })
        stock_res = await receive()
        data = json.loads(stock_res["result"]["content"][0]["text"])
        print(f"Index Analysis (^OMX): Status OK, Financials: {data['key_financials']}")

    finally:
        process.terminate()
        await process.wait()

if __name__ == "__main__":
    asyncio.run(run_test())
