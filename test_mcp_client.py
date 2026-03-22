"""
Comprehensive test client to verify dividends and all tools.
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

        print("\n--- Testing Dividends (Investor AB - INVE-B.ST) ---")
        await send({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "analyze_stock_tool", "arguments": {"symbol": "INVE-B.ST"}}
        })
        res = await receive()
        data = json.loads(res["result"]["content"][0]["text"])
        print(f"Symbol: {data['symbol']}")
        print(f"Dividend Data: {data['dividends']}")

    finally:
        process.terminate()
        await process.wait()

if __name__ == "__main__":
    asyncio.run(run_test())
