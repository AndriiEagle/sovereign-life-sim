import assert from 'node:assert/strict';
import test from 'node:test';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {positions,labelFor,titleFor,syncProjectButtons,createMap,viewportFor,pickProject,layoutLabels} from '../engine-isometric-ui/emberglass.mjs';
test('live adapter places 100 stable IDs inside the original 12x12 world',()=>{
 const nodes=Array.from({length:100},(_,i)=>({id:'node-'+i,title:'Node '+i}));
 const placed=positions(nodes);assert.equal(new Set(placed.map(n=>`${n.x},${n.y}`)).size,100);
 assert.ok(placed.every(n=>n.x>=0&&n.x<12&&n.y>=0&&n.y<12));
 assert.deepEqual(positions(nodes.slice(0,16)),placed.slice(0,16));
 assert.equal(labelFor({id:'synera',title:'Synera'}),'Synera');
 const custom={id:'custom-node',title:'A user-created project with a long meaningful name'};
 assert.equal(titleFor(custom),custom.title);
 assert.ok(labelFor(custom).length<titleFor(custom).length);
});

test('crowded labels preserve selection and never cover one another',()=>{
 const nodes=[{id:'synera',title:'Synera',status:'FOCUSED',screen:{x:200,y:200}},
  {id:'new-bot',title:'New bot',status:'Queued',screen:{x:200,y:180}}];
 const labels=layoutLabels(nodes,'new-bot',null,.3,s=>s.length*6);
 assert.equal(labels.length,1);assert.equal(labels[0].node.id,'new-bot');
 const sparse=layoutLabels([nodes[0],{...nodes[1],screen:{x:400,y:200}}],'synera',null,.3,s=>s.length*6);
 assert.equal(sparse.length,2);
});

test('label plates and buildings select their actual project, empty scenery does not',()=>{
 const item={id:'synera',screen:{x:200,y:200},labelBox:{x:160,y:220,w:80,h:32}};
 assert.equal(pickProject([item],200,240,.5)?.id,'synera');
 assert.equal(pickProject([item],200,150,.5)?.id,'synera');
 assert.equal(pickProject([item],20,20,.5),undefined);
 assert.equal(viewportFor(900).height,600);
});

test('missing art keeps the map usable; high-DPI pixels do not move click targets',async()=>{
 const originals={window:globalThis.window,Image:globalThis.Image,ResizeObserver:globalThis.ResizeObserver};
 const context=vm.createContext({module:{exports:{}}});
 vm.runInContext(readFileSync(new URL('../engine-isometric-ui/reference-source/iso-kit-renderer.js',import.meta.url),'utf8'),context);
 const kit=context.module.exports;
 let fallbackSprites=0;const events={},selected=[];
 const ctx=new Proxy({measureText:s=>({width:s.length*6})},{get:(target,key)=>key in target?target[key]:()=>{}});
 const canvas={clientWidth:720,parentElement:{clientWidth:360,scrollLeft:0},dataset:{},style:{},getContext:()=>ctx,addEventListener:(name,fn)=>events[name]=fn,
  getBoundingClientRect:()=>({left:10,top:20,width:360,height:240})};
 try{
  globalThis.Image=class{complete=false;naturalWidth=0;}; // every image unavailable
  globalThis.ResizeObserver=class{observe(){}};
  globalThis.window={devicePixelRatio:2,EmberIsoKitRenderer:{...kit,init:async()=>{},drawAsset:()=>fallbackSprites++}};
  const map=await createMap(canvas,id=>selected.push(id));
  const nodes=[{id:'synera',title:'Synera',wave:1,status:'FOCUSED'}];
  map.update({nodes,assets:{},selected:'synera',bio:{fog:0}});
  assert.equal(canvas.width,1440);assert.equal(canvas.height,960);
  assert.equal(canvas.parentElement.scrollLeft,180,'the first mobile view should show the center of the world');
  canvas.parentElement.scrollLeft=50;
  map.update({nodes,assets:{},selected:'synera',bio:{fog:0}});
  assert.equal(canvas.parentElement.scrollLeft,50,'a refresh must preserve the user\'s pan position');
  assert.equal(canvas.dataset.artStatus,'fallback');assert.equal(fallbackSprites,2);
  const click=()=>{
   const view=viewportFor(720),p=kit.worldToScreen(1,1,0,view.scale,view.origin);
   events.click({clientX:10+p.x/2,clientY:20+(p.y-30*view.scale)/2});
  };
  click();assert.deepEqual(selected,['synera']);
  events.click({clientX:11,clientY:21});assert.deepEqual(selected,['synera']);
 }finally{Object.assign(globalThis,originals);}
});

// A small DOM stand-in checks identity; a real browser separately checks keyboard focus.
function projectContainer(){
 const make=()=>({dataset:{},children:[],childNodes:[],attributes:{},listeners:{},
  append(...children){this.childNodes.push(...children);this.children.push(...children.filter(c=>!('nodeValue' in c)));},
  setAttribute(key,value){this.attributes[key]=value;},
  addEventListener(key,fn){this.listeners[key]=fn;},
  remove(){const i=container.children.indexOf(this);if(i>=0)container.children.splice(i,1);if(container.ownerDocument.activeElement===this)container.ownerDocument.activeElement=null;}});
 const container={children:[],ownerDocument:{activeElement:null,createElement:make,createTextNode:value=>({nodeValue:value})},
  replaceChildren(...children){this.ownerDocument.activeElement=null;this.children=children;},
  insertBefore(child,before){const old=this.children.indexOf(child);if(old>=0){if(this.ownerDocument.activeElement===child)this.ownerDocument.activeElement=null;this.children.splice(old,1);}const i=this.children.indexOf(before);this.children.splice(i<0?this.children.length:i,0,child);}};
 return container;
}
test('state refresh retains the selected project button and its keyboard target',()=>{
 const container=projectContainer(),calls=[];
 const nodes=[{id:'synera',title:'Synera',status:'FOCUSED',wave:1},{id:'fiverr',title:'Fiverr',status:'Queued',wave:3}];
 syncProjectButtons(container,nodes,'synera',id=>calls.push(id));
 const original=container.children[1];
 container.ownerDocument.activeElement=original;
 syncProjectButtons(container,[nodes[0],{...nodes[1],status:'FOCUSED',wave:1}],'fiverr',id=>calls.push(id));
 assert.equal(container.children[1],original,'refresh must not remove the focused DOM button');
 assert.equal(container.ownerDocument.activeElement,original,'refresh must not detach the active keyboard target');
 assert.equal(original.attributes['aria-pressed'],'true');
 assert.equal(original.children[0].textContent,'W1 · FOCUSED');
 original.listeners.click();assert.deepEqual(calls,['fiverr']);
 syncProjectButtons(container,[nodes[1]],'fiverr',id=>calls.push(id));
 assert.deepEqual(container.children,[original]);
});
