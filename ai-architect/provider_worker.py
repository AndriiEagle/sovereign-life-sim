"""Trusted bounded API worker; invoked ONLY by the governor adapter. No retries."""
import json
import os
from pathlib import Path
import sys
import urllib.request


def run(request):
    key_name='OPENAI_API_KEY' if request['provider']=='openai' else 'OPENROUTER_API_KEY'
    key=os.environ.get(key_name)
    env=Path(request['env_file'])
    if not key and env.is_file():
        for line in env.read_text(encoding='utf-8-sig').splitlines():
            name,separator,value=line.strip().partition('=')
            if separator and name==key_name:key=value.strip().strip('"').strip("'")
    if not key:return dict(status='BLOCKED_KEY',attempted=False,usage={})
    if request['kind']=='image':
        url='https://api.openai.com/v1/images/generations'
        body=dict(model=request['model'],prompt=request['prompt'],n=1,size='1024x1024',quality='low',background='transparent',output_format='png')
    else:
        url=('https://api.openai.com/v1/chat/completions' if request['provider']=='openai' else 'https://openrouter.ai/api/v1/chat/completions')
        instruction='Return only a JSON rule with schema="sovereign.rule.v1", id (lowercase safe ID), format="'+request['format']+'", origin="llm", assumptions (list). '
        instruction+='For json include operations: at most 8 add_node {op,id,title,kind:tower|mine|agent,revenue_day_cents,cost_day_cents,setup_cents}, expense {op,amount_cents}, or set_modifier {op,name:confidence_assumption|b2b_uplift_assumption,value:0..100}. '
        instruction+='For python include source defining only evaluate(state, params, seed), returning the same operations. No imports or external effects. All finances are synthetic, no invented actual revenue or health effects.'
        body=dict(model=request['model'],messages=[dict(role='system',content=instruction),dict(role='user',content=request['prompt'])],
                  max_tokens=request['max_output_tokens'],response_format={'type':'json_object'})
        if request['provider']=='openrouter':body['provider']={'allow_fallbacks':False}
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=70) as response:
            data=response.read(12*1024*1024+1)
        if len(data)>12*1024*1024:raise ValueError('PROVIDER_RESPONSE_TOO_LARGE')
        result=json.loads(data)
        output=result['data'][0]['b64_json'] if request['kind']=='image' else json.loads(result['choices'][0]['message']['content'])
        return dict(status='PASS',attempted=True,data=output,usage=result.get('usage',{}))
    except Exception:return dict(status='PROVIDER_FAILED',attempted=True,usage={})


if __name__=='__main__':
    request=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    result=run(request)
    target=Path(sys.argv[2]);temporary=target.with_suffix('.tmp')
    with temporary.open('wb') as handle:
        handle.write(json.dumps(result,allow_nan=False).encode());handle.flush();os.fsync(handle.fileno())
    os.replace(temporary,target)
