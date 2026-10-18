"""One durable command dispatcher for HTTP, UI and the MCP adapter."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import uuid

from assetforge import AssetForge
from contracts import canonical, identifier, keys, number, text
from persistence import Store, atomic_write, digest
from ruleforge import compile_offline, evaluate, stage, validate_rule
from sandbox import Sandbox
from unified_tick import advance, apply_operations, command, initial_state, node, public_state, refresh
from providers import ProviderGateway


class Runtime:
    def __init__(self, root, directory, generated=None, plugins=None):
        self.root=Path(root); self.directory=Path(directory)
        self.assets=AssetForge(generated or self.directory/'generated-assets')
        self.plugins=Path(plugins or self.directory/'plugins')
        self.sandbox=Sandbox(self.directory/'sandbox.json')
        self.providers=ProviderGateway(self.root,self.directory)
        manifest=json.loads((self.root/'CONTEXT_MANIFEST.json').read_text(encoding='utf-8'))
        self.store=Store(self.directory,initial_state(manifest))
        self.start_revision=self.store.get()['revision'];self.bridge_confirmed=False
        self.jobs=ThreadPoolExecutor(max_workers=1,thread_name_prefix='sovereign-forge')
        with self.store.lock:
            state=self.store.get()
            interrupted=False
            for job in state.get('jobs',{}).values():
                if job.get('status') in {'QUEUED','RUNNING'}:
                    job['status']='INTERRUPTED_NO_RETRY';interrupted=True
            for asset in state['assets'].values():
                if asset.get('status')=='QUEUED':asset['status']='READY';interrupted=True
            if interrupted:self.store.commit('jobs_interrupted',{},'system','recover-'+uuid.uuid4().hex,{},state)
            if self.ensure_assets(state):
                self.store.commit('assets_ready',{},'system','assets-start-'+uuid.uuid4().hex,{},state)

    def ensure_assets(self,state):
        changed=False
        for n in state['nodes']:
            old=state['assets'].get(n['id'])
            path=self.assets.directory/(old['key']+'.'+old['format']) if old else None
            if path and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()!=old['sha256']:
                path.unlink()
            if not old or not path.is_file():
                state['assets'][n['id']]=self.assets.fallback(n,old.get('variant',0) if old else 0);changed=True
        return changed

    def get(self):
        result=public_state(self.store.get())
        result['bridge']['status']='LIVE_LOCAL_BRIDGE' if self.bridge_confirmed else 'NOT_CONNECTED'
        result['capabilities']=dict(python=self.sandbox.report(),provider=self.providers.report(),
            renderer='EmberIsoKitRenderer with original owned atlas',mcp='Official SDK stdio adapter; provider sessions tracked separately')
        return result

    def persist_rule(self,rule):
        atomic_write(self.plugins/(rule['sha256']+'.json'),canonical({k:v for k,v in rule.items() if k!='sha256'}).encode())
        if rule['format']=='python':atomic_write(self.plugins/(rule['sha256']+'.py'),rule['source'].encode())

    def execute(self,name,payload,request_id,source='ui'):
        if not isinstance(request_id,str) or not 8<=len(request_id)<=100 or any(not(c.isalnum() or c in '-_') for c in request_id):
            raise ValueError('INVALID_REQUEST_ID')
        if not isinstance(payload,dict):raise ValueError('EXPECTED_PAYLOAD_OBJECT')
        fingerprint=digest([name,payload]);background=None
        with self.store.lock:
            previous=self.store.duplicate(request_id,fingerprint)
            if previous is not None:return previous
            state=self.store.get();summary={};result=dict(status='PASS',event_id=state['revision']+1,request_id=request_id)
            if name=='tick':
                keys(payload,['steps','hours','days','action'])
                dimensions=[k for k in ('steps','hours','days') if k in payload]
                if len(dimensions)>1:raise ValueError('AMBIGUOUS_TICK_UNIT')
                unit=dimensions[0] if dimensions else 'hours'
                amount=number(payload.get(unit,1),unit,1,{'steps':672,'hours':168,'days':7}[unit],True)
                steps=amount*{'steps':1,'hours':4,'days':96}[unit];operations={};errors={}
                trial=deepcopy(state)
                for id,rule in state['rules'].items():
                    if rule.get('pending'):
                        try:
                            ops=evaluate(rule['pending'],trial,self.sandbox)
                            trial=apply_operations(trial,ops,id,charge=rule['pending']['sha256'] not in rule['applied'])
                            operations[id]=ops
                        except (ValueError,OSError) as error:
                            errors[id]=str(error).split(':')[0];rule['pending']=None
                state=advance(state,steps,payload.get('action','rest'),operations)
                self.ensure_assets(state);result['rule_errors']=errors
                summary=dict(steps=steps,action=payload.get('action','rest'),rule_errors=errors)
            elif name=='forge_rule':
                keys(payload,['prompt','format','rule','use_provider','template_params'])
                use_provider=payload.get('use_provider',False)
                if type(use_provider) is not bool:raise ValueError('INVALID_BOOLEAN')
                if 'rule' in payload:
                    if 'prompt' in payload or use_provider or 'template_params' in payload:raise ValueError('AMBIGUOUS_RULE_INPUT')
                    rule=validate_rule(payload['rule'])
                elif use_provider:
                    if 'template_params' in payload:raise ValueError('OFFLINE_TEMPLATE_PARAMS_ONLY')
                    prompt=text(payload.get('prompt'),2000);self.providers.check('rule')
                    job_id='job-'+uuid.uuid4().hex
                    state.setdefault('jobs',{})[job_id]=dict(status='QUEUED',kind='rule')
                    background=('rule',job_id,dict(prompt=prompt,format=payload.get('format','json')))
                    rule=None;result.update(status='QUEUED',job_id=job_id);summary=dict(job_id=job_id)
                else:rule=compile_offline(payload.get('prompt'),payload.get('format','json'),payload.get('template_params'))
                if rule:
                    state=stage(state,rule,self.sandbox);self.persist_rule(rule)
                    result.update(status='PENDING_TICK',rule_id=rule['id'],sha256=rule['sha256'])
                    summary=dict(rule_id=rule['id'],format=rule['format'],sha256=rule['sha256'])
            elif name=='rollback_rule':
                keys(payload,['rule_id'],['rule_id']);id=identifier(payload['rule_id']);rule=state['rules'].get(id)
                if not rule:raise ValueError('UNKNOWN_RULE')
                if rule['pending']:rule['pending']=None
                elif rule['history']:rule['pending']=rule['history'].pop()
                else:
                    rule['active']=None
                    for n in state['nodes']:
                        if n['owner_rule']==id:
                            focused=n['status']=='FOCUSED';n['status']='DISABLED'
                            if focused:
                                queued=next((x for x in state['nodes'] if x['status']=='Queued'),None)
                                if queued:queued['status']='FOCUSED'
                summary=dict(rule_id=id)
            elif name=='regenerate_asset':
                keys(payload,['node_id','use_provider'],['node_id']);n=node(state,payload['node_id'])
                if type(payload.get('use_provider',False)) is not bool:raise ValueError('INVALID_BOOLEAN')
                variant=state['assets'].get(n['id'],{}).get('variant',0)+1
                state['assets'][n['id']]=self.assets.fallback(n,variant)
                result.update(status='READY_OFFLINE',node_id=n['id']);summary=dict(node_id=n['id'],variant=variant)
                if payload.get('use_provider'):
                    self.providers.check('image');job_id='job-'+uuid.uuid4().hex
                    state['assets'][n['id']]['status']='QUEUED'
                    state.setdefault('jobs',{})[job_id]=dict(status='QUEUED',kind='image',node_id=n['id'],variant=variant)
                    background=('image',job_id,dict(node=deepcopy(n),variant=variant));result.update(status='QUEUED',job_id=job_id)
            elif name=='ack_event':
                if source!='mcp':raise ValueError('MCP_CLIENT_REQUIRED')
                keys(payload,['event_id'],['event_id']);seq=number(payload['event_id'],'EVENT',self.start_revision+1,state['revision'],True)
                if self.store.rows[seq-1]['source']!='mcp':raise ValueError('FOREIGN_EVENT_ACK')
                state['bridge']['status']='LIVE_LOCAL_BRIDGE';summary=dict(event_id=seq)
            elif name=='game_theory':
                from game_theory_shield import simulate
                keys(payload,['left','right','rounds','exit_on_breach','payoffs','energy_cost','exploitation_cost'])
                state['game_theory_custom']=simulate(**payload);summary=dict(rounds=state['game_theory_custom']['completed_rounds'])
            else:state=command(state,name,payload);summary=deepcopy(payload)
            refresh(state)
            self.store.commit(name,summary,source,request_id,result,state,fingerprint)
            if name=='ack_event':self.bridge_confirmed=True
        if background:self.jobs.submit(self._background,*background)
        return result

    def _background(self,kind,job_id,payload):
        try:
            data=self.providers.generate(kind,payload['prompt'] if kind=='rule' else self.assets.prompt(payload['node']),payload.get('format','json'))
            if kind=='rule':
                rule=validate_rule(data)
                with self.store.lock:
                    state=stage(self.store.get(),rule,self.sandbox);self.persist_rule(rule)
                    state['jobs'][job_id]['status']='PENDING_TICK'
                    state['jobs'][job_id]['rule_id']=rule['id']
                    self.store.commit('rule_ready',dict(job_id=job_id,rule_id=rule['id']),'system',job_id+'-ready',{},state)
                self.execute('tick',{'steps':1,'action':'rest'},job_id+'-activate','system')
            else:
                asset=self.assets.accept_image(payload['node'],data,payload['variant'])
                with self.store.lock:
                    state=self.store.get();id=payload['node']['id']
                    if state['assets'].get(id,{}).get('variant')==payload['variant']:state['assets'][id]=asset
                    state['jobs'][job_id]['status']='READY'
                    self.store.commit('asset_ready',dict(job_id=job_id,node_id=id),'system',job_id+'-ready',{},state)
        except Exception:
            with self.store.lock:
                state=self.store.get();state.setdefault('jobs',{}).setdefault(job_id,{})['status']='ERROR'
                if kind=='image':
                    asset=state['assets'].get(payload['node']['id'],{})
                    if asset.get('variant')==payload['variant']:asset.update(status='READY',provider_status='ERROR')
                self.store.commit('generation_failed',dict(job_id=job_id,code='GENERATION_FAILED'),'system',job_id+'-failed',{},state)

    def close(self):
        self.jobs.shutdown(wait=True,cancel_futures=True);self.store.close()
