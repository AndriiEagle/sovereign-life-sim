"""Build reproducible, line-numbered browser excerpts from explicit source files.

These are derived reading aids. Original files and their byte hashes stay in Git.
No discovery scan, personal runtime, environment file or external call is used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = '5963e7d1dc54057db73f61159171f1bb94f94604'
GROUPS = {
    '01-journal': ['simulation-core/persistence.py', 'ai-architect/runtime.py', 'simulation-core/contracts.py'],
    '02-state': ['simulation-core/unified_tick.py', 'simulation-core/game_theory_shield.py'],
    '03-guards': ['ai-architect/ruleforge.py', 'ai-architect/assetforge.py', 'ai-architect/sandbox.py',
                  'ai-architect/providers.py', 'ai-architect/provider_worker.py'],
    '04-economics': ['simulation-core/game-forge/sim/__init__.py', 'simulation-core/game-forge/sim/core.py',
                     'simulation-core/game-forge/sim/params.json', 'simulation-core/revenue_lab/__init__.py',
                     'simulation-core/revenue_lab/core.py'],
    '05-transport-ui': ['scripts/serve.py', 'mcp-bridge/client.py', 'mcp-bridge/command-queue.mjs',
                        'engine-isometric-ui/app.mjs', 'engine-isometric-ui/emberglass.mjs',
                        'engine-isometric-ui/scenario-forms.mjs'],
    '06-argon': ['argon-game/game.py', 'argon-game/world.json', 'scripts/serve_argon.py',
                 'argon-game/client.mjs', 'argon-game/app.mjs'],
    '07-tests': ['tests/test_phase2.py', 'tests/test_audit_followup.py', 'tests/test_argon.py',
                 'tests/test_journal_review.py', 'tests/test_integrity.py', 'tests/test_server.py',
                 'tests/scenario-forms.test.mjs', 'tests/argon-client.test.mjs',
                 'scripts/configure_mcp.py', 'scripts/verify.py', 'scripts/freeze.py'],
}
# This file is deliberately linked once, rather than duplicated into a code bundle.
LINK_ONLY = ['CONTEXT_MANIFEST.json', 'requirements-bridge.txt', 'RIGHTS.md', 'AGENTS.md',
             'AUDIT_CONTEXT.md', 'AUDIT_PROMPT.uk.md']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    outputs, files, bundles = {}, [], []
    for group, paths in GROUPS.items():
        sections = []
        for relative in paths:
            data = (ROOT / relative).read_bytes()
            text = data.decode('utf-8')
            # Line numbers refer to the original file, never this wrapper's Markdown lines.
            numbered = '\n'.join(f'{index:5} | {line}' if line else f'{index:5} |'
                                 for index, line in enumerate(text.splitlines(), 1))
            section = (f'\n## {relative}\n\nOriginal bytes: {len(data)}; SHA256: `{sha(data)}`. '
                       f'Original source line numbers follow.\n\n````text\n{numbered}\n````\n')
            sections.append((relative, section))
        chunks, chunk, names = [], '', []
        for relative, section in sections:
            if chunk and len((chunk + section).encode('utf-8')) > 48000:
                chunks.append((chunk, names)); chunk, names = '', []
            chunk += section; names.append(relative)
        if chunk:
            chunks.append((chunk, names))
        for index, (body, names) in enumerate(chunks, 1):
            name = f'{group}-{index}.md'
            data = (f'# Sovereign source reader: {group}, part {index}\n\n'
                    'Derived reading aid; original file bytes and rights are authoritative. '
                    'No functions or file sections have been omitted from the listed files. '
                    'Cite `original/path:line` using the numbered column. '
                    'Read at the exact review commit supplied in the user message.\n'
                    + body).encode('utf-8')
            outputs[name] = data
            bundles.append({'path': name, 'bytes': len(data), 'sha256': sha(data), 'source_files': names})
    for relative in [path for paths in GROUPS.values() for path in paths] + LINK_ONLY:
        data = (ROOT / relative).read_bytes()
        original = subprocess.run(['git', 'show', BASE + ':' + relative], cwd=ROOT, capture_output=True)
        if original.returncode and relative != 'tests/test_journal_review.py':
            raise ValueError('BASE_SOURCE_MISSING: ' + relative)
        old = original.stdout if original.returncode == 0 else None
        status = 'unchanged_from_base' if old == data else 'new_regression_test' if old is None else 'candidate_change'
        if status == 'candidate_change' and relative != 'simulation-core/persistence.py':
            raise ValueError('UNEXPECTED_SOURCE_CHANGE: ' + relative)
        files.append({'path': relative, 'bytes': len(data), 'sha256': sha(data),
                      'source_lines': len(data.decode('utf-8').splitlines()), 'status': status,
                      'base_sha256': sha(old) if old is not None else None})
    manifest = {'schema': 'sovereign.browser-source-reader.v1',
                'repository': 'AndriiEagle/sovereign-life-sim', 'repository_id': 1423646041,
                'source_base_commit': BASE, 'review_branch': 'codex/journal-audit-530',
                'boundary': 'Finite source slice, not full UI/SDK/provider/runtime or product acceptance. '
                            'Candidate modifies only persistence.py; read originals at the supplied review commit.',
                'files': files, 'bundles': bundles,
                'link_only': LINK_ONLY,
                'optional_dependencies': {'mcp': 'requirements-bridge.txt; no install authorized by this handoff',
                                          'Pillow': 'image validation only; no dependency installation performed'},
                'external_dependencies': {'hosted_provider_governor': 'Host-only, outside this repository; '
                                          'live provider execution remains NOT_RUN',
                                          'python_rule_isolation': 'Rootless OCI + pinned local image required; BLOCKED_SANDBOX'}}
    outputs['SOURCE_MANIFEST.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = build()
    for name, data in outputs.items():
        target = HERE / name
        if args.check:
            if not target.is_file() or target.read_bytes() != data:
                raise SystemExit('READER_MISSING_OR_STALE: ' + name)
        else:
            target.write_bytes(data)
    print(json.dumps({'status': 'PASS', 'mode': 'check' if args.check else 'build',
                      'files': len(outputs), 'bytes': sum(map(len, outputs.values()))}))


if __name__ == '__main__':
    main()
