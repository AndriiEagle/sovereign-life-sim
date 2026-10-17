"""Create a package integrity snapshot after review. This does not sign or accept it."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def included(path):
    relative = path.relative_to(ROOT)
    if any(part in {'.git', '__pycache__', '.runtime', '.venv', 'node_modules', 'screenshots', 'generated'} for part in relative.parts):
        return False
    if relative.name.startswith('.env') and relative.name != '.env.example':
        return False
    if relative.name in {'PACKAGE_MANIFEST.json', 'remote-readback.json', 'acceptance-local.json'}:
        return False
    return not (len(relative.parts) > 1 and relative.parts[0] == 'audit' and relative.parts[1].startswith('local-'))


def main():
    files = []
    for path in sorted(ROOT.rglob('*')):
        if path.is_file() and included(path):
            with path.open('rb') as handle:
                digest = hashlib.file_digest(handle, 'sha256').hexdigest()
            files.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': digest, 'bytes': path.stat().st_size})
    (ROOT / 'PACKAGE_MANIFEST.json').write_text(json.dumps({'schema': 'sovereign.package.v1',
        'boundary': 'SHA256 integrity only, not a signature or an acceptance verdict.', 'files': files}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'hashed_files': len(files), 'bytes': sum(row['bytes'] for row in files)}))


if __name__ == '__main__':
    main()
