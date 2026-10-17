import {createMap,labelFor} from './emberglass.mjs';
const $=id=>document.getElementById(id);let state,token,map,stream,reconnectTimer,busy=false;
let messageTimer;const eventIds=new Set();
function notice(message){$('notice').textContent=message;$('notice').hidden=false;clearTimeout(messageTimer);messageTimer=setTimeout(()=>$('notice').hidden=true,6000);}
async function session(){const response=await fetch('/api/session');if(!response.ok)throw Error('LOCAL_SESSION_UNAVAILABLE');token=(await response.json()).token;}
async function api(path,body,retry=true){
  const response=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json','Authorization':'Bearer '+token}:{},body:body?JSON.stringify(body):undefined});
  if(response.status===401&&retry){await session();return api(path,body,false);}
  const data=await response.json();if(!response.ok)throw Error(data.error||'REQUEST_FAILED');return data;
}
async function act(command,payload={}){
  const data=await api('/api/command',{command,payload,request_id:crypto.randomUUID()});state=data.state;render();return data.result;
}
function button(label,handler,className){const b=document.createElement('button');b.textContent=label;if(className)b.className=className;b.addEventListener('click',()=>Promise.resolve(handler()).catch(e=>notice(e.message)));return b;}
function theory(){
  const chart=$('theory-chart');chart.replaceChildren();$('theory-legend').replaceChildren();
  const colors=['#d6b783','#9fbe91','#91bec1'],names=['Рятівник','Tit-for-Tat','Вихід після порушення'];
  const values=state.game_theory.flatMap(s=>s.history.map(r=>r.cumulative[0]));const max=Math.max(1,...values),min=Math.min(0,...values);
  state.game_theory.forEach((s,i)=>{
    const points=s.history.map(r=>`${20+(r.round-1)/19*560},${140-(r.cumulative[0]-min)/(max-min)*120}`).join(' ');
    const path=document.createElementNS('http://www.w3.org/2000/svg','polyline');path.setAttribute('points',points);path.setAttribute('fill','none');path.setAttribute('stroke',colors[i]);path.setAttribute('stroke-width','3');chart.append(path);
    const dot=document.createElementNS('http://www.w3.org/2000/svg','circle');const last=points.split(' ').at(-1).split(',');dot.setAttribute('cx',last[0]);dot.setAttribute('cy',last[1]);dot.setAttribute('r','4');dot.setAttribute('fill',colors[i]);chart.append(dot);
    const span=document.createElement('span');span.style.borderColor=colors[i];span.textContent=`${names[i]}: ${s.cumulative[0]} · енергія −${s.energy[0]} · експл. ${(s.exploitation_rate[0]*100).toFixed(0)}% (${s.completed_rounds} р.)`;$('theory-legend').append(span);
  });
}
function render(){
  if(!state)return;map?.update(state);$('cash').textContent=`CHF ${(state.economy.cash_cents/100).toLocaleString('de-CH',{minimumFractionDigits:2,maximumFractionDigits:2})}`;
  $('day').textContent=`ДЕНЬ ${Math.floor(state.life.tick/96)+1}`;$('energy').textContent=`${state.bio.Bio_RAM.toFixed(1)} / 100`;$('energy-bar').style.width=state.bio.Bio_RAM+'%';
  $('sim-time').textContent=new Date(state.sim_time).toLocaleString('uk-UA',{timeZone:'Europe/Zurich'});$('revision').textContent=`REV ${state.revision} · SYNTHETIC`;
  $('runway').textContent=`Ігровий запас · runway ${state.economy.runway_days??'∞'} днів · фактичні гроші невідомі`;
  $('trust').textContent=state.economy.gilbert_trust_index.toFixed(1);$('trust').title=state.economy.trust_formula;
  $('quest').textContent=state.quest.hours_remaining===null?'Не активований':`${state.quest.hours_remaining.toFixed(2)} год`;$('activate-quest').disabled=state.quest.start_step!==null;
  $('gemeinde').textContent=state.economy.gemeinde_status==='UNCONFIGURED'?'Не налаштовано':`${state.economy.gemeinde_days_remaining} днів`;
  $('bridge-state').textContent=state.bridge.status;$('sandbox-status').textContent=`Python: ${state.capabilities.python.status}`;
  $('use-provider').disabled=state.capabilities.provider.status!=='CONFIGURED_NOT_LIVE_VERIFIED';if($('use-provider').disabled)$('use-provider').checked=false;
  const focus=state.nodes.find(n=>n.id===state.selected);$('focus-name').textContent=focus?.title||'Обери вузол';$('focus-status').textContent=focus?`ХВИЛЯ ${focus.wave} · ${focus.status}`:'—';
  $('focus-description').textContent=focus?`${focus.source_status}. Прогрес сценарію: ${focus.progress.toFixed(1)}%. Наступна дія: ${focus.status==='Queued'?'дочекатися вільного слота':focus.status==='FOCUSED'?'робоча сесія або завершення':focus.status==='SHIPPED'?'задати модель cashflow':'перегляд параметрів'}.`:'';
  $('work').disabled=focus?.status!=='FOCUSED';$('ship').disabled=focus?.status!=='FOCUSED';$('cashflow').disabled=focus?.status!=='SHIPPED';
  const asset=focus&&state.assets[focus.id];if(asset){$('asset-preview').src=asset.url;$('asset-origin').textContent=`${asset.origin}\n${asset.status} · SHA ${asset.sha256.slice(0,10)}`;}
  $('node-economics').textContent=focus?`Припущення CHF/день: +${focus.revenue_day_cents/100} / −${focus.cost_day_cents/100}. ROI: ${state.economy.ROI[focus.id]??'базу не задано'}.`:'';
  if(focus&&document.activeElement?.tagName!=='INPUT')for(const [id,key]of[['daily-income','revenue_day_cents'],['daily-cost','cost_day_cents'],['roi-base','setup_cents']])$(id).value=(focus[key]/100).toFixed(2);
  $('node-count').textContent=`${state.nodes.length} вузлів · ${state.nodes.filter(n=>n.status==='FOCUSED').length}/2 у фокусі`;
  $('nodes').replaceChildren(...state.nodes.map(n=>{const b=button(labelFor(n),()=>act('select_node',{node_id:n.id}),`project ${n.status.toLowerCase()} ${n.id===state.selected?'selected':''}`);b.dataset.nodeId=n.id;b.setAttribute('aria-pressed',String(n.id===state.selected));const s=document.createElement('span');s.textContent=`W${n.wave} · ${n.status}`;b.append(s);return b;}));
  $('rules').replaceChildren(...Object.values(state.rules).map(r=>{const div=document.createElement('div');div.textContent=`${r.id} · ${r.pending?'PENDING_TICK':r.active?'ACTIVE':'DISABLED'} · ${r.format||'—'}`;div.append(button('Відкотити',()=>act('rollback_rule',{rule_id:r.id})));return div;}));
  $('recovery').textContent=state.bio.debuff_active?`${state.bio.debuff_reason}: будівництво ×0.6 до тіку ${state.bio.debuff_until_step}. Одна дія: ${state.bio.recovery}.`:'Дебаф не активний. Параметри — добровільна самооцінка сценарію.';
  if(document.activeElement?.tagName!=='INPUT'){
    $('bio-ram').value=state.bio.Bio_RAM.toFixed(1);$('sleep-sync').value=state.bio.Sleep_Sync_Index.toFixed(1);$('weather').value=state.bio.Swiss_Grey_Weather_Modifier;$('reduced-fog').checked=state.bio.reduced_fog;
  }
  theory();
}
function record(event){if(eventIds.has(event.seq))return;eventIds.add(event.seq);const li=document.createElement('li');li.textContent=`#${event.seq} · ${event.type} · ${event.source}`;$('events').prepend(li);while($('events').children.length>10)$('events').lastChild.remove();}
function connect(){
  stream?.close();clearTimeout(reconnectTimer);stream=new EventSource('/api/mcp/stream?after='+state.revision);
  stream.onopen=()=>{$('connection').textContent='● ЛОКАЛЬНО · ЗБЕРЕЖЕНО';};
  stream.addEventListener('state',async e=>{record(JSON.parse(e.data));try{state=await api('/api/state');render();}catch(error){notice(error.message);}});
  stream.onerror=()=>{stream.close();$('connection').textContent='Відновлення зв’язку…';reconnectTimer=setTimeout(async()=>{try{await session();state=await api('/api/state');render();connect();}catch{connect();}},1500);};
}
for(const [id,name,payload]of[['work','tick',{hours:1,action:'work'}],['rest','tick',{hours:1,action:'rest'}],['next-day','tick',{days:1,action:'rest'}],['activate-quest','activate_quest',{}]])$(id).addEventListener('click',()=>act(name,payload).catch(e=>notice(e.message)));
for(const [id,status]of[['ship','SHIPPED'],['cashflow','ACTIVE_CASHFLOW']])$(id).addEventListener('click',()=>act('node_status',{node_id:state.selected,status}).catch(e=>notice(e.message)));
$('regenerate').addEventListener('click',()=>act('regenerate_asset',{node_id:state.selected,use_provider:$('use-provider').checked}).catch(e=>notice(e.message)));
$('economics-form').addEventListener('submit',async e=>{e.preventDefault();try{await act('configure_node',{node_id:state.selected,revenue_day_cents:Math.round(Number($('daily-income').value)*100),cost_day_cents:Math.round(Number($('daily-cost').value)*100),setup_cents:Math.round(Number($('roi-base').value)*100)});}catch(error){notice(error.message);}});
$('zoom-in').addEventListener('click',()=>map?.zoom(.1));$('zoom-out').addEventListener('click',()=>map?.zoom(-.1));
$('example-bot').addEventListener('click',()=>$('prompt').value='Додай нову башту доходу на базі нового бота');$('example-client').addEventListener('click',()=>$('prompt').value='Додай клієнта з агентною поведінкою в стилі MiroFish');
$('bio-form').addEventListener('submit',async e=>{e.preventDefault();try{const bio={Bio_RAM:Number($('bio-ram').value),Sleep_Sync_Index:Number($('sleep-sync').value),Swiss_Grey_Weather_Modifier:Number($('weather').value),reduced_fog:$('reduced-fog').checked};if($('debuff-hours').value!=='')bio.debuff_hours=Number($('debuff-hours').value);await act('update_params',{bio});}catch(error){notice(error.message);}});
$('architect-form').addEventListener('submit',async e=>{
  e.preventDefault();if(busy)return;busy=true;$('forge').disabled=true;
  try{const result=await act('forge_rule',{prompt:$('prompt').value,format:$('rule-format').value,use_provider:$('use-provider').checked});
    $('architect-status').textContent=result.status==='QUEUED'?`Генерація: ${result.job_id}`:`Правило ${result.rule_id} перевірено.`;
    if(result.status==='PENDING_TICK'){await act('tick',{steps:1,action:'rest'});$('architect-status').textContent='Правило активовано. Вузол і візуал збережено.';}
  }catch(error){$('architect-status').textContent=error.message;notice(error.message);}finally{busy=false;$('forge').disabled=false;}
});
$('export').addEventListener('click',async()=>{try{const data=await api('/api/events');const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='sovereign-local-events.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){notice(error.message);}});
try{await session();state=await api('/api/state');try{map=await createMap($('map'),id=>act('select_node',{node_id:id}).catch(e=>notice(e.message)));}catch(error){$('renderer-state').textContent='Помилка рендерера';notice(error.message);}render();for(const event of (await api('/api/events')).events.slice(-10))record(event);connect();}catch(error){$('connection').textContent='Сервер недоступний';notice(error.message);}
