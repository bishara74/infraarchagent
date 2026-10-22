import {usePreferences} from '../lib/preferences';
import type { RunEvent } from '../api/types';
import { Icon } from './Icon';
import { WindowedRows } from './WindowedRows';
const logTime = new Intl.DateTimeFormat(undefined, { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
export function LiveLog({events,live=true}:{events:RunEvent[];live?:boolean}){
 const preferences=usePreferences();
 return <section className="panel log"><h2 className="icon-label"><Icon name="terminal"/>Live log</h2>{events.length?<WindowedRows count={events.length} follow={preferences.data.ui.auto_scroll} label="Live event log" row={index=>{const event=events[index]!;return <div className="log-row" key={event.seq}><time className="muted" dateTime={event.timestamp}>{logTime.format(new Date(event.timestamp))}</time> <span className={event.status==='failed'?'danger-text':'running-text'}>[{event.status==='failed'?'ERROR':'INFO'}]</span> <span>{event.agent}{event.variant?` (${event.variant})`:''}: {(event.message??event.status).replace(/[\r\n]+/g,' ')}</span>{live&&index===events.length-1&&<span className="log-cursor" aria-hidden="true">█</span>}</div>;}}/>:<p className="muted">Waiting for events…</p>}</section>;
}
