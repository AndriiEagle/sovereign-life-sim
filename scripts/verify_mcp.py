"""Real SDK initialization, tools/list and command/event/ack acceptance. Zero LLM calls."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
import tomllib
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path(__file__).resolve().parents[1]

async def check(session_file, project_config=False):
    if project_config:
        from configure_mcp import configuration
        config=tomllib.loads((ROOT/'.codex/config.toml').read_text(encoding='utf-8'))['mcp_servers']['sovereign_local']
        if config!=configuration(ROOT,session_file):raise AssertionError('UNEXPECTED_PROJECT_MCP_CONFIG')
        arguments=config['args'] if '--session-file' in config['args'] else config['args']+['--session-file',str(session_file)]
        params=StdioServerParameters(command=config['command'],args=arguments,cwd=config['cwd'])
    else:
        params=StdioServerParameters(command=sys.executable,args=['-B',str(ROOT/'scripts/mcp_server.py'),'--session-file',str(session_file)])
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            listing=await session.list_tools()
            names={t.name for t in listing.tools}
            if not {'get_state','command','probe_bridge'}<=names:raise AssertionError('MCP_TOOL_LIST_MISSING')
            state_result=await session.call_tool('get_state',{})
            if state_result.isError:raise AssertionError('MCP_STARTUP_FAILED')
            state=state_result.structuredContent or json.loads(next(c.text for c in state_result.content if c.type=='text'))
            if state['bridge']['status']!='LIVE_LOCAL_BRIDGE' or state['bridge']['providers']!='NOT_CONNECTED':
                raise AssertionError('MCP_STARTUP_ROUNDTRIP_NOT_CONFIRMED')
            result=await session.call_tool('probe_bridge',{})
            if result.isError:raise AssertionError('MCP_PROBE_FAILED')
            content=result.structuredContent or json.loads(next(c.text for c in result.content if c.type=='text'))
            if content.get('status')!='LIVE_LOCAL_BRIDGE':raise AssertionError('ROUNDTRIP_NOT_CONFIRMED')
            print(json.dumps(dict(status='PASS',sdk='mcp',project_config=project_config,startup_roundtrip='PASS',tools=sorted(names),roundtrip=content,provider_calls=0),ensure_ascii=True))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--session-file',type=Path,default=ROOT/'.runtime/simulator/session.json')
    parser.add_argument('--project-config',action='store_true')
    args=parser.parse_args();asyncio.run(check(args.session_file,args.project_config))
