"""Generated Python runs only in a rootless, resource-checked OCI container."""
import ast
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
import uuid


def check_source(source):
    if not isinstance(source,str) or len(source)>16000: raise ValueError('INVALID_PYTHON_SIZE')
    try:tree=ast.parse(source)
    except SyntaxError:raise ValueError('PYTHON_SYNTAX_REJECTED') from None
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef) or tree.body[0].name!='evaluate':
        raise ValueError('EXPECTED_EVALUATE_FUNCTION')
    fn=tree.body[0]
    if [a.arg for a in fn.args.args]!=['state','params','seed'] or fn.decorator_list or fn.args.defaults or fn.args.kwarg or fn.args.vararg:
        raise ValueError('INVALID_EVALUATE_SIGNATURE')
    for item in ast.walk(tree):
        if isinstance(item,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,ast.ClassDef,ast.AsyncFunctionDef)):
            raise ValueError('PYTHON_POLICY_REJECTED')
        if isinstance(item,ast.Attribute) and item.attr.startswith('_'):
            raise ValueError('PYTHON_POLICY_REJECTED')
        if isinstance(item,ast.Name) and (item.id.startswith('__') or item.id in {'open','eval','exec','compile','getattr','setattr','globals','locals','input','breakpoint'}):
            raise ValueError('PYTHON_POLICY_REJECTED')
    return tree


RUNNER = r'''
import json, sys, os, pathlib, resource, math
cg=pathlib.Path('/sys/fs/cgroup')
memory=(cg/'memory.max').read_text().strip()
quota,period=(cg/'cpu.max').read_text().split()
status=pathlib.Path('/proc/self/status').read_text()
mounts=pathlib.Path('/proc/mounts').read_text().splitlines()
checks={
 'nonroot':os.getuid()==65534,
 'memory':memory!='max' and int(memory)<=268435456,
 'cpu':quota!='max' and int(quota)/int(period)<=.5,
 'network':set(os.listdir('/sys/class/net'))<=set(['lo']),
 'capabilities':any(line.startswith('CapEff:') and int(line.split()[1],16)==0 for line in status.splitlines()),
 'no_new_privileges':'NoNewPrivs:\t1' in status,
 'readonly_root':any(line.split()[1]=='/' and 'ro' in line.split()[3].split(',') for line in mounts),
 'no_gpu':not pathlib.Path('/dev/nvidia0').exists() and not pathlib.Path('/dev/dri').exists(),
}
if not all(checks.values()): raise RuntimeError('ISOLATION_NOT_ENFORCED')
os.environ.clear()
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
resource.setrlimit(resource.RLIMIT_CPU,(4,4))
request=json.loads(sys.stdin.read(262145))
safe={k:__builtins__.__dict__[k] for k in ['abs','min','max','sum','range','len','enumerate','round','list','dict','int','float','str','bool','any','all','zip','sorted']}
scope={'__builtins__':safe,'math':math}
exec(compile(request['source'],'<isolated-rule>','exec'),scope)
ops=scope['evaluate'](request['state'],request.get('params',{}),request['seed'])
print(json.dumps({'operations':ops,'isolation':checks},allow_nan=False))
'''


class Sandbox:
    def __init__(self, config_path):
        self.status='BLOCKED_SANDBOX'; self.reason='Rootless OCI runtime and pinned image are required.'
        self.runtime=None; self.image=None
        path=Path(config_path)
        if not path.is_file(): return
        try:
            cfg=json.loads(path.read_text(encoding='utf-8'))
            if set(cfg)!={'runtime','image'} or cfg['runtime'] not in {'podman','docker'}: return
            self.runtime=shutil.which(cfg['runtime']); self.image=cfg['image']
            if not self.runtime or not re.fullmatch(r'[a-zA-Z0-9./_-]+@sha256:[a-f0-9]{64}',self.image): return
            p=subprocess.run([self.runtime,'info','--format','json' if cfg['runtime']=='podman' else '{{json .}}'],capture_output=True,timeout=4,text=True)
            info=json.loads(p.stdout)
            host=info.get('host',{})
            rootless=(host.get('security',{}).get('rootless') is True if cfg['runtime']=='podman'
                      else any('rootless' in item for item in info.get('SecurityOptions',[])))
            cgroup=host.get('cgroupVersion') if cfg['runtime']=='podman' else info.get('CgroupVersion')
            if not rootless or str(cgroup) not in {'2','v2'}: return
            self.status='PROBING'
            self.evaluate('def evaluate(state, params, seed):\n    return []\n',{},42)
            self.status='READY'; self.reason='Rootless OCI isolation and resource controls observed in a real worker.'
        except Exception:
            self.status='BLOCKED_SANDBOX'; self.reason='Runtime, pinned local image, or enforced isolation probe failed.'

    def evaluate(self, source, state, seed):
        check_source(source)
        if self.status not in {'READY','PROBING'}: raise ValueError('BLOCKED_SANDBOX')
        name='sovereign-rule-'+uuid.uuid4().hex
        argv=[self.runtime,'run','--rm','--pull=never','--name',name,'--network=none','--read-only',
              '--cap-drop=ALL','--security-opt=no-new-privileges','--user=65534:65534',
              '--cpus=0.5','--memory=256m','--memory-swap=256m','--pids-limit=16',
              '--tmpfs=/tmp:rw,noexec,nosuid,size=8m','--workdir=/tmp','--entrypoint=python','-i',
              self.image,'-I','-S','-c',RUNNER]
        data=json.dumps(dict(source=source,state=state,params={},seed=seed),allow_nan=False).encode()
        if len(data)>262144: raise ValueError('SANDBOX_INPUT_TOO_LARGE')
        proc=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        buffers=[bytearray(),bytearray()]; overflow=threading.Event()
        def read(pipe, output):
            while True:
                chunk=pipe.read(4096)
                if not chunk: return
                if len(output)+len(chunk)>65536: overflow.set(); return
                output.extend(chunk)
        threads=[threading.Thread(target=read,args=(pipe,buffers[i]),daemon=True) for i,pipe in enumerate((proc.stdout,proc.stderr))]
        for t in threads:t.start()
        def write_input():
            try:proc.stdin.write(data);proc.stdin.close()
            except (BrokenPipeError,OSError,ValueError):pass
        writer=threading.Thread(target=write_input,daemon=True)
        try:
            writer.start()
            deadline=time.monotonic()+5
            while proc.poll() is None and not overflow.is_set() and time.monotonic()<deadline:
                time.sleep(.02)
            if proc.poll() is None or overflow.is_set():
                proc.kill()
                raise ValueError('SANDBOX_TIMEOUT_OR_OUTPUT_LIMIT')
            for t in threads:t.join(timeout=.5)
            if proc.returncode or overflow.is_set(): raise ValueError('SANDBOX_RULE_FAILED')
            response=json.loads(buffers[0])
            if not response.get('isolation') or not all(response['isolation'].values()): raise ValueError('SANDBOX_ISOLATION_FAILED')
            return response['operations']
        finally:
            if proc.poll() is None: proc.kill()
            proc.wait(timeout=2)
            for pipe in (proc.stdout,proc.stderr):pipe.close()
            subprocess.run([self.runtime,'rm','--force',name],capture_output=True,timeout=3)

    def report(self):
        return dict(status=self.status,reason=self.reason)
