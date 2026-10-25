"""Reconstruct complete source bytes from small browser-readable parts."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCES = ['simulation-core/persistence.py', 'simulation-core/contracts.py',
           'simulation-core/unified_tick.py', 'ai-architect/runtime.py', 'ai-architect/ruleforge.py',
           'engine-isometric-ui/app.mjs', 'engine-isometric-ui/emberglass.mjs',
           'mcp-bridge/command-queue.mjs', 'mcp-bridge/client.py', 'scripts/serve.py', 'scripts/mcp_server.py',
           'engine-isometric-ui/reference-source/iso-kit-renderer.js',
           'simulation-core/game-forge/sim/params.json', 'CONTEXT_MANIFEST.json',
           'tests/test_returned_repairs.py', 'tests/retry-ack.test.mjs']


def build():
    outputs, files = {}, []
    for index, source in enumerate(SOURCES, 1):
        data = (ROOT / source).read_bytes()
        chunks, current = [], b''
        for line in data.splitlines(keepends=True):
            if len(line) > 12000:
                raise ValueError('LINE_TOO_LARGE: ' + source)
            if len(current) + len(line) > 12000:
                chunks.append(current)
                current = b''
            current += line
        if current:
            chunks.append(current)
        assert b''.join(chunks) == data
        parts, first = [], 1
        for number, content in enumerate(chunks, 1):
            name = f'source/{index:02}-{number:02}.txt'
            outputs[name] = content
            count = len(content.splitlines())
            parts.append(dict(path=name, bytes=len(content), line_start=first,
                              line_end=first + count - 1, sha256=hashlib.sha256(content).hexdigest()))
            first += count
        files.append(dict(path=source, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), parts=parts))
    outputs['SOURCE_MANIFEST.json'] = (json.dumps({'base': '7e1b314f010c114fdde6d8cd387601442652f76c',
        'boundary': 'Complete listed source bytes; required unlisted imports/assets remain in the same repository.',
        'files': files}, indent=2) + '\n').encode()
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = build()
    for relative, data in outputs.items():
        path = HERE / relative
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                raise ValueError('READER_MISSING_OR_STALE: ' + relative)
        else:
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(data)
    print(json.dumps({'status': 'PASS', 'files': len(outputs), 'max_part_bytes': 12000,
                      'bytes': sum(map(len, outputs.values()))}))


if __name__ == '__main__':
    main()
