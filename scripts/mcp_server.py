"""Official MCP SDK stdio adapter to the single local simulation command bus."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'mcp-bridge'))
from client import LocalClient
from mcp.server.fastmcp import FastMCP

parser=argparse.ArgumentParser()
parser.add_argument('--session-file',type=Path,default=ROOT/'.runtime/simulator/session.json')
args=parser.parse_args()
client=LocalClient(args.session_file)
mcp=FastMCP('Sovereign Local Simulator')

@mcp.tool()
def get_state() -> dict:
    """Read the local synthetic scenario, with provider and sandbox capability status."""
    return client.call('get_state')

@mcp.tool()
def command(name: str, payload: dict, request_id: str) -> dict:
    """Apply one allowlisted local scenario command with a stable idempotency key. No shell or external effects."""
    if name not in {'tick','select_node','update_params','configure_node','node_status','activate_quest','verify_milestone','forge_rule','rollback_rule','regenerate_asset','game_theory'}:
        raise ValueError('UNKNOWN_LOCAL_COMMAND')
    return client.call(name,payload,request_id)

@mcp.tool()
def probe_bridge() -> dict:
    """Observe a real command/event roundtrip, then acknowledge it; no LLM is called."""
    return client.probe()

if __name__=='__main__':mcp.run(transport='stdio')
