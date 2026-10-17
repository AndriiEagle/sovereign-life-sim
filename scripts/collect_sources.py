"""Explicit, finite private source extraction. Run on Sol only; originals are read-only."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
CONDUCTOR = Path('C:/Users/Andrii/Desktop/conductor-revenue-lab')
KI = Path('C:/Users/Andrii/Desktop/KI')
ARCHIVE = Path('D:/AI_DEPOT/handoffs/game-forge-audit-20261017/arcanum-repo')
GAME_FORGE = Path('C:/Users/Andrii/Desktop/game-forge')


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    copies = []
    plan = [(CONDUCTOR / 'revenue_lab' / name, ROOT / 'simulation-core/revenue_lab' / name,
             'CONDUCTOR_RECIPIENT_REUSE_GRANT')
            for name in ('__init__.py', '__main__.py', 'core.py', 'README.md')]
    plan += [(CONDUCTOR / 'tests' / name, ROOT / 'simulation-core/upstream-tests' / name,
              'CONDUCTOR_RECIPIENT_REUSE_GRANT') for name in ('test_core.py', 'test_cli.py')]
    plan += [(CONDUCTOR / 'LICENSE_AND_RIGHTS.md', ROOT / 'simulation-core/CONDUCTOR_RIGHTS.md',
              'CONDUCTOR_RECIPIENT_REUSE_GRANT')]
    plan += [(KI / 'creator-income-os/templates/short-video-script.md',
              ROOT / 'automation-nodes/source-templates/short-video-script.md', 'PRIVATE_USER_AUTHORIZED'),
             (KI / 'brand-social-os/references/viral-lab.md',
              ROOT / 'automation-nodes/source-templates/viral-lab.md', 'PRIVATE_USER_AUTHORIZED')]
    # Inert source snapshots: no game binary, lore, atlas, customer media or third-party npm tree.
    plan += [(ARCHIVE / 'references/potential-reuse/emberglass' / name,
              ROOT / 'engine-isometric-ui/reference-source' / name,
              'PRIVATE_USER_AUTHORIZED_PUBLIC_COMMERCIAL_RIGHTS_UNRESOLVED')
             for name in ('iso-kit-renderer.js', 'iso-worldpack-v11.js')]
    plan += [(GAME_FORGE / 'sim' / name,
              ROOT / 'simulation-core/game-forge/sim' / name,
              'PRIVATE_USER_AUTHORIZED_PUBLIC_COMMERCIAL_RIGHTS_UNRESOLVED')
             for name in ('__init__.py', 'core.py', 'params.json', 'MATH.md')]
    plan += [(GAME_FORGE / 'sim/tests' / name,
              ROOT / 'simulation-core/game-forge/sim/tests' / name,
              'PRIVATE_USER_AUTHORIZED_PUBLIC_COMMERCIAL_RIGHTS_UNRESOLVED')
             for name in ('__init__.py', 'test_math.py')]
    for source, target, rights in plan:
        if not source.is_file():
            raise SystemExit(f'NOT_FOUND_IN_CHECKED_SCOPE: {source}')
        digest = sha(source)
        if target.exists() and sha(target) != digest:
            raise SystemExit(f'REFUSE_OVERWRITE_CHANGED_SNAPSHOT: {target}')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha(target) != digest:
            raise SystemExit(f'COPY_HASH_MISMATCH: {target}')
        copies.append(dict(source=str(source), target=target.relative_to(ROOT).as_posix(),
                           sha256=digest, bytes=target.stat().st_size, rights=rights,
                           mode='snapshot_inactive' if 'reference-source' in target.parts else 'reused'))
    (ROOT / 'audit/source-copies.json').write_text(json.dumps({
        'schema': 'sovereign.source-copies.v1', 'copies': copies,
        'originals_modified': False, 'runtime_note': 'Archived renderer snapshots are inactive; their atlas/worldpack closure is not bundled.'
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'copied': len(copies), 'hashes_matched': len(copies), 'originals_modified': False}))


if __name__ == '__main__':
    main()
