"""Prove an actual resource guard rejects a planted behavioral defect in a temporary copy."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = (ROOT / 'simulation-core/model.mjs').read_text(encoding='utf-8')
    before, after = 'energy: state.energy - 15', 'energy: state.energy + 15'
    if source.count(before) != 1:
        raise SystemExit('MUTATION_TARGET_NOT_UNIQUE')
    with tempfile.TemporaryDirectory(prefix='sovereign-mutation-') as directory:
        root = Path(directory)
        (root / 'simulation-core').mkdir()
        (root / 'tests').mkdir()
        shutil.copyfile(ROOT / 'tests/model.test.mjs', root / 'tests/model.test.mjs')
        (root / 'simulation-core/model.mjs').write_text(source, encoding='utf-8')
        baseline = subprocess.run(['node', '--test', 'tests/model.test.mjs'], cwd=root, capture_output=True, text=True)
        (root / 'simulation-core/model.mjs').write_text(source.replace(before, after), encoding='utf-8')
        mutant = subprocess.run(['node', '--test', 'tests/model.test.mjs'], cwd=root, capture_output=True, text=True)
        if baseline.returncode != 0 or mutant.returncode == 0 or 'AssertionError' not in mutant.stdout + mutant.stderr:
            raise SystemExit('GUARD_NOT_DEFECT_SENSITIVE')
        report = {'status': 'PASS', 'baseline_exit': baseline.returncode, 'mutant_exit': mutant.returncode,
                  'mutation': 'Work incorrectly restores energy instead of consuming it',
                  'oracle': 'tests/model.test.mjs: work consumes resource without inventing money or actual payment',
                  'original_files_modified': False}
        (ROOT / 'audit/local-mutation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report))


if __name__ == '__main__':
    main()
