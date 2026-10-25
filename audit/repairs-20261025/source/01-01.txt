"""Durable transactions. The fsynced, hash-chained journal is authoritative."""
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import threading
import uuid

from contracts import canonical


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if os.name != 'nt':
            descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


class Store:
    def __init__(self, directory, initial):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.changed = threading.Condition(self.lock)
        self.path = self.directory / 'events.jsonl'
        self.rows, self.requests = [], {}
        self.state = deepcopy(initial)
        self.failed = False
        # A single local process owns a store, including native MCP adapter clients.
        self._lease = (self.directory / 'owner.lock').open('a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                self._lease.seek(0)
                if not self._lease.read(1):
                    self._lease.write(b'0'); self._lease.flush()
                self._lease.seek(0)
                msvcrt.locking(self._lease.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self._lease.close()
            raise ValueError('STORE_ALREADY_IN_USE') from None
        try:
            self._recover()
            if not self.rows:
                self.commit('initial', {}, 'system', 'initial', {}, self.state)
        except Exception:
            self.close()
            raise

    def _recover(self):
        if not self.path.exists():
            return
        data = self.path.read_bytes()
        good = 0
        for line in io.BytesIO(data):
            if not line.endswith(b'\n'):
                # Preserve the interrupted tail before truncating it. Never skip a corrupt committed row.
                atomic_write(self.directory / ('interrupted-' + uuid.uuid4().hex + '.bin'), line)
                with self.path.open('r+b') as handle:
                    handle.truncate(good); handle.flush(); os.fsync(handle.fileno())
                break
            try:
                row = json.loads(line)
                if (not isinstance(row, dict) or row['schema'] != 'sovereign.event.v2'
                        or type(row['seq']) is not int
                        or any(not isinstance(row[key], str) for key in
                               ('sha256', 'previous', 'request_id', 'fingerprint', 'type', 'source'))
                        or any(not isinstance(row[key], dict) for key in ('payload', 'state', 'result'))
                        or type(row['sim_time']) not in (str, int)
                        or type(row['state']['revision']) is not int
                        or type(row['state']['sim_time']) not in (str, int)):
                    raise ValueError('JOURNAL_CORRUPT')
                checksum = row.pop('sha256')
                if digest(row) != checksum or row['seq'] != len(self.rows) + 1 or row['previous'] != (self.rows[-1]['sha256'] if self.rows else '0' * 64):
                    raise ValueError('JOURNAL_CORRUPT')
            except (KeyError, TypeError, ValueError):
                raise ValueError('JOURNAL_CORRUPT') from None
            row['sha256'] = checksum
            self.rows.append(row)
            self.requests[row['request_id']] = row
            self.state = row['state']
            good += len(line)

    def get(self):
        with self.lock:
            return deepcopy(self.state)

    def duplicate(self, request_id, fingerprint):
        row = self.requests.get(request_id)
        if row and row['fingerprint'] != fingerprint:
            raise ValueError('REQUEST_ID_CONFLICT')
        return deepcopy(row['result']) if row else None

    def commit(self, kind, payload, source, request_id, result, state, fingerprint=None):
        with self.lock:
            if self.failed:
                raise OSError('STORE_WRITE_FAILED_RESTART_REQUIRED')
            state = deepcopy(state)
            state['revision'] = len(self.rows) + 1
            row = dict(schema='sovereign.event.v2', seq=state['revision'],
                       previous=self.rows[-1]['sha256'] if self.rows else '0' * 64,
                       request_id=request_id, fingerprint=fingerprint or digest([kind, payload]),
                       sim_time=state['sim_time'], type=kind, source=source, payload=payload,
                       state=state, result=deepcopy(result))
            row['sha256'] = digest(row)
            try:
                with self.path.open('ab') as handle:
                    handle.write((canonical(row) + '\n').encode('utf-8'))
                    handle.flush(); os.fsync(handle.fileno())
            except OSError:
                self.failed = True
                raise
            self.rows.append(row)
            self.requests[request_id] = row
            self.state = state
            try:
                atomic_write(self.directory / 'state.json', canonical(state).encode('utf-8'))
            except OSError:
                # The committed journal is sufficient to recover; a snapshot is only a cache.
                pass
            self.changed.notify_all()
            return deepcopy(result)

    def events(self, after=0):
        with self.lock:
            return [{k:deepcopy(v) for k,v in row.items() if k not in {'state','result','fingerprint','previous'}}
                    for row in self.rows if row['seq'] > after]

    def close(self):
        if not self._lease.closed:
            if os.name == 'nt':
                import msvcrt
                self._lease.seek(0)
                msvcrt.locking(self._lease.fileno(), msvcrt.LK_UNLCK, 1)
            self._lease.close()
