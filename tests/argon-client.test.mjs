import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {createCommandQueue,wasDemoShown} from '../argon-game/client.mjs';

function storage(){const values=new Map();return {getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};}
function network(){let turns=0,calls=0;const seen=new Set();return {turns:()=>turns,async send(request){if(!seen.has(request.request_id)){seen.add(request.request_id);turns++;}calls++;if(calls<=2)throw new TypeError('Synthetic lost acknowledgment');return {state:{location:'stadelhofen',revision:turns},result:{accepted:true,request_id:request.request_id}};}};}

test('two lost responses then a retry commit only one turn, even after reload',async()=>{
  const store=storage(),server=network();let ids=0;
  let queue=createCommandQueue({send:server.send,storage:store,uuid:()=>`synthetic-${++ids}`});
  await assert.rejects(queue.execute('catch_breath',{},0));
  assert(queue.hasPending());
  await assert.rejects(queue.execute('catch_breath',{},0));
  queue=createCommandQueue({send:server.send,storage:store,uuid:()=>`synthetic-${++ids}`});
  const response=await queue.retry();assert.equal(response.state.revision,1);
  assert.equal(server.turns(),1);assert.equal(ids,1);assert(!queue.hasPending());
});

test('actual UI act entrypoint preserves the pending ID on a manual retry',async()=>{
  const file=process.env.ARGON_UI_TEST_SOURCE||new URL('../argon-game/app.mjs',import.meta.url);
  const source=fs.readFileSync(file,'utf8');const first=source.indexOf('async function act('),last=source.indexOf('\nfunction choose(',first);
  assert(first>=0&&last>first);
  const server=network(),store=storage();let ids=0;
  const queue=createCommandQueue({send:server.send,storage:store,uuid:()=>`synthetic-${++ids}`});
  const elements=new Map();const $=id=>{if(!elements.has(id))elements.set(id,{hidden:false,textContent:'',classList:{remove(){},add(){}},offsetWidth:0});return elements.get(id);};
  const context={busy:false,data:{state:{location:'stadelhofen',revision:0}},started:false,selected:null,hero:{},commandQueue:queue,$,
    api:(_path,request)=>server.send(request),render(){},showError(){},TypeError,crypto:{randomUUID:()=>`legacy-${++ids}`}};
  vm.createContext(context);vm.runInContext(source.slice(first,last),context);
  await context.act('catch_breath',{});await context.act(undefined,{},true);
  assert.equal(server.turns(),1,'A lost acknowledgment cannot cause a second committed turn');
});

test('a definite rejection clears pending; an ambiguous success retains it',async()=>{
  const rejected=Object.assign(Error('revision changed'),{status:409,stateView:{state:{revision:2}}});
  const queue=createCommandQueue({send:async()=>{throw rejected;},storage:storage(),uuid:()=> 'synthetic'});
  await assert.rejects(queue.execute('catch_breath',{},0));assert(!queue.hasPending());
  const ambiguous=createCommandQueue({send:async()=>({result:{accepted:true,request_id:'wrong'}}),storage:storage(),uuid:()=> 'synthetic'});
  await assert.rejects(ambiguous.execute('catch_breath',{},0));assert(ambiguous.hasPending());
  const authentication=createCommandQueue({send:async()=>{throw Object.assign(Error('auth'),{status:401});},storage:storage(),uuid:()=> 'synthetic'});
  await assert.rejects(authentication.execute('catch_breath',{},0));assert(authentication.hasPending());
});

test('honest postponement never claims a demo presentation',()=>{
  assert.equal(wasDemoShown({flags:['demo_tested'],ending:{id:'honest'}}),false);
  assert.equal(wasDemoShown({flags:['demo_tested'],ending:{id:'prepared'}}),true);
  assert.equal(wasDemoShown({flags:['demo_tested'],ending:{id:'late'}}),true);
  assert.equal(wasDemoShown({flags:[],ending:null}),false);
});

test('actual UI checklist leaves the presentation incomplete after an honest ending',()=>{
  const file=process.env.ARGON_UI_TEST_SOURCE||new URL('../argon-game/app.mjs',import.meta.url);
  const source=fs.readFileSync(file,'utf8');const first=source.indexOf('function render(){'),last=source.indexOf('\nfunction restart(',first);
  assert(first>=0&&last>first);
  const elements=new Map();const element=()=>({children:[],className:'',replaceChildren(){this.children=[];},append(child){this.children.push(child);},setAttribute(){}});
  const $=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id);};
  const context={$,
    document:{createElement:element},canvas:element(),data:{state:{sim_time:1160,location:'atelier',energy:70,cash_cents:1200,ending:{id:'honest'},flags:['demo_tested'],items:[],visited:['atelier'],log:[]},location:{title:'Atelier'},items:{}},
    locationNames:{},wasDemoShown,renderHotspots(){},renderInteraction(){},drawScene(){}};
  vm.createContext(context);vm.runInContext(source.slice(first,last),context);context.render();
  assert.notEqual($('tasks').children[2].className,'done','Postponement cannot be shown as a completed demo presentation');
});
