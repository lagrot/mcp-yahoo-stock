"""
Comprehensive test client to verify market status and all tools.
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

        print("\n--- Testing Market Overview (Status Check) ---")
        await send({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "get_market_overview_tool", "arguments": {}}
        })
        market_res = await receive()
        data = json.loads(market_res["result"]["content"][0]["text"])
        print(f"Market Status: {data['market_status']}")
        print(f"Last Trading Day: {data['last_trading_day']}")

        print("\n--- Testing Stock Analysis (NVDA Status) ---")
        await send({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "analyze_stock_tool", "arguments": {"symbol": "NVDA"}}
        })
        stock_res = await receive()
        data = json.loads(stock_res["result"]["content"][0]["text"])
        print(f"NVDA Market Status: {data['market_status']}")
        print(f"Last Trade Date: {data['last_trade_date']}")

    finally:
        process.terminate()
        await process.wait()

if __name__ == "__main__":
    asyncio.run(run_test())
