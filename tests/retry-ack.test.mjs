import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source=fs.readFileSync(new URL('../engine-isometric-ui/app.mjs',import.meta.url),'utf8');
const start=source.indexOf("$('retry-command').addEventListener('click',async()=>{");
const end=source.indexOf("\n$('export')",start);
assert(start>=0&&end>start);
const handlerSource=source.slice(start,end);

for(const scenario of ['success','failed_tick','wrong_active_version','activation_error']){
  test(`actual retry handler: ${scenario}`,async()=>{
    let handler,resets=0,calls=0;const notices=[];
    const forged={status:'PENDING_TICK',rule_id:'fixture-rule',sha256:'expected'};
    const context={
      $:id=>id==='retry-command'?{addEventListener:(_,fn)=>handler=fn}:{reset:()=>resets++},
      state:{rules:{'fixture-rule':{active:scenario==='wrong_active_version'?'wrong':'expected'}}},
      act:async()=>{
        calls++;
        if(scenario==='success')return {status:'PASS',rule_errors:{}};
        if(scenario==='failed_tick')return {status:'PASS',rule_errors:{'fixture-rule':'INSUFFICIENT_SCENARIO_FUNDS'}};
        if(calls===1)return forged;
        return {status:'PASS',rule_errors:scenario==='activation_error'?{'fixture-rule':'INSUFFICIENT_SCENARIO_FUNDS'}:{}};
      },
      notice:message=>notices.push(message),Error
    };
    vm.runInNewContext(handlerSource,context);
    await handler();
    assert.equal(resets,scenario==='success'?1:0,'Rejected activation must preserve the user form');
    assert.equal(notices.some(x=>x.includes('Дію підтверджено')),scenario==='success');
    assert.equal(calls,['success','failed_tick'].includes(scenario)?1:2);
  });
}
