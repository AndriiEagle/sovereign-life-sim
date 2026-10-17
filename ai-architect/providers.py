"""Opt-in provider adapter. No approved policy means no external process or call."""
import base64
from datetime import datetime, timezone, date
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
import threading
import uuid

from contracts import canonical, number, text
from persistence import atomic_write


class ProviderGateway:
    def __init__(self,root,directory):
        self.root=Path(root);self.directory=Path(directory);self.lock=threading.Lock()
        path=self.directory/'providers.json'
        self.policy=json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
        self.governor=Path(self.policy.get('governor',str(Path.home()/'Desktop/KI/andrey-os/gradual_ai_launcher.py')))

    def check(self,kind):
        p=self.policy
        if p.get('enabled') is not True or p.get('allow_paid') is not True:raise ValueError('BLOCKED_PROVIDER_NO_APPROVED_BUDGET')
        if p.get('provider') not in {'openai','openrouter'} or kind not in {'rule','image'}:raise ValueError('BLOCKED_PROVIDER')
        if kind=='image' and p['provider']!='openai':raise ValueError('BLOCKED_IMAGE_ADAPTER')
        if not self.governor.is_file() or not (self.governor.parent/'harness/power_governor.py').is_file():raise ValueError('BLOCKED_GOVERNOR')
        for key in ('task_cap_usd','day_cap_usd','max_call_usd'):
            number(p.get(key),key,.000001,100)
        verified=date.fromisoformat(p.get('pricing_verified_on','1900-01-01'))
        if not 0<=(datetime.now(timezone.utc).date()-verified).days<=1:raise ValueError('BLOCKED_STALE_PRICING')
        text(p.get(kind+'_model'),120)
        number(p.get('max_output_tokens',1024),'MAX_OUTPUT_TOKENS',64,4096,True)
        for key in (('image_usd',) if kind=='image' else ('input_usd_per_million','output_usd_per_million')):
            number(p.get(key),key,0,10000)

    def report(self):
        try:self.check('rule');status='CONFIGURED_NOT_LIVE_VERIFIED'
        except (ValueError,TypeError):status='OFFLINE'
        ledger=self._ledger()
        return dict(status=status,provider=self.policy.get('provider') if status!='OFFLINE' else None,
                    calls=sum(bool(r.get('attempted')) for r in ledger),
                    receipts_known_usd=str(sum(Decimal(str(r.get('reported_cost_usd') or 0)) for r in ledger)),
                    unknown_cost_calls=sum(bool(r.get('attempted')) and r.get('reported_cost_usd') is None for r in ledger))

    def _ledger(self):
        path=self.directory/'provider-ledger.json'
        return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else []

    def generate(self,kind,prompt,format='json'):
        self.check(kind);text(prompt,4000)
        if format not in {'json','python'}:raise ValueError('UNKNOWN_RULE_FORMAT')
        with self.lock:
            p=self.policy;now=datetime.now(timezone.utc);day=now.date().isoformat()
            ledger=self._ledger();cap=Decimal(str(p['max_call_usd']))
            used=sum(Decimal(str(r['reservation_usd'])) for r in ledger)
            daily=sum(Decimal(str(r['reservation_usd'])) for r in ledger if r['utc_day']==day)
            if used+cap>Decimal(str(p['task_cap_usd'])) or daily+cap>Decimal(str(p['day_cap_usd'])):raise ValueError('BLOCKED_BUDGET_CAP')
            # Conservative byte-based input bound, including protocol/schema overhead.
            estimate=(Decimal(str(p['image_usd'])) if kind=='image' else
                Decimal(len(prompt.encode())+8192)*Decimal(str(p['input_usd_per_million']))/1000000+
                Decimal(p.get('max_output_tokens',1024))*Decimal(str(p['output_usd_per_million']))/1000000)
            if estimate>cap:raise ValueError('BLOCKED_CALL_PRICE_BOUND')
            id=uuid.uuid4().hex;folder=self.directory/'provider-jobs'/id;folder.mkdir(parents=True)
            request=folder/'request.json';response=folder/'response.json'
            atomic_write(request,canonical(dict(kind=kind,prompt=prompt,format=format,provider=p['provider'],model=p[kind+'_model'],
                max_output_tokens=p.get('max_output_tokens',1024),env_file=str(self.root/'.env'))).encode())
            row=dict(id=id,utc_day=day,kind=kind,reservation_usd=str(cap),attempted=None,status='RESERVED',reported_cost_usd=None)
            ledger.append(row);atomic_write(self.directory/'provider-ledger.json',canonical(ledger).encode())
            argv=[sys.executable,'-B',str(self.governor),'--governor','--report',str(folder/'governor.json'),'--',
                  sys.executable,'-I','-B',str(self.root/'ai-architect/provider_worker.py'),str(request),str(response)]
            try:
                with (folder/'process.log').open('wb') as log:
                    process=subprocess.run(argv,cwd=folder,stdout=log,stderr=log,timeout=120)
                if process.returncode or not response.is_file() or response.stat().st_size>12*1024*1024:raise ValueError('PROVIDER_WORKER_FAILED')
                result=json.loads(response.read_text(encoding='utf-8'))
                row.update(status=result['status'],attempted=result.get('attempted'),usage=result.get('usage'),
                           reported_cost_usd=result.get('usage',{}).get('cost'))
                if result.get('attempted') is False:row['reservation_usd']='0'
                atomic_write(self.directory/'provider-ledger.json',canonical(ledger).encode())
                if result['status']!='PASS':raise ValueError('PROVIDER_REQUEST_FAILED')
                return base64.b64decode(result['data'],validate=True) if kind=='image' else result['data']
            except Exception:
                if row['status']=='RESERVED':
                    row.update(status='UNKNOWN_REQUIRES_RECONCILIATION',attempted=True)
                    atomic_write(self.directory/'provider-ledger.json',canonical(ledger).encode())
                raise
