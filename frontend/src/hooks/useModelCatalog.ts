import {useCallback,useEffect,useState,useSyncExternalStore} from 'react';
import {api} from '../api/client';
import type {Catalog} from '../api/types';
import {getSessionStatus,subscribeSession} from '../lib/sessionState';

/** Each screen revalidates on mount/account change; provider selection clears the server cache. */
export function useModelCatalog() {
 const session=useSyncExternalStore(subscribeSession,getSessionStatus);
 const owner=session?.user?.id??'local';
 const [attempt,setAttempt]=useState(0);
 const [state,setState]=useState<{owner:string;catalog:Catalog|null;error:unknown}>({owner,catalog:null,error:null});
 useEffect(()=>{
  const controller=new AbortController();
  void api.request<Catalog>(`/api/models${attempt?'?refresh=true':''}`,'GET',undefined,controller.signal).then(catalog=>{
   if(!controller.signal.aborted)setState({owner,catalog,error:null});
  }).catch(error=>{if(!controller.signal.aborted)setState({owner,catalog:null,error});});
  return()=>controller.abort();
 },[owner,attempt]);
 const retry=useCallback(()=>{setState({owner,catalog:null,error:null});setAttempt(n=>n+1);},[owner]);
 return {...(state.owner===owner?state:{catalog:null,error:null}),retry};
}
