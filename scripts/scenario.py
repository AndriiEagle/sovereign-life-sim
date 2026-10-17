"""Exercise the copied pure game-forge seam with synthetic inputs, not a personal twin."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'simulation-core/game-forge'))
from sim.core import initial_state, load_params, step


def main():
    parser = argparse.ArgumentParser(description='Synthetic game-forge resource trajectory; no real-world prediction.')
    parser.add_argument('--ticks', type=int, default=96)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--action', choices=['rest', 'sleep', 'work'], default='rest')
    args = parser.parse_args()
    if not 1 <= args.ticks <= 10000:
        parser.error('--ticks must be in 1..10000')
    params = load_params()
    state = initial_state(params, seed=args.seed)
    start = {key: state[key] for key in ('tick', 'energy', 'burnout', 'balance_cents')}
    for _ in range(args.ticks):
        state = step(state, {'kind': args.action}, params, state['rng'])
    print(json.dumps({'status': 'SYNTHETIC_NOT_PERSONAL_OR_FORECAST', 'source': 'game-forge/sim',
                     'start': start, 'finish': {key: state[key] for key in start},
                     'action': args.action, 'real_payment': 'NOT_CONNECTED'}, indent=2))


if __name__ == '__main__':
    main()
