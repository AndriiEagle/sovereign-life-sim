import assert from 'node:assert/strict';
import test from 'node:test';
import {positions,labelFor} from '../engine-isometric-ui/emberglass.mjs';
test('live adapter places 100 stable IDs inside the original 12x12 world',()=>{
 const nodes=Array.from({length:100},(_,i)=>({id:'node-'+i,title:'Node '+i}));
 const placed=positions(nodes);assert.equal(new Set(placed.map(n=>`${n.x},${n.y}`)).size,100);
 assert.ok(placed.every(n=>n.x>=0&&n.x<12&&n.y>=0&&n.y<12));
 assert.deepEqual(positions(nodes.slice(0,16)),placed.slice(0,16));
 assert.equal(labelFor({id:'synera',title:'Synera'}),'Synera');
});
