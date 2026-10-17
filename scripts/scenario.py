"""Exercise the copied pure game-forge seam with synthetic inputs, not a personal twin."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'simulation-core'))
from unified_tick import initial_state, advance


def main():
    parser = argparse.ArgumentParser(description='Synthetic game-forge resource trajectory; no real-world prediction.')
    parser.add_argument('--ticks', type=int, default=96)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--action', choices=['rest', 'sleep', 'work'], default='rest')
    args = parser.parse_args()
    if not 1 <= args.ticks <= 10000:
        parser.error('--ticks must be in 1..10000')
    manifest=json.loads((ROOT/'CONTEXT_MANIFEST.json').read_text(encoding='utf-8'))
    state = initial_state(manifest, seed=args.seed)
    start = {key: state['life'][key] for key in ('tick', 'energy', 'burnout', 'balance_cents')}
    remaining=args.ticks
    while remaining:
        count=min(remaining,672);state=advance(state,count,args.action);remaining-=count
    print(json.dumps({'status': 'SYNTHETIC_NOT_PERSONAL_OR_FORECAST', 'source': 'unified_tick + game-forge + Conductor',
                     'start': start, 'finish': {key: state['life'][key] for key in start},
                     'action': args.action, 'real_payment': 'NOT_CONNECTED'}, indent=2))


if __name__ == '__main__':
    main()
