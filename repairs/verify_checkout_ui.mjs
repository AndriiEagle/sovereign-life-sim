import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const file=process.argv[2];
const html=fs.readFileSync(file,'utf8');
const start=html.indexOf('async function submitCheckout()');
const end=html.indexOf('function copyToClipboard',start);
assert(start>0&&end>start,'Checkout entrypoint missing');
for(const scenario of ['unavailable','offline','malformed_success']){
  const elements=new Map();
  const get=id=>{if(!elements.has(id)){const classes=new Set(id==='modal-step-success'?['hidden']:[]);elements.set(id,{value:id==='modal-email'?'synthetic@example.invalid':'',innerText:'',textContent:'',disabled:false,hidden:true,classList:{add:v=>classes.add(v),remove:v=>classes.delete(v),contains:v=>classes.has(v)}});}return elements.get(id);};
  const context={document:{getElementById:get},currentSelectedTier:'pro',currentPayMethod:'stripe',
    crypto:{getRandomValues(){throw Error('A client must not invent a paid key');}},lucide:{createIcons(){}},
    fetch:async()=>{if(scenario==='offline')throw Error('Synthetic offline');return {ok:scenario==='malformed_success',json:async()=>scenario==='malformed_success'?{}:{detail:{message:'Payment provider unavailable'}}};}};
  vm.createContext(context);vm.runInContext(html.slice(start,end),context);
  await context.submitCheckout();
  assert.equal(get('modal-result-key').value,'',scenario+': no fabricated key');
  assert(get('modal-step-success').classList.contains('hidden'),scenario+': success screen stays hidden');
  assert.equal(get('btn-modal-submit').disabled,false);
}
console.log('Checkout UI: unavailable, offline, malformed success all fail closed (3 scenarios).');
