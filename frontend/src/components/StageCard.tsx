import { useEffect,useState } from 'react';
import type { StageItem } from '../lib/runReducer';
import { StatusBadge } from './StatusBadge';
export function elapsed(start:string|null,end:string|null,now:number){if(!start)return '—';return `${Math.max(0,Math.floor(((end?Date.parse(end):now)-Date.parse(start))/1000))}s`;}
export function StageCard({name,stage,id,children}:{name:string;stage:StageItem;id:string;children?:React.ReactNode}){
 const [now,setNow]=useState(Date.now);useEffect(()=>{if(stage.status!=='running')return;const timer=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(timer);},[stage.status]);
 return <section className="panel stage"><div className="stage-heading"><h2>{name}</h2><StatusBadge status={stage.status} seq={stage.seq} testId={`stage-${id}`}/><time className="elapsed muted">{elapsed(stage.started,stage.ended,now)}</time></div><p className="muted stage-message" title={stage.message??undefined}>{stage.message??'Waiting to start'}</p>{children}</section>;
}
