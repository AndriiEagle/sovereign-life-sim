// Adapter over the byte-preserved Emberglass renderer: owned atlas + live project DTOs.
const shortNames = {'game-forge':'Game Forge','brand-social-os':'Instagram','creator-income-os':'Creator OS','revenue-defense':'Revenue Defense','visual-voice-lab':'Voice Lab','agency-backlog':'Agency Lab','coiffeur-site':'Coiffeur','lego-godot':'LEGO / Godot','arcanum-card':'Card Forge','control-room':'Control Room','conductor':'Conductor','fiverr':'Fiverr / B2B','mirofish':'MiroFish','synera':'Synera','living-arcanum':'Living Arcanum','memento':'Memento'};
export const titleFor = node => shortNames[node.id] || node.title;
export const labelFor = node => titleFor(node).slice(0,22);
export function syncProjectButtons(container,nodes,selected,onSelect) {
  const existing=new Map([...container.children].map(b=>[b.dataset.nodeId,b]));
  for(const [index,n] of nodes.entries()){
    let b=existing.get(n.id);
    if(!b){
      b=container.ownerDocument.createElement('button');
      b.type='button';b.dataset.nodeId=n.id;
      b.append(container.ownerDocument.createTextNode(''),container.ownerDocument.createElement('span'));
      b.addEventListener('click',()=>onSelect(n.id));
    }
    b.className=`project ${n.status.toLowerCase()} ${n.id===selected?'selected':''}`;
    b.setAttribute('aria-pressed',String(n.id===selected));
    b.title=n.title;
    b.childNodes[0].nodeValue=labelFor(n);b.children[0].textContent=`W${n.wave} · ${n.status}`;
    // Leave existing elements in place: removing or re-appending them loses focus.
    if(container.children[index]!==b)container.insertBefore(b,container.children[index]||null);
    existing.delete(n.id);
  }
  for(const b of existing.values())b.remove();
}
export function positions(nodes) {
  const primary = Array.from({length:16},(_,i)=>({x:1+3*(i%4),y:1+3*Math.floor(i/4)}));
  const rest=[];
  for(let y=0;y<12;y++)for(let x=0;x<12;x++)if(!primary.some(p=>p.x===x&&p.y===y))rest.push({x,y});
  return nodes.map((n,i)=>({...n,...[...primary,...rest][i],z:0,zBias:0}));
}
export function viewportFor(width,zoom=1) {
  const height=Math.round(width*2/3);
  return {width,height,scale:width/2450*zoom,origin:{x:width/2,y:height*.205}};
}
export function pickProject(items,x,y,scale) {
  const front=[...items].reverse();
  return front.find(n=>n.labelBox&&x>=n.labelBox.x&&x<=n.labelBox.x+n.labelBox.w&&y>=n.labelBox.y&&y<=n.labelBox.y+n.labelBox.h)
    ||front.find(n=>Math.abs(x-n.screen.x)<60*scale&&y>n.screen.y-128*scale&&y<n.screen.y+25*scale);
}
export function layoutLabels(items,selected,hovered,scale,measure) {
  const priority=n=>(n.id===selected?4:0)+(n.id===hovered?2:0)+(n.status==='FOCUSED'?1:0);
  const labels=[];
  for(const n of [...items].sort((a,b)=>priority(b)-priority(a))){
    if(items.length>24&&n.id!==selected&&n.id!==hovered)continue;
    const w=Math.min(140,Math.max(78,measure(labelFor(n))+20)),h=scale<.33?27:30;
    const box={x:n.screen.x-w/2,y:n.screen.y+14*scale,w,h};
    if(labels.some(({box:b})=>box.x<b.x+b.w&&box.x+box.w>b.x&&box.y<b.y+b.h&&box.y+box.h>b.y))continue;
    labels.push({node:n,box});
  }
  return labels;
}
export async function createMap(canvas,onSelect) {
  const iso=window.EmberIsoKitRenderer;
  if(!iso)throw new Error('Emberglass renderer unavailable');
  const ids=['sovereign_tile','sovereign_mine','sovereign_tower','sovereign_agent'];
  await iso.init({kitVersion:'emberglass-iso-kit-v1',atlas:{file:'atlas.svg'},
    promotedAssets:ids.map(assetId=>({assetId,qaStatus:'promoted',artStatus:'original-owned-geometric',pivot:{x:64,y:assetId==='sovereign_tile'?96:128}})),
    runtimeAssets:ids.map((assetId,i)=>({assetId,frame:{x:i*128,y:0,w:128,h:160}}))},'/engine-isometric-ui');
  const ctx=canvas.getContext('2d');let state=null,view=null,items=[],zoom=1,hovered=null,mobileCentered=false;
  const backdrop=new Image();backdrop.onload=draw;backdrop.onerror=()=>draw();
  backdrop.src='/engine-isometric-ui/assets/visual/sovereign-island-v1.png';
  const images=new Map();
  function image(url) {
    if(!images.has(url)){
      const img=new Image();img.onload=draw;img.onerror=()=>{img.failed=true;draw();};img.src=url;images.set(url,img);
    }
    return images.get(url);
  }
  function draw(){
    if(!state)return;
    view=viewportFor(Math.max(320,Math.round(canvas.clientWidth||1100)),zoom);
    const {width,height,scale,origin}=view;
    const stage=canvas.parentElement;
    if(stage&&stage.clientWidth<width&&!mobileCentered){stage.scrollLeft=(width-stage.clientWidth)/2;mobileCentered=true;}
    else if(stage&&stage.clientWidth>=width)mobileCentered=false;
    const density=Math.max(1,Math.min(2,window.devicePixelRatio||1));
    canvas.width=Math.round(width*density);canvas.height=Math.round(height*density);
    ctx.setTransform(density,0,0,density,0,0);ctx.imageSmoothingEnabled=true;
    ctx.fillStyle='#122d32';ctx.fillRect(0,0,width,height);
    const hasArt=backdrop.complete&&backdrop.naturalWidth;
    canvas.dataset.artStatus=hasArt?'ready':'fallback';
    if(hasArt)ctx.drawImage(backdrop,0,0,width,height);
    // Reuse the frozen kit's world projection and sprite renderer. The active
    // adapter owns the art and grid; no archived renderer bytes are changed.
    for(let y=0;y<12;y++)for(let x=0;x<12;x++){
      const p=iso.worldToScreen(x,y,0,scale,origin);
      ctx.beginPath();ctx.moveTo(p.x,p.y-32*scale);ctx.lineTo(p.x+64*scale,p.y);
      ctx.lineTo(p.x,p.y+32*scale);ctx.lineTo(p.x-64*scale,p.y);ctx.closePath();
      if(!hasArt){ctx.fillStyle=(x+y)%2?'#304940':'#385247';ctx.fill();}
      ctx.strokeStyle=hasArt?'rgba(225,232,191,.09)':'rgba(195,218,177,.2)';ctx.lineWidth=.7;ctx.stroke();
    }
    items=positions(state.nodes).sort((a,b)=>a.x+a.y-b.x-b.y||a.id.localeCompare(b.id));
    for(const n of items){
      const point=iso.worldToScreen(n.x,n.y,0,scale,origin);
      const asset=state.assets[n.id];const img=asset&&image(asset.url);
      const selected=n.id===state.selected,focused=n.status==='FOCUSED',cashflow=n.status==='ACTIVE_CASHFLOW';
      ctx.fillStyle=selected?'rgba(249,217,149,.4)':focused?'rgba(218,237,156,.25)':cashflow?'rgba(121,200,193,.3)':'rgba(8,30,29,.3)';
      ctx.beginPath();ctx.ellipse(point.x,point.y+5*scale,60*scale,28*scale,0,0,Math.PI*2);ctx.fill();
      if(selected||focused||cashflow){
        ctx.strokeStyle=selected?'#f7dc9f':cashflow?'#79c8c1':'#d2e49f';ctx.lineWidth=selected?2:1;
        ctx.beginPath();ctx.ellipse(point.x,point.y+5*scale,60*scale,28*scale,0,0,Math.PI*2);ctx.stroke();
      }
      ctx.globalAlpha=n.status==='Queued'?.78:n.status==='DISABLED'?.35:1;
      if(img?.complete&&img.naturalWidth&&!img.failed)ctx.drawImage(img,point.x-64*scale,point.y-128*scale,128*scale,160*scale);
      else iso.drawAsset(ctx,'sovereign_'+(n.kind==='agent'?'agent':n.status==='Queued'?'mine':'tower'),point,scale,ctx.globalAlpha);
      ctx.globalAlpha=1;
      n.screen=point;
    }
    if(state.bio.fog){ctx.fillStyle=`rgba(13,24,23,${state.bio.fog})`;ctx.fillRect(0,0,width,height);}
    ctx.font='500 11px system-ui';
    for(const {node:n,box} of layoutLabels(items,state.selected,hovered,scale,text=>ctx.measureText(text).width)){
      const selected=n.id===state.selected,focused=n.status==='FOCUSED',cashflow=n.status==='ACTIVE_CASHFLOW',p=n.screen;
      ctx.font='500 11px system-ui';ctx.textAlign='center';
      n.labelBox=box;const {w,h}=box;
      ctx.fillStyle=selected?'rgba(21,42,35,.97)':'rgba(12,31,30,.87)';
      ctx.strokeStyle=selected?'#e5c58b':focused?'rgba(210,228,159,.65)':cashflow?'#79c8c1':'rgba(205,218,191,.17)';ctx.lineWidth=1;
      ctx.beginPath();ctx.roundRect(box.x,box.y,w,h,5);ctx.fill();ctx.stroke();
      ctx.fillStyle=selected?'#f5deae':'#e4ebd8';ctx.fillText(labelFor(n),p.x,box.y+13,w-12);
      ctx.font='9px system-ui';ctx.fillStyle=focused?'#d2e49f':cashflow?'#79c8c1':'#afc3b6';
      ctx.fillText(`W${n.wave} · ${n.status}`,p.x,box.y+23);
    }
  }
  function target(event){
    if(!view)return;const bounds=canvas.getBoundingClientRect();
    const x=(event.clientX-bounds.left)*view.width/bounds.width,y=(event.clientY-bounds.top)*view.height/bounds.height;
    const hit=pickProject(items,x,y,view.scale);
    const tile=iso.clickTarget(x,y,{heights:Array.from({length:12},()=>Array(12).fill(0))},view.scale,view.origin);
    return hit||items.find(n=>tile&&n.x===tile.x&&n.y===tile.y);
  }
  canvas.addEventListener('click',event=>{const n=target(event);if(n)onSelect(n.id);});
  canvas.addEventListener('pointermove',event=>{const node=target(event),id=node?.id||null;if(id!==hovered){hovered=id;canvas.style.cursor=id?'pointer':'default';canvas.title=node?labelFor(node):'';draw();}});
  canvas.addEventListener('pointerleave',()=>{hovered=null;canvas.style.cursor='default';canvas.title='';draw();});
  new ResizeObserver(draw).observe(canvas);
  return {update(next){state=next;draw();},zoom(delta){zoom=Math.max(.65,Math.min(1.4,zoom+delta));draw();}};
}
