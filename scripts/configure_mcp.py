"""Register only this checkout's local stdio adapter; never change user/account config."""
import argparse
import json
from pathlib import Path
import sys
import tomllib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation-core'))
from persistence import atomic_write


def configuration(root,session_file=None):
    root=Path(root).resolve()
    interpreter=root/'.runtime/bridge-venv'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    if not interpreter.is_file():raise ValueError('BLOCKED_BRIDGE_ENV: create .runtime/bridge-venv and install requirements-bridge.txt')
    args=['-B',str(root/'scripts/mcp_server.py')]
    if session_file is not None:
        session_file=Path(session_file).resolve()
        if not session_file.is_relative_to(root/'.runtime'):raise ValueError('PROJECT_RUNTIME_SESSION_REQUIRED')
        if session_file!=root/'.runtime/simulator/session.json':args+=['--session-file',str(session_file)]
    return dict(command=str(interpreter),args=args,
                cwd=str(root),startup_timeout_sec=30,enabled_tools=['get_state','command','probe_bridge'])


def register(root,session_file=None):
    root=Path(root).resolve();target=root/'.codex/config.toml';config=configuration(root,session_file)
    if not target.resolve().is_relative_to(root):raise ValueError('MCP_CONFIG_OUTSIDE_PROJECT')
    old=target.read_text(encoding='utf-8') if target.exists() else ''
    parsed=tomllib.loads(old)
    existing=parsed.get('mcp_servers',{}).get('sovereign_local')
    if existing is not None:
        if existing!=config:raise ValueError('MCP_CONFIG_CONFLICT: existing sovereign_local preserved')
        return 'UNCHANGED'
    section='\n[mcp_servers.sovereign_local]\n'+''.join(
        key+' = '+json.dumps(value,ensure_ascii=False)+'\n' for key,value in config.items())
    new=old.rstrip()+'\n'+section
    tomllib.loads(new)
    atomic_write(target,new.encode('utf-8'))
    return 'REGISTERED_PROJECT_ONLY'


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--session-file',type=Path)
    args=parser.parse_args()
    try:print(json.dumps(dict(status=register(ROOT,args.session_file),scope='this trusted project',provider_calls=0)))
    except (OSError,ValueError) as error:
        print(str(error),file=sys.stderr);raise SystemExit(2)
