import {useEffect,useState} from 'react';
import {api,errorMessage} from '../api/client';
import type {LessonPage} from '../api/types';
import {StatusBadge} from './StatusBadge';

export function LessonVersions({lessonId,onSelect}:{lessonId:string;onSelect:(id:string)=>void}){
  const [page,setPage]=useState(1);const [attempt,setAttempt]=useState(0);
  const [state,setState]=useState<{page:number;data?:LessonPage;error?:unknown}>({page:0});
  useEffect(()=>{
    const controller=new AbortController();
    void api.request<LessonPage>(`/api/lessons?lesson_id=${encodeURIComponent(lessonId)}&page=${page}`,'GET',undefined,controller.signal).then(data=>{if(!controller.signal.aborted)setState({page,data});}).catch(error=>{if(!controller.signal.aborted)setState({page,error});});
    return()=>controller.abort();
  },[lessonId,page,attempt]);
  const current=state.page===page?state:undefined;
  return <section><h3>Version history</h3>{current?.error?<div role="alert"><p>{errorMessage(current.error)}</p><button onClick={()=>setAttempt(value=>value+1)}>Retry versions</button></div>:!current?.data?<p role="status">Loading versions…</p>:<><ul className="lesson-versions">{current.data.items.map(item=><li key={item.id}><button onClick={()=>onSelect(item.id)}>Version {item.revision}</button> <StatusBadge status={item.status}/><span>{item.proposer??item.proposer_id}{item.self_approved?' · self-approved':''}</span></li>)}</ul><nav className="actions" aria-label="Lesson version pages"><button disabled={page===1} onClick={()=>setPage(value=>value-1)}>Previous versions</button><span>Page {page} of {Math.max(1,Math.ceil(current.data.total/25))}</span><button disabled={page*25>=current.data.total} onClick={()=>setPage(value=>value+1)}>Next versions</button></nav></>}</section>;
}
