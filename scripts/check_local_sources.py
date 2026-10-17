"""Optional source freshness check. Clone acceptance never needs the original machine."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    rows = json.loads((ROOT / 'audit/source-copies.json').read_text(encoding='utf-8'))['copies']
    results = []
    for row in rows:
        source = Path(row['source'])
        status = ('NOT_FOUND_IN_CHECKED_SCOPE' if not source.is_file() else
                  'MATCH' if sha(source) == row['sha256'] else 'SOURCE_CHANGED')
        results.append({'target': row['target'], 'status': status})
    print(json.dumps(results, indent=2))
    return int(any(row['status'] != 'MATCH' for row in results))


if __name__ == '__main__':
    raise SystemExit(main())
