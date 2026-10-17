"""Finite metadata inventory of named roots. Excludes personal/account/generated content."""
from collections import Counter
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.next', '.vercel',
    '.codex', '.claude', '.kilo', 'codex-health', 'quarantine', 'backups', 'downloads',
    'logs', 'sessions', 'captures', 'memory', 'data', 'out', 'output', 'outputs', 'runs',
    'artifacts', 'reports', 'graphify-out', '.codegraph', '.codegraphcontext', '.pytest_cache',
    '.tools', 'tools-cache', '_deploy_worktrees', '_to_delete', 'account', 'accounts'}
EXTENSIONS = {'.py', '.js', '.mjs', '.ts', '.tsx', '.gd', '.tscn', '.godot', '.html', '.css',
              '.md', '.json', '.svg', '.png', '.webp', '.jpg', '.jpeg', '.glsl', '.gdshader', '.frag', '.vert', '.ps1'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume-partial', action='store_true', help='Keep earlier complete metadata observations; finish only partial roots.')
    args = parser.parse_args()
    context = json.loads((ROOT / 'CONTEXT_MANIFEST.json').read_text(encoding='utf-8'))
    roots = sorted({p for item in context['projects'] for p in item['local_roots']})
    summaries, indexes = [], []
    prior, prior_indexes = {}, {}
    if args.resume_partial:
        previous = json.loads((ROOT / 'audit/coverage-summary.json').read_text(encoding='utf-8'))
        prior = {item['root']: item for item in previous['roots'] if item['status'] == 'COMPLETE_WITHIN_FILTERED_SCOPE'}
        prior_indexes = {item['root']: item for item in json.loads((ROOT / 'audit/local-file-inventory.json').read_text(encoding='utf-8'))}
    for location in roots:
        if location in prior:
            summaries.append(prior[location])
            indexes.append(prior_indexes[location])
            continue
        root = Path(location)
        counts, selected, errors = Counter(), [], []
        stopped = False
        stop_reason = None
        started = time.monotonic()
        directories = 0
        if not root.is_dir():
            summaries.append({'root': location, 'status': 'NOT_FOUND_IN_CHECKED_SCOPE'})
            continue
        if args.resume_partial and (root / '.git').exists():
            indexed = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'], capture_output=True, timeout=15)
            if indexed.returncode == 0:
                for raw in indexed.stdout.decode('utf-8').split('\0'):
                    path = Path(raw)
                    if not raw or any(part.lower() in EXCLUDED or part.startswith('.') for part in path.parts) or path.suffix.lower() not in EXTENSIONS or 'account' in path.name.lower() or 'secret' in path.name.lower():
                        continue
                    selected.append(raw)
                    counts[path.suffix.lower()] += 1
                summaries.append({'root': location, 'status': 'COMPLETE_WITHIN_GIT_INDEX_FILTER',
                    'files': len(selected), 'extension_counts': dict(counts), 'errors': [], 'cap_reached': False,
                    'limit': 'Tracked index metadata only; not an assertion that every ignored/untracked or working-tree file exists.'})
                indexes.append({'root': location, 'paths': selected})
                print(json.dumps({'root_checked': len(summaries), 'files': len(selected), 'status': summaries[-1]['status']}), flush=True)
                continue
        for directory, subdirs, files in os.walk(root, followlinks=False, onerror=lambda e: errors.append(type(e).__name__)):
            directories += 1
            if directories > (5000 if args.resume_partial else 1000) or time.monotonic() - started > (20 if args.resume_partial else 3):
                stopped, stop_reason = True, 'metadata_time_or_directory_budget'
                break
            allowed = []
            for name in sorted(subdirs):
                if name.lower() in EXCLUDED or name.startswith('.'):
                    continue
                try:
                    info = Path(directory, name).lstat()
                    if getattr(info, 'st_file_attributes', 0) & 1024 or Path(directory, name).is_symlink():
                        continue
                except OSError:
                    errors.append('DIRECTORY_NOT_READABLE')
                    continue
                allowed.append(name)
            subdirs[:] = allowed
            for name in sorted(files):
                path = Path(directory, name)
                if name.startswith('.') or path.suffix.lower() not in EXTENSIONS or 'account' in name.lower() or 'secret' in name.lower():
                    continue
                counts[path.suffix.lower()] += 1
                selected.append(path.relative_to(root).as_posix())
                if len(selected) >= 10000:
                    stopped, stop_reason = True, 'file_metadata_budget'
                    break
            if stopped:
                break
        summaries.append({'root': location, 'status': 'PARTIAL' if stopped or errors else 'COMPLETE_WITHIN_FILTERED_SCOPE',
                          'files': len(selected), 'extension_counts': dict(counts), 'errors': errors, 'cap_reached': stopped})
        summaries[-1]['stop_reason'] = stop_reason
        print(json.dumps({'root_checked': len(summaries), 'files': len(selected), 'status': summaries[-1]['status']}), flush=True)
        indexes.append({'root': location, 'paths': selected})
    (ROOT / 'audit/local-file-inventory.json').write_text(json.dumps(indexes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result = {'schema': 'sovereign.coverage.v1', 'scope': 'FILE-NAME METADATA ONLY; no contents, runtime or whole-drive completion claim',
              'excluded_directories': sorted(EXCLUDED), 'roots': summaries,
              'private_filename_index': 'audit/local-file-inventory.json (local only, excluded from Git)',
              'total_files_in_filtered_roots': sum(item.get('files', 0) for item in summaries)}
    (ROOT / 'audit/coverage-summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'roots': len(roots), 'files': result['total_files_in_filtered_roots'], 'partial_roots': sum(item['status']=='PARTIAL' for item in summaries)}))


if __name__ == '__main__':
    main()
