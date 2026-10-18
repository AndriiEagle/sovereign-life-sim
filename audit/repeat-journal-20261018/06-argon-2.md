# Sovereign source reader: 06-argon, part 2

Derived reading aid; original file bytes and rights are authoritative. No functions or file sections have been omitted from the listed files. Cite `original/path:line` using the numbered column. Read at the exact review commit supplied in the user message.

## argon-game/app.mjs

Original bytes: 16687; SHA256: `0e1392b0b1a6d53d9163f70e67f66aa48581f03c4ef9bf40d73675b855262d35`. Original source line numbers follow.

````text
    1 | import {createCommandQueue,wasDemoShown} from './client.mjs';
    2 | const $ = id => document.getElementById(id);
    3 | const canvas = $('scene'), ctx = canvas.getContext('2d');
    4 | let token = '', data, selected = null, busy = false, started = false;
    5 | let commandQueue;
    6 | let hero = {x:520,y:590,tx:520,ty:590}, lastFrame=0, clockFrame=0, images={};
    7 | const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    8 | const locationNames = {stadelhofen:'Stadelhofen',bellevue:'Bellevue',altstadt:'Altstadt',atelier:'Майстерня'};
    9 |
   10 | async function api(path, body, retry=true){
   11 |   const response=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json',...(token?{Authorization:`Bearer ${token}`}:{})},...(body?{body:JSON.stringify(body)}:{})});
   12 |   if(response.status===401&&retry){token=(await(await fetch('/api/session')).json()).token;return api(path,body,false);}
   13 |   const result=await response.json();if(!response.ok){const error=Error(result.error||'Зв’язок із грою перервався. Спробуй ще раз.');error.status=response.status;error.stateView=result;throw error;}return result;
   14 | }
   15 | function button(label,action,primary=false){const element=document.createElement('button');element.textContent=label;if(primary)element.className='primary';element.onclick=action;return element;}
   16 | function showError(error){$('error').textContent=error.message;$('error').hidden=false;}
   17 | async function act(action,payload={},retryPending=false){
   18 |   if(busy)return;busy=true;$('error').hidden=true;const oldLocation=data.state.location;
   19 |   try{
   20 |     data=retryPending?await commandQueue.retry():await commandQueue.execute(action,payload,data.state.revision);
   21 |     started=true;
   22 |     if(data.state.location!==oldLocation||action==='new_game'||action==='load_checkpoint'){
   23 |       selected=null;const [x,y]=data.location.spawn;hero={x,y,tx:x,ty:y};
   24 |       $('location-transition').classList.remove('flash');void $('location-transition').offsetWidth;$('location-transition').classList.add('flash');
   25 |     }
   26 |     render();$('save-status').textContent=action==='save_checkpoint'?'Контрольну точку збережено':'Автозбереження · на цьому комп’ютері';
   27 |   }catch(error){
   28 |     if(error.status===409&&error.stateView?.state){data=error.stateView;selected=null;const [x,y]=data.location.spawn;hero={x,y,tx:x,ty:y};render();error.message='Стан змінився в іншій вкладці. Його оновлено; обери дію ще раз.';}
   29 |     showError(error);
   30 |   }finally{busy=false;$('retry-turn').hidden=!commandQueue.hasPending();}
   31 | }
   32 | function choose(spot){selected=spot.id;started=true;hero.tx=Math.max(90,Math.min(1190,spot.x));hero.ty=Math.max(565,Math.min(645,spot.y+90));renderInteraction();renderHotspots();}
   33 | function renderHotspots(){
   34 |   $('hotspots').replaceChildren();
   35 |   if(data.state.ending)return;
   36 |   data.location.hotspots.forEach((spot,index)=>{
   37 |     const element=button('',()=>choose(spot));element.className='hotspot'+(spot.id===selected?' active':'');element.setAttribute('aria-label',spot.title);
   38 |     element.style.left=`${spot.x/12.8}%`;element.style.top=`${spot.y/7.2}%`;
   39 |     const label=document.createElement('span');label.className='tag';label.textContent=`${index+1} · ${spot.title}`;
   40 |     const dot=document.createElement('span');dot.className='dot';element.append(label,dot);$('hotspots').append(element);
   41 |   });
   42 | }
   43 | function renderInteraction(){
   44 |   $('choices').replaceChildren();$('code-form').hidden=true;$('interaction').classList.toggle('ending',!!data.state.ending);
   45 |   if(data.state.ending){
   46 |     $('interaction-title').textContent=data.state.ending.title;$('interaction-description').textContent=data.state.ending.text;
   47 |     $('choices').append(button('Зберегти цей фінал',()=>act('save_checkpoint'),true),button('Почати нову пригоду',()=>restart()));return;
   48 |   }
   49 |   const spot=data.location.hotspots.find(s=>s.id===selected);
   50 |   if(!spot){
   51 |     $('interaction-title').textContent=started?'Куди підеш далі?':'Вітаємо в Цюриху.';
   52 |     $('interaction-description').textContent=started?data.location.description:'18:42. Зустріч о 19:30. Прототип із тобою, а кабель залишився на станції. Знайди його, дістанься майстерні й покажи демо.';
   53 |     if(!started)$('choices').append(button('Почати пригоду',()=>{started=true;choose(data.location.hotspots[0]);},true));return;
   54 |   }
   55 |   $('interaction-title').textContent=spot.title;$('interaction-description').textContent=spot.description;
   56 |   $('code-form').hidden=spot.input!=='code';
   57 |   for(const [index,choice] of spot.choices.entries()){
   58 |     const element=button(choice.label,()=>act(choice.id,spot.input==='code'?{code:$('locker-code').value}:{}),index===0&&!choice.disabled);
   59 |     element.disabled=!!choice.disabled;
   60 |     if(choice.disabled){const why=document.createElement('small');why.textContent=choice.disabled;element.append(why);}
   61 |     $('choices').append(element);
   62 |   }
   63 | }
   64 | function render(){
   65 |   const s=data.state;const hour=Math.floor(s.sim_time/60)%24,minute=s.sim_time%60;
   66 |   $('clock').textContent=`${String(hour).padStart(2,'0')}:${String(minute).padStart(2,'0')}`;
   67 |   $('chapter').textContent=data.location.chapter;$('location-title').textContent=data.location.title;$('location-subtitle').textContent=data.location.subtitle;
   68 |   canvas.setAttribute('aria-label',`Ігрова сцена: ${data.location.title}`);
   69 |   $('energy').textContent=`${s.energy} / 100`;$('energy-meter').value=s.energy;$('cash').textContent=`CHF ${(s.cash_cents/100).toFixed(2)}`;
   70 |   $('last-note').textContent=s.note;$('save-status').textContent='Збережено на цьому комп’ютері';$('load').disabled=!data.saved_checkpoint;
   71 |   $('objective').textContent=s.ending?'Ця глава завершена.':'Показати те, що працює.';
   72 |   $('tasks').replaceChildren();
   73 |   for(const [title,done] of [['Знайти кабель',s.items.includes('cable')],['Дістатися майстерні',s.visited.includes('atelier')],['Перевірити й показати демо',wasDemoShown(s)]]){
   74 |     const li=document.createElement('li');li.textContent=title;li.className=done?'done':'';$('tasks').append(li);
   75 |   }
   76 |   $('inventory').replaceChildren();for(const id of s.items){const li=document.createElement('li');li.textContent=data.items[id].name;li.title=data.items[id].description;$('inventory').append(li);}
   77 |   $('route').replaceChildren();for(const [id,name] of Object.entries(locationNames)){const element=document.createElement('span');element.textContent=name;element.className=s.location===id?'current':s.visited.includes(id)?'visited':'';$('route').append(element);}
   78 |   $('journal-entries').replaceChildren();for(const note of [...s.log].reverse()){const li=document.createElement('li');li.textContent=note;$('journal-entries').append(li);}
   79 |   renderHotspots();renderInteraction();drawScene(0);
   80 | }
   81 | function restart(){if(confirm('Почати нову пригоду? Ручна контрольна точка залишиться доступною.')){selected=null;act('new_game');}}
   82 | $('save').onclick=()=>act('save_checkpoint');$('load').onclick=()=>act('load_checkpoint');$('new').onclick=restart;
   83 | $('retry-turn').onclick=()=>act(undefined,{},true);
   84 | $('code-form').onsubmit=event=>{event.preventDefault();const first=$('choices').querySelector('button:enabled');first?.click();};
   85 | document.addEventListener('keydown',event=>{
   86 |   if(!data||['INPUT','TEXTAREA','BUTTON'].includes(document.activeElement.tagName))return;
   87 |   if(/^[1-7]$/.test(event.key)){const spot=data.location.hotspots[Number(event.key)-1];if(spot)choose(spot);}
   88 |   if(event.key.toLowerCase()==='j')$('journal').open=!$('journal').open;
   89 |   if(event.key.toLowerCase()==='e')$('choices').querySelector('button:enabled')?.click();
   90 | });
   91 | canvas.addEventListener('click',event=>{const r=canvas.getBoundingClientRect();hero.tx=Math.max(80,Math.min(1200,(event.clientX-r.left)/r.width*1280));hero.ty=Math.max(560,Math.min(650,(event.clientY-r.top)/r.height*720));});
   92 |
   93 | // The existing scene uses Canvas 2D. This renderer keeps the same light CPU path,
   94 | // caps visual updates at 30 Hz, and stops drawing in hidden tabs.
   95 | function poly(points,color){ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(...points[0]);for(const p of points.slice(1))ctx.lineTo(...p);ctx.closePath();ctx.fill();}
   96 | function rect(x,y,w,h,color){ctx.fillStyle=color;ctx.fillRect(x,y,w,h);}
   97 | function ellipse(x,y,rx,ry,color){ctx.fillStyle=color;ctx.beginPath();ctx.ellipse(x,y,rx,ry,0,0,Math.PI*2);ctx.fill();}
   98 | function line(x,y,a,b,color,width=1){ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(a,b);ctx.stroke();}
   99 | function sky(){const gradient=ctx.createLinearGradient(0,0,0,720);gradient.addColorStop(0,'#10182d');gradient.addColorStop(.55,'#405369');gradient.addColorStop(1,'#203543');ctx.fillStyle=gradient;ctx.fillRect(0,0,1280,720);ellipse(1070,108,24,24,'#f4dfae');for(let i=0;i<55;i++){const x=(i*193+71)%1280,y=(i*79+11)%250;rect(x,y,1.3,1.3,'#a9bbce66');}}
  100 | function house(x,y,w,h,color,roof=true){rect(x,y,w,h,color);if(roof)poly([[x-8,y],[x+w/2,y-45],[x+w+8,y]],'#253241');for(let row=0;row<Math.floor(h/46)-1;row++)for(let col=0;col<Math.floor(w/36);col++){const wx=x+12+col*34,wy=y+22+row*46;rect(wx,wy,17,25,(row+col)%3?'#e5c98b':'#738c9d');line(wx+8,wy,wx+8,wy+25,'#354956',2);line(wx,wy+12,wx+17,wy+12,'#354956',2);}}
  101 | function lamp(x,y){line(x,y,x,y-150,'#283c48',8);ellipse(x,y-150,15,9,'#efcf92');const g=ctx.createRadialGradient(x,y-142,3,x,y-120,100);g.addColorStop(0,'#efd69745');g.addColorStop(1,'#efd69700');ctx.fillStyle=g;ctx.fillRect(x-110,y-245,220,240);}
  102 | function street(){poly([[0,520],[1280,500],[1280,720],[0,720]],'#263b45');for(let y=560;y<720;y+=38){line(0,y,1280,y-12,'#40545a66');for(let x=(y%76)*3;x<1280;x+=95)line(x,y,x-16,y+35,'#40545a55');}for(let i=0;i<9;i++)ellipse(60+i*153,640+(i%3)*20,80,4,'#91afb015');}
  103 | function tram(x,y,scale=1){ctx.save();ctx.translate(x,y);ctx.scale(scale,scale);rect(0,0,590,155,'#2f788d');poly([[0,0],[28,-25],[562,-25],[590,0]],'#a6bbc4');rect(0,93,590,35,'#cad2cc');for(let i=0;i<9;i++){rect(18+i*63,13,47,65,'#eed59d');line(42+i*63,13,42+i*63,78,'#354d5a',2);}rect(276,4,5,138,'#193c51');ellipse(100,150,28,14,'#101a21');ellipse(490,150,28,14,'#101a21');line(170,-25,220,-90,'#8199a8',4);line(220,-90,270,-25,'#8199a8',4);ctx.restore();}
  104 | function station(){
  105 |   if(images.sky?.complete&&images.station?.complete&&images.train?.complete&&images.train.naturalWidth){for(const key of ['sky','station','train'])ctx.drawImage(images[key],0,0,1280,720);rect(0,520,1280,200,'#152d3840');}
  106 |   else{sky();house(70,245,190,190,'#3f4859');house(350,270,200,180,'#344656');tram(0,337,1.3);for(let i=0;i<5;i++){ctx.strokeStyle='#b5c6c9';ctx.lineWidth=13;ctx.beginPath();ctx.ellipse(200+i*240,405,190,150,-.22,Math.PI,Math.PI*2);ctx.stroke();}street();}
  107 |   rect(120,418,88,140,'#425963');for(let i=0;i<3;i++){rect(125,425+i*42,77,36,'#293f4d');rect(185,440+i*42,5,5,'#d9b77d');}rect(270,355,180,73,'#142733');rect(279,365,162,5,'#d2b06a');rect(279,382,135,4,'#c5c88c');rect(279,398,150,4,'#9ab6a5');lamp(1120,564);
  108 | }
  109 | function bellevue(){sky();rect(0,380,1280,170,'#385268');for(let i=0;i<18;i++)line(20+i*75,430+(i%4)*14,95+i*75,430+(i%4)*14,'#a1c3c233');house(30,300,190,150,'#4c4d59');house(225,275,130,175,'#596071');house(1020,235,180,230,'#484852');street();line(0,540,1280,525,'#c8b68e',3);line(0,560,1280,545,'#738a92',3);line(0,205,1280,240,'#657e8d',2);tram(590,330,.9);rect(120,380,145,120,'#314d54');poly([[95,380],[287,380],[267,350],[112,350]],'#a5a58a');rect(155,406,79,67,'#e6bc79');rect(918,430,66,126,'#8a9b9b');rect(927,442,48,41,'#243d4c');rect(934,496,33,8,'#d6b77c');lamp(335,560);lamp(1150,530);ellipse(525,550,36,10,'#0c1b2688');rect(508,472,27,67,'#544856');ellipse(520,460,16,18,'#d3ad8b');ellipse(547,515,28,36,'#bd935f');}
  110 | function altstadt(){sky();rect(0,450,1280,250,'#274c60');for(let i=0;i<4;i++){house(i*210-20,220+(i%2)*35,195,270,'#4c5660');}house(840,210,220,300,'#6a6661');house(1080,275,190,240,'#555d60');poly([[745,210],[790,75],[830,210]],'#233947');rect(766,205,48,220,'#6c7370');ellipse(791,234,17,17,'#e5d3a1');line(791,234,791,224,'#35404a',2);line(791,234,800,239,'#35404a',2);street();poly([[0,525],[500,510],[710,720],[0,720]],'#3b4c53');poly([[430,510],[650,500],[1060,720],[820,720]],'#667478');for(let i=0;i<6;i++)line(460+i*44,516,840+i*44,720,'#adada455');rect(894,393,65,123,'#314f43');rect(900,398,53,108,'#40664e');ellipse(943,462,3,3,'#dfbf78');lamp(1045,566);rect(340,520,130,15,'#ae8b68');line(353,533,347,570,'#263641',7);line(453,533,460,570,'#263641',7);rect(383,467,29,62,'#45616e');ellipse(397,455,15,17,'#d2ac84');}
  111 | function atelier(){rect(0,0,1280,720,'#25343b');rect(0,0,1280,465,'#31454b');for(let x=0;x<1280;x+=76)line(x,0,x,465,'#45575b33');poly([[0,465],[1280,465],[1280,720],[0,720]],'#5a4c41');for(let y=490;y<720;y+=45)line(0,y,1280,y,'#8e786144');for(let x=0;x<1280;x+=150)line(x,465,x+100,720,'#352f2d88');rect(65,110,320,280,'#182d3f');for(let i=0;i<4;i++)house(85+i*72,230+(i%2)*30,60,140,'#405467',false);rect(219,110,9,280,'#aaa58a');rect(65,245,320,8,'#aaa58a');rect(58,102,334,10,'#c5b28b');rect(460,424,320,56,'#a47a52');poly([[460,480],[780,480],[830,537],[420,537]],'#694c38');line(473,481,455,650,'#49372d',19);line(767,481,788,650,'#49372d',19);rect(552,345,120,77,'#1c2c36');rect(560,353,104,60,'#94c4bc');for(let i=0;i<5;i++)rect(570,365+i*8,70-i*7,2,'#355a64');poly([[541,423],[685,423],[704,439],[528,439]],'#9fa7a0');rect(1000,90,190,330,'#243a41');for(let y=150;y<420;y+=75){rect(1000,y,190,9,'#a18261');for(let i=0;i<7;i++)rect(1010+i*24,y-52,16,52,['#63766b','#9c7c61','#c4b18a'][i%3]);}rect(1060,420,105,150,'#4b605c');rect(165,470,100,44,'#8e7460');rect(175,513,13,100,'#54483c');rect(242,513,13,100,'#54483c');rect(167,430,92,50,'#7b6251');rect(870,385,35,106,'#6f5860');ellipse(888,367,20,24,'#d9b78e');poly([[861,343],[889,324],[913,346],[908,373],[899,351],[869,353]],'#433537');lamp(785,425);const light=ctx.createRadialGradient(620,270,40,620,440,390);light.addColorStop(0,'#f5d08d26');light.addColorStop(1,'#f5d08d00');ctx.fillStyle=light;ctx.fillRect(260,70,800,620);line(620,0,620,205,'#131f29',4);poly([[583,233],[600,205],[640,205],[657,233]],'#e8c38a');}
  112 | function drawHero(time){const moving=Math.abs(hero.tx-hero.x)>1;const bob=moving?Math.sin(time/80)*2:0;const x=hero.x,y=hero.y+bob;ellipse(x,y+5,27,8,'#08162377');line(x-9,y-34,x-12+(moving?Math.sin(time/100)*5:0),y,'#192935',11);line(x+8,y-34,x+10-(moving?Math.sin(time/100)*5:0),y,'#192935',11);poly([[x-22,y-98],[x+18,y-98],[x+25,y-34],[x-24,y-34]],'#37525c');poly([[x-18,y-99],[x+5,y-94],[x+17,y-73],[x+6,y-70]],'#c6a777');ellipse(x,y-118,16,21,'#d2ad8b');poly([[x-18,y-121],[x-18,y-138],[x+3,y-146],[x+19,y-128],[x+15,y-116],[x+8,y-131],[x-13,y-129]],'#423d37');line(x-23,y-81,x-30,y-47,'#354955',10);line(x+20,y-80,x+31,y-52,'#354955',10);rect(x-19,y-90,7,33,'#a49b79');}
  113 | function drawScene(time){if(!data)return;ctx.clearRect(0,0,1280,720);({stadelhofen:station,bellevue,altstadt,atelier}[data.state.location])();if(!reduced){hero.x+=(hero.tx-hero.x)*.13;hero.y+=(hero.ty-hero.y)*.13;}else{hero.x=hero.tx;hero.y=hero.ty;}drawHero(time);if(data.state.location!=='atelier'){for(let i=0;i<72;i++){const x=(i*173+(time/30))%1380-50,y=(i*97+time*.25)%750;line(x,y,x-5,y+17,'#b9d7df19');}}const vignette=ctx.createRadialGradient(640,360,230,640,360,780);vignette.addColorStop(0,'#07111b00');vignette.addColorStop(1,'#07111b8a');ctx.fillStyle=vignette;ctx.fillRect(0,0,1280,720);}
  114 | function frame(time){if(!document.hidden&&time-lastFrame>=1000/30){lastFrame=time;clockFrame=time;drawScene(reduced?0:time);}requestAnimationFrame(frame);}
  115 | async function start(){
  116 |   try{token=(await api('/api/session')).token;data=await api('/api/state');commandQueue=createCommandQueue({send:request=>api('/api/action',request),storage:sessionStorage});started=data.state.history.length>0;const [x,y]=data.location.spawn;hero={x,y,tx:x,ty:y};render();requestAnimationFrame(frame);
  117 |     $('retry-turn').hidden=!commandQueue.hasPending();if(commandQueue.hasPending())showError(Error('Попередній хід очікує підтвердження. Натисни «Повторити підтвердження».'));
  118 |     for(const key of ['sky','station','train']){const img=new Image();img.onload=()=>{images[key]=img;drawScene(clockFrame);};img.src=`/art/${key}.png`;}
  119 |   }catch(error){$('save-status').textContent='Не вдалося відкрити збереження';showError(error);}
  120 | }
  121 | start();
````
