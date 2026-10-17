"""Real SDK initialization, tools/list and command/event/ack acceptance. Zero LLM calls."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path(__file__).resolve().parents[1]

async def check(session_file):
    params=StdioServerParameters(command=sys.executable,args=['-B',str(ROOT/'scripts/mcp_server.py'),'--session-file',str(session_file)])
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            listing=await session.list_tools()
            names={t.name for t in listing.tools}
            if not {'get_state','command','probe_bridge'}<=names:raise AssertionError('MCP_TOOL_LIST_MISSING')
            result=await session.call_tool('probe_bridge',{})
            if result.isError:raise AssertionError('MCP_PROBE_FAILED')
            content=result.structuredContent or json.loads(next(c.text for c in result.content if c.type=='text'))
            if content.get('status')!='LIVE_LOCAL_BRIDGE':raise AssertionError('ROUNDTRIP_NOT_CONFIRMED')
            print(json.dumps(dict(status='PASS',sdk='mcp',tools=sorted(names),roundtrip=content,provider_calls=0),ensure_ascii=True))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--session-file',type=Path,default=ROOT/'.runtime/simulator/session.json')
    asyncio.run(check(parser.parse_args().session_file))
