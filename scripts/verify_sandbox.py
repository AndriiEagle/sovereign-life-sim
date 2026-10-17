"""Probe real isolation separately; absence is BLOCKED, never a synthetic PASS."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ai-architect'))
from sandbox import Sandbox

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,default=ROOT/'.runtime/simulator/sandbox.json')
    sandbox=Sandbox(parser.parse_args().config)
    if sandbox.status!='READY':print(json.dumps(sandbox.report()));return 2
    expected=[{'op':'set_modifier','name':'confidence_assumption','value':50}]
    source='def evaluate(state, params, seed):\n    return '+repr(expected)+'\n'
    if sandbox.evaluate(source,{},42)!=expected:raise AssertionError('SANDBOX_OUTPUT_MISMATCH')
    try:sandbox.evaluate('def evaluate(state, params, seed):\n    while True: pass\n',{},42)
    except ValueError:pass
    else:raise AssertionError('SANDBOX_TIMEOUT_NOT_ENFORCED')
    print(json.dumps({'status':'PASS','isolation':sandbox.report(),'provider_calls':0}));return 0

if __name__=='__main__':raise SystemExit(main())
