// Adapter over the byte-preserved Emberglass renderer: owned atlas + live project DTOs.
const shortNames = {'game-forge':'Game Forge','brand-social-os':'Instagram','creator-income-os':'Creator OS','revenue-defense':'Revenue Defense','visual-voice-lab':'Voice Lab','agency-backlog':'Agency Lab','coiffeur-site':'Coiffeur','lego-godot':'LEGO / Godot','arcanum-card':'Card Forge','control-room':'Control Room','conductor':'Conductor','fiverr':'Fiverr / B2B','mirofish':'MiroFish','synera':'Synera','living-arcanum':'Living Arcanum','memento':'Memento'};
export const labelFor = node => shortNames[node.id] || node.title.slice(0,22);
export function positions(nodes) {
  const primary = Array.from({length:16},(_,i)=>({x:1+3*(i%4),y:1+3*Math.floor(i/4)}));
  const rest=[];
  for(let y=0;y<12;y++)for(let x=0;x<12;x++)if(!primary.some(p=>p.x===x&&p.y===y))rest.push({x,y});
  return nodes.map((n,i)=>({...n,...[...primary,...rest][i],z:0,zBias:0}));
}
export async function createMap(canvas,onSelect) {
  const iso=window.EmberIsoKitRenderer;
  if(!iso)throw new Error('Emberglass renderer unavailable');
  const ids=['sovereign_tile','sovereign_mine','sovereign_tower','sovereign_agent'];
  await iso.init({kitVersion:'emberglass-iso-kit-v1',atlas:{file:'atlas.svg'},
    promotedAssets:ids.map(assetId=>({assetId,qaStatus:'promoted',artStatus:'original-owned-geometric',pivot:{x:64,y:assetId==='sovereign_tile'?96:128}})),
    runtimeAssets:ids.map((assetId,i)=>({assetId,frame:{x:i*128,y:0,w:128,h:160}}))},'/engine-isometric-ui');
  const ctx=canvas.getContext('2d');let state=null,view=null,items=[],zoom=1;
  const images=new Map();
  function image(url) {
    if(!images.has(url)){
      const img=new Image();img.onload=draw;img.onerror=()=>{img.failed=true;draw();};img.src=url;images.set(url,img);
    }
    return images.get(url);
  }
  function draw(){
    if(!state)return;
    const width=Math.max(640,Math.min(1600,canvas.clientWidth||1100));
    canvas.width=width;canvas.height=Math.round(width*.62);
    const scale=Math.min(width/1680,canvas.height/1030)*zoom;
    const origin={x:width/2,y:100*width/1100};
    const cell={id:'sovereign',heights:Array.from({length:12},()=>Array(12).fill(0)),tiles:Array.from({length:12},()=>Array(12).fill(ids[0])),entities:[]};
    view=iso.render(ctx,{worldBand:'ground',backgroundAssetId:ids[0],cell,assets:[]},null,{scale,origin});
    items=positions(state.nodes).sort((a,b)=>a.x+a.y-b.x-b.y||a.id.localeCompare(b.id));
    for(const n of items){
      const point=iso.worldToScreen(n.x,n.y,0,scale,origin);
      const asset=state.assets[n.id];const img=asset&&image(asset.url);
      ctx.globalAlpha=n.status==='Queued'?.5:n.status==='DISABLED'?.25:1;
      if(img?.complete&&img.naturalWidth&&!img.failed)ctx.drawImage(img,point.x-64*scale,point.y-128*scale,128*scale,160*scale);
      else iso.drawAsset(ctx,'sovereign_'+(n.kind==='agent'?'agent':n.status==='Queued'?'mine':'tower'),point,scale,ctx.globalAlpha);
      ctx.globalAlpha=1;
      if(n.id===state.selected){ctx.strokeStyle='#e7c38a';ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(point.x,point.y+8*scale,53*scale,24*scale,0,0,Math.PI*2);ctx.stroke();}
      ctx.font=`${Math.max(9,12*scale)}px system-ui`;ctx.textAlign='center';ctx.fillStyle=n.status==='FOCUSED'?'#e3eabd':'#aab9aa';
      ctx.fillText(labelFor(n),point.x,point.y+48*scale,130*scale);
      ctx.fillStyle='#7f9988';ctx.font=`${Math.max(8,10*scale)}px system-ui`;ctx.fillText(`W${n.wave} · ${n.status}`,point.x,point.y+65*scale);
      n.screen=point;
    }
    if(state.bio.fog){ctx.fillStyle=`rgba(13,24,23,${state.bio.fog})`;ctx.fillRect(0,0,canvas.width,canvas.height);}
  }
  canvas.addEventListener('click',event=>{
    if(!view)return;const bounds=canvas.getBoundingClientRect();
    const x=(event.clientX-bounds.left)*canvas.width/bounds.width,y=(event.clientY-bounds.top)*canvas.height/bounds.height;
    const hit=[...items].reverse().find(n=>Math.abs(x-n.screen.x)<60*view.scale&&y>n.screen.y-125*view.scale&&y<n.screen.y+25*view.scale);
    const tile=iso.clickTarget(x,y,{heights:Array.from({length:12},()=>Array(12).fill(0))},view.scale,view.origin);
    const n=hit||items.find(n=>tile&&n.x===tile.x&&n.y===tile.y);if(n)onSelect(n.id);
  });
  new ResizeObserver(draw).observe(canvas);
  return {update(next){state=next;draw();},zoom(delta){zoom=Math.max(.65,Math.min(1.4,zoom+delta));draw();}};
}
