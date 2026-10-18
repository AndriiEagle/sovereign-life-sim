import {createDurableQueue} from '../mcp-bridge/command-queue.mjs';

export function wasDemoShown(state){
  return state.flags.includes('demo_tested')&&['prepared','late'].includes(state.ending?.id);
}

export function createCommandQueue({send,storage,uuid=()=>crypto.randomUUID()}){
  return createDurableQueue({send,storage,uuid,key:'argon.pending.v1',
    acknowledged:(response,pending)=>response?.result?.accepted===true&&response.result.request_id===pending.request_id});
}
