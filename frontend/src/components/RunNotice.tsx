import type { StreamState } from '../api/sse';
export function RunNotice({state,onReconnect}:{state:StreamState;onReconnect:()=>void}){
 return state==='paused'?<p className="notice" role="status">Live updates paused, <button onClick={onReconnect}>Reconnect</button></p>:state==='reconnecting'?<p className="muted" role="status">Reconnecting live updates…</p>:null;
}
