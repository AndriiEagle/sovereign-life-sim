import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {cents,expenseRule,towerParams} from '../engine-isometric-ui/scenario-forms.mjs';
import {createDurableQueue} from '../mcp-bridge/command-queue.mjs';

test('UI expresses explicit synthetic modifiers and exact cents; plain expense infers none',()=>{
  assert.equal(cents('20.01'),2001);
  assert.deepEqual(towerParams('20',true),{setup_cents:2000,auto_deduct_setup:true});
  const input={id:'expense-test',title:'Implants',amount:'20'};
  assert.deepEqual(expenseRule(input).operations,[{op:'expense',amount_cents:2000,kpi_modifiers:{}}]);
  assert.deepEqual(expenseRule({...input,multiplier:'1.5',bio:'60'}).operations[0].kpi_modifiers,{revenue_multiplier:1.5,Bio_RAM:60});
  for(const value of ['','NaN','Infinity','-1','1000001','1.001'])assert.throws(()=>cents(value));
  for(const multiplier of ['5.01','-1','NaN'])assert.throws(()=>expenseRule({...input,multiplier}));
});

test('simulator lost-ack retry after reload reuses one request and one expense',async()=>{
  const values=new Map(),storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
  let debits=0,calls=0;const seen=new Set();
  const options={storage,key:'sovereign.pending.v1',uuid:()=> 'one-expense-id',
    acknowledged:(response,pending)=>response.result.request_id===pending.request_id,
    async send(request){
      if(!seen.has(request.request_id)){seen.add(request.request_id);debits++;}
      if(++calls<=2)throw new TypeError('lost ack');
      return {result:{event_id:2,request_id:request.request_id}};
    }};
  let queue=createDurableQueue(options);
  await assert.rejects(queue.execute('forge_rule',{rule:expenseRule({id:'one-rule',title:'Test',amount:'20'})},1));
  queue=createDurableQueue(options);
  await queue.retry();assert.equal(debits,1);assert(!queue.hasPending());
});

test('actual simulator UI retries the durable command rather than creating a new request',async()=>{
  const source=fs.readFileSync(new URL('../engine-isometric-ui/app.mjs',import.meta.url),'utf8');
  const first=source.indexOf('async function act('),last=source.indexOf('\nasync function activateRule',first);
  assert(first>=0&&last>first);
  const values=new Map(),storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
  let calls=0,debits=0;const seen=new Set();
  const commandQueue=createDurableQueue({storage,key:'sovereign.pending.v1',uuid:()=> 'one-stable-ui-id',
    acknowledged:(r,p)=>r.result.request_id===p.request_id,
    async send(request){
      if(!seen.has(request.request_id)){seen.add(request.request_id);debits++;}
      if(++calls<=2)throw new TypeError('lost ack');
      return {result:{request_id:request.request_id,event_id:3},state:{revision:3}};
    }});
  const context={commandBusy:false,commandQueue,state:{revision:1},render(){},$:()=>({hidden:false}),Error};
  vm.createContext(context);vm.runInContext(source.slice(first,last),context);
  await assert.rejects(context.act('tick',{steps:1}));
  await context.act(undefined,{},true);assert.equal(debits,1);
});
