import type { RunEvent } from '../api/types';
import { WindowedRows } from './WindowedRows';
export function LiveLog({events}:{events:RunEvent[]}){
 return <section className="panel log"><h2>Live log</h2>{events.length?<WindowedRows count={events.length} follow label="Live event log" row={index=>{const event=events[index]!;return <div className="log-row" key={event.seq}><time className="muted" dateTime={event.timestamp}>{new Date(event.timestamp).toLocaleTimeString(undefined,{hour12:false})}</time> <span className={event.status==='failed'?'danger-text':'running-text'}>[{event.kind}]</span> <span>{event.agent}{event.variant?` (${event.variant})`:''}: {(event.message??event.status).replace(/[\r\n]+/g,' ')}</span></div>;}}/>:<p className="muted">Waiting for events…</p>}</section>;
}
