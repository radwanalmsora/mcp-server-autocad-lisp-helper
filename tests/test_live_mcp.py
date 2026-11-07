import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SAMPLE_LISP = """
(defun c:draw_box (pt1 pt2 / width height)
  (setvar "CMDECHO" 0)
  (setq width 100)
  (setq unlocalized_var 50)
  (princ "\nDone.")
  (princ)
)
"""

async def main():
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp-server-autocad-lisp-helper"],
    )

    print("\n[1/4] Connecting to MCP Server via stdio...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Initialize
            init_res = await session.initialize()
            print(f"[✓] Connected! Server: {init_res.serverInfo.name} v{init_res.serverInfo.version}")

            # 2. List Tools
            tools = await session.list_tools()
            print(f"\n[2/4] Available Tools ({len(tools.tools)}):")
            for t in tools.tools:
                print(f"  • {t.name}: {t.description.strip().splitlines()[0]}")

            # 3. Call analyze_lisp_syntax
            print("\n[3/4] Calling 'analyze_lisp_syntax'...")
            res_syntax = await session.call_tool("analyze_lisp_syntax", {"code": SAMPLE_LISP})
            print("  Result:", res_syntax.content[0].text)

            # 4. Call check_missing_cleanups
            print("\n[4/4] Calling 'check_missing_cleanups'...")
            res_cleanups = await session.call_tool("check_missing_cleanups", {"code": SAMPLE_LISP})
            print("  Result:", res_cleanups.content[0].text)

    print("\n=======================================================")
    print("ALL LIVE MCP CLIENT-SERVER TESTS COMPLETED SUCCESSFULLY!")
    print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(main())
