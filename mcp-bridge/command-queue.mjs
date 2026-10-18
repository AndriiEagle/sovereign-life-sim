// Durable request IDs shared by the simulator and Argon. Persist before sending.
export function createDurableQueue({send,storage,key,acknowledged,uuid=()=>crypto.randomUUID()}){
  let pending=null;
  const stored=storage.getItem(key);
  if(stored){
    try{
      const value=JSON.parse(stored);
      if(typeof value.action!=='string'||typeof value.payload!=='object'||value.payload===null||
         typeof value.request_id!=='string'||!Number.isInteger(value.expected_revision))throw Error();
      pending=value;
    }catch{storage.removeItem(key);}
  }
  function clear(){pending=null;try{storage.removeItem(key);}catch{/* A persisted ID remains safe to replay. */}}
  async function transmit(){
    if(!pending)throw Error('Немає непідтвердженої дії');
    let response;
    try{
      try{response=await send(pending);}catch(error){if(error instanceof TypeError)response=await send(pending);else throw error;}
    }catch(error){
      if(error.status===400||(error.status===409&&error.stateView?.state))clear();
      throw error;
    }
    if(!acknowledged(response,pending))throw Error('Підтвердження дії не отримано. Повтори підтвердження.');
    clear();return response;
  }
  return {
    hasPending:()=>pending!==null,
    async execute(action,payload,revision){
      if(pending)throw Error('Спершу повтори підтвердження попередньої дії.');
      const next={action,payload:JSON.parse(JSON.stringify(payload)),request_id:uuid(),expected_revision:revision};
      storage.setItem(key,JSON.stringify(next));pending=next;
      return transmit();
    },
    retry:()=>transmit()
  };
}
