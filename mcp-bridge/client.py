"""Authenticated loopback client. Session tokens never enter URLs or stdout."""
import json
from pathlib import Path
from urllib.parse import urlsplit
import urllib.request
import uuid


class LocalClient:
    def __init__(self,session_file):self.session_file=Path(session_file)
    def session(self):
        data=json.loads(self.session_file.read_text(encoding='utf-8'))
        parsed=urlsplit(data['url'])
        if parsed.scheme!='http' or parsed.hostname!='127.0.0.1' or not parsed.port or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise ValueError('LOOPBACK_SESSION_REQUIRED')
        return data
    def call(self,name,payload=None,request_id=None):
        session=self.session()
        body=dict(jsonrpc='2.0',id=uuid.uuid4().hex,method=name,params=dict(payload=payload or {},request_id=request_id or uuid.uuid4().hex))
        req=urllib.request.Request(session['url']+'/api/mcp',data=json.dumps(body).encode(),
            headers={'Authorization':'Bearer '+session['token'],'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=15) as response:result=json.load(response)
        if 'error' in result:raise ValueError(result['error']['message'])
        return result['result']
    def probe(self):
        before=self.call('get_state')
        result=self.call('select_node',{'node_id':before['selected']})
        event_id=result['result']['event_id'];session=self.session()
        req=urllib.request.Request(session['url']+'/api/mcp/stream?after='+str(event_id-1),headers={'Authorization':'Bearer '+session['token']})
        observed=False
        with urllib.request.urlopen(req,timeout=6) as response:
            for _ in range(100):
                line=response.readline(16384).decode()
                if line.startswith('data: '):
                    event=json.loads(line[6:])
                    if event['seq']==event_id and event['source']=='mcp':observed=True;break
        if not observed:raise ValueError('SSE_ROUNDTRIP_NOT_OBSERVED')
        accepted=self.call('ack_event',{'event_id':event_id})
        return dict(status=accepted['state']['bridge']['status'],event_id=event_id,transport='MCP stdio → authenticated HTTP JSON-RPC → SSE → ack',providers='NOT_CONNECTED')
