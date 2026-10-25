import {useEffect,useRef,useState,type KeyboardEvent} from 'react';
import {Link,useSearchParams} from 'react-router';
import {api,ApiError,errorMessage} from '../api/client';
import type {LessonConfirmation,LessonControls,LessonDetail,LessonHistoryPage,LessonPage,LessonRevision} from '../api/types';
import {LessonForm} from '../components/LessonForm';
import {LessonPreview} from '../components/LessonPreview';
import {LessonVersions} from '../components/LessonVersions';
import {StatusBadge} from '../components/StatusBadge';
import {lessonRoles} from '../lib/lessonLabels';
import {categoryLabel} from '../lib/reviewCategories';
import {getSessionStatus} from '../lib/sessionState';

const tabs=[['proposed','Proposed'],['approved','Active'],['retired','Retired'],['history','History']] as const;
function utc(value:string){return new Intl.DateTimeFormat(undefined,{dateStyle:'short',timeStyle:'medium',timeZone:'UTC'}).format(new Date(value));}
function wrapDialogFocus(event:KeyboardEvent<HTMLDialogElement>){
  if(event.key!=='Tab')return;
  const controls=[...event.currentTarget.querySelectorAll<HTMLElement>('button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),summary,[tabindex]:not([tabindex="-1"])')].filter(element=>element.getClientRects().length>0);
  const first=controls[0];const last=controls.at(-1);
  if(first&&last&&((event.shiftKey&&document.activeElement===first)||(!event.shiftKey&&document.activeElement===last))){event.preventDefault();(event.shiftKey?last:first).focus();}
}
export function LessonsSettings(){
  const [params,setParams]=useSearchParams();const requested=params.get('tab');
  const tab=tabs.find(([id])=>id===requested)?.[0]??'proposed';
  const requestedPage=Number(params.get('page')??1);
  const page=Number.isSafeInteger(requestedPage)&&requestedPage>0?requestedPage:1;const selected=params.get('lesson');
  const account=getSessionStatus()?.user;
  const [attempt,setAttempt]=useState(0);const [detailAttempt,setDetailAttempt]=useState(0);
  const key=`${tab}:${page}`;
  const [state,setState]=useState<{key:string;control?:LessonControls;data?:LessonPage;history?:LessonHistoryPage;error?:unknown}>({key:''});
  const [detail,setDetail]=useState<{id:string;data?:LessonDetail;error?:unknown}>({id:''});
  const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);const [notice,setNotice]=useState('');
  const [editing,setEditing]=useState(false);const [confirmation,setConfirmation]=useState<LessonConfirmation|null>(null);
  const [destructive,setDestructive]=useState<{action:'reject'|'retire';id:string;text:string}|null>(null);
  const inspector=useRef<HTMLDialogElement>(null);const selfDialog=useRef<HTMLDialogElement>(null);const actionDialog=useRef<HTMLDialogElement>(null);
  const trigger=useRef<HTMLButtonElement|null>(null);const approveButton=useRef<HTMLButtonElement>(null);
  const heading=useRef<HTMLHeadingElement>(null);const detailHeading=useRef<HTMLHeadingElement>(null);
  const control=state.key===key?state.control:undefined;const current=state.key===key?state:undefined;
  const inspected=selected&&detail.id===selected?detail.data:undefined;
  useEffect(()=>{
    const controller=new AbortController();
    void Promise.all([api.request<LessonControls>('/api/lessons/control','GET',undefined,controller.signal),tab==='history'?api.request<LessonHistoryPage>(`/api/lessons/history?page=${page}`,'GET',undefined,controller.signal):api.request<LessonPage>(`/api/lessons?status=${tab}&page=${page}`,'GET',undefined,controller.signal)])
      .then(([control,data])=>{if(!controller.signal.aborted)setState({key,control,...(tab==='history'?{history:data as LessonHistoryPage}:{data:data as LessonPage})});})
      .catch(error=>{if(!controller.signal.aborted)setState({key,error});});
    return()=>controller.abort();
  },[tab,page,key,attempt]);
  useEffect(()=>{
    if(!selected)return;
    const controller=new AbortController();
    void api.request<LessonDetail>(`/api/lessons/${encodeURIComponent(selected)}`,'GET',undefined,controller.signal).then(data=>{if(!controller.signal.aborted)setDetail({id:selected,data});}).catch(error=>{if(!controller.signal.aborted)setDetail({id:selected,error});});
    return()=>controller.abort();
  },[selected,detailAttempt]);
  useEffect(()=>{
    if(selected&&!inspector.current?.open)inspector.current?.showModal();
    else if(!selected&&inspector.current?.open)inspector.current.close();
  },[selected]);
  useEffect(()=>{if(confirmation&&confirmation.lesson.id===selected&&!selfDialog.current?.open)selfDialog.current?.showModal();else if(confirmation?.lesson.id!==selected&&selfDialog.current?.open)selfDialog.current.close();},[confirmation,selected]);
  useEffect(()=>{if(destructive&&destructive.id===selected&&!actionDialog.current?.open)actionDialog.current?.showModal();else if(destructive?.id!==selected&&actionDialog.current?.open)actionDialog.current.close();},[destructive,selected]);
  function choose(id:string|null){setParams(previous=>{const next=new URLSearchParams(previous);if(id)next.set('lesson',id);else next.delete('lesson');return next;});setEditing(false);setError(null);}
  function filter(name:string,value:string){setParams(previous=>{const next=new URLSearchParams(previous);next.set(name,value);if(name==='tab'){next.delete('page');next.delete('lesson');}return next;});setEditing(false);setError(null);}
  function refresh(){setAttempt(value=>value+1);setDetailAttempt(value=>value+1);}
  async function toggle(enabled:boolean){if(busy)return;setBusy(true);setError(null);try{const updated=await api.request<LessonControls>('/api/lessons/control','PUT',{enabled});setState(previous=>({...previous,control:updated}));setNotice(enabled?'Approved lessons enabled for newly accepted runs.':'Lessons disabled. Active runs cannot resume lessons.');}catch(cause){setError(cause);}finally{setBusy(false);}}
  async function act(action:'approve'|'reject'|'retire',token?:string){
    if(busy||!inspected)return;
    if((token&&confirmation?.lesson.id!==inspected.lesson.id)||(action!=='approve'&&destructive?.id!==inspected.lesson.id)){setError(new ApiError(409,'lesson_selection_changed','The selected lesson changed. Inspect it again before confirming.'));return;}
    setBusy(true);setError(null);
    try{
      const updated=await api.request<LessonRevision>(`/api/lessons/${inspected.lesson.id}/${action}`,'POST',token?{confirmation_token:token}:{});
      setDetail(previous=>previous.data&&previous.id===updated.id?{id:updated.id,data:{...previous.data,lesson:updated}}:previous);
      selfDialog.current?.close();actionDialog.current?.close();setConfirmation(null);setDestructive(null);
      setNotice(`Lesson ${action==='approve'?'approved':action==='reject'?'rejected':'retired'}.`);refresh();detailHeading.current?.focus();
    }catch(cause){setError(cause);refresh();}
    finally{setBusy(false);}
  }
  async function approve(){
    if(!inspected||!control||busy)return;
    if(inspected.lesson.proposer_id===account?.id&&!control.require_second_approver){
      setBusy(true);setError(null);try{const value=await api.request<LessonConfirmation>(`/api/lessons/${inspected.lesson.id}/confirmation`,'POST');setConfirmation(value);}catch(cause){setError(cause);setDetailAttempt(value=>value+1);}finally{setBusy(false);}
    }else await act('approve');
  }
  const total=tab==='history'?current?.history?.total:current?.data?.total;
  const own=inspected?.lesson.proposer_id===account?.id;
  return <section aria-label="Lessons"><h2 ref={heading} tabIndex={-1}>Lessons</h2>
    <p>Curated reviewer preferences are advisory. Approved content and version history remain traceable.</p>
    {control&&<section className="panel lesson-controls" aria-label="Lesson runtime control">
      <div><h3>{control.enabled?'Lessons enabled':'Lessons disabled'}</h3><p>Active set v{control.set_version} · {control.lesson_count} {control.lesson_count===1?'lesson':'lessons'}</p><p>SHA-256: <code className="lesson-hash">{control.set_hash}</code></p></div>
      <div><label className="checkbox"><input type="checkbox" checked={control.runtime_enabled} disabled={busy||!control.server_enabled} onChange={event=>void toggle(event.target.checked)}/>Use approved lessons</label><button disabled={busy} className="destructive" onClick={()=>void toggle(false)}>Disable lessons{busy?'…':''}</button>
      {!control.server_enabled&&<p className="muted">The server gate is off. LESSONS_ENABLED must be true on the server before this switch can enable lessons.</p>}</div>
    </section>}
    {control&&!control.require_second_approver&&<p className="notice warn" role="status">Four-eyes review is off. Administrators can self-approve only after a separate confirmation of the filter and prompt preview.</p>}
    {notice&&<p className="notice" role="status">{notice}</p>}
    {!selected&&!!error&&<p role="alert">{errorMessage(error)}</p>}
    <nav className="actions history-views" aria-label="Lesson views">{tabs.map(([id,label])=><button key={id} aria-pressed={tab===id} onClick={()=>filter('tab',id)}>{label}</button>)}</nav>
    {current?.error?<div role="alert"><p>{errorMessage(current.error)}</p><button onClick={refresh}>Retry lessons</button></div>:total===undefined?<p role="status">Loading lessons…</p>:<>
      {total===0?<p>{tab==='history'?'No lesson changes recorded.':`No ${tab==='approved'?'active':tab} lessons.`}</p>:<div className="history-table lesson-table"><table><caption className="sr-only">{tab==='history'?'Lesson audit history':'Lesson revisions'}</caption>
      {tab==='history'?<><thead><tr>{['Action','Actor','Timestamp (UTC)','Set','Revision'].map(label=><th key={label} scope="col">{label}</th>)}</tr></thead><tbody>{current?.history?.items.map(row=><tr key={row.id}><td>{row.action.replaceAll('_',' ')}</td><td>{typeof row.payload.actor==='string'?row.payload.actor:row.actor_id}</td><td>{utc(row.timestamp)}</td><td>{row.set_version===null?'unavailable':`v${row.set_version}`}</td><td>{row.revision_id?<button onClick={event=>{trigger.current=event.currentTarget;choose(row.revision_id);}}>Inspect revision</button>:'Runtime setting'}{row.payload.self_approved===true&&<span className="warn"> · self-approved</span>}</td></tr>)}</tbody></>:<><thead><tr>{['Lesson','Role','Category','Version','Proposer','Approval','Actions'].map(label=><th key={label} scope="col">{label}</th>)}</tr></thead><tbody>{current?.data?.items.map(row=><tr key={row.id}><td>{row.text}</td><td>{lessonRoles[row.scope_role]}</td><td>{categoryLabel(row.category)}</td><td>v{row.revision} · <StatusBadge status={row.status}/></td><td>{row.proposer??row.proposer_id}</td><td>{row.self_approved?<span className="warn">Self-approved</span>:row.approver??'Awaiting approval'}</td><td><button aria-label={`Inspect lesson: ${row.text}`} onClick={event=>{trigger.current=event.currentTarget;choose(row.id);}}>Inspect</button></td></tr>)}</tbody></>}
      </table></div>}
      <nav className="actions" aria-label="Lesson pages"><button disabled={page===1} onClick={()=>filter('page',String(page-1))}>Previous</button><span>Page {page} of {Math.max(1,Math.ceil(total/25))}</span><button disabled={page*25>=total} onClick={()=>filter('page',String(page+1))}>Next</button></nav>
    </>}
    <dialog onKeyDown={wrapDialogFocus} ref={inspector} className="lesson-inspector" aria-labelledby="lesson-inspector-title" onClose={()=>{choose(null);(trigger.current?.isConnected?trigger.current:heading.current)?.focus();}}>
      <div className="page-heading"><h2 ref={detailHeading} id="lesson-inspector-title" tabIndex={-1}>Lesson {inspected?`v${inspected.lesson.revision}`:''}</h2><button onClick={()=>inspector.current?.close()}>Close lesson</button></div>
      {detail.id===selected&&detail.error?<div role="alert"><p>{errorMessage(detail.error)}</p><button onClick={()=>setDetailAttempt(value=>value+1)}>Retry lesson</button></div>:!inspected?<p role="status">Loading lesson…</p>:<>
        <p>{inspected.lesson.text}</p><p><StatusBadge status={inspected.lesson.status}/> · {lessonRoles[inspected.lesson.scope_role]} · {categoryLabel(inspected.lesson.category)} · tags: {inspected.lesson.applies_to.join(', ')||'none'}</p>
        <p>Proposed by {inspected.lesson.proposer??inspected.lesson.proposer_id} · {utc(inspected.lesson.created_at)} (UTC)</p>
        {inspected.lesson.approver&&<p>Approved by {inspected.lesson.approver}{inspected.lesson.self_approved?' · self-approved; four-eyes review was off':''}</p>}
        <div className="lesson-detail-layout"><section><h3>Linked review decision</h3>{inspected.lesson.source_decision?<><Link to={`/settings/review-history?decision_id=${encodeURIComponent(inspected.lesson.decision_id)}`}>View source decision</Link><p>{inspected.lesson.source_decision.reviewer_name??'Reviewer not recorded'} · {inspected.lesson.source_decision.action??'Decision not recorded'} · {categoryLabel(inspected.lesson.source_decision.category)}</p><p className="lesson-reason">{inspected.lesson.source_decision.reason??'Reason not recorded'}</p></>:<p>Source decision unavailable.</p>}
          <h3>Changes from previous version</h3>{inspected.previous?<dl className="lesson-diff">{(['text','scope_role','category','applies_to'] as const).map(field=>{const before=String(inspected.previous![field]);const after=String(inspected.lesson[field]);return <div key={field}><dt>{field.replaceAll('_',' ')}{before!==after?' · changed':' · unchanged'}</dt>{before===after?<dd>{after||"none"}</dd>:<><dd><span>Previous: </span><del>{before||"none"}</del></dd><dd><span>Current: </span><ins>{after||"none"}</ins></dd></>}</div>;})}</dl>:<p>First version.</p>}
        </section><LessonPreview preview={inspected.preview} inactive={["retired","rejected"].includes(inspected.lesson.status)}/></div>
        {!!error&&<p role="alert">{errorMessage(error)}</p>}
        {own&&control?.require_second_approver&&inspected.lesson.status==='proposed'&&<p className="notice">A different named administrator must approve your proposal.</p>}
        <div className="actions">{inspected.lesson.status==='proposed'&&<><button ref={approveButton} disabled={busy||!control||!inspected.preview.filter_result.passed||(own&&control.require_second_approver)} onClick={()=>void approve()}>Approve lesson{busy?'…':''}</button><button disabled={busy} className="destructive" onClick={()=>setDestructive({action:'reject',id:inspected.lesson.id,text:inspected.lesson.text})}>Reject lesson</button></>}{inspected.lesson.status==='approved'&&<button disabled={busy} className="destructive" onClick={()=>setDestructive({action:'retire',id:inspected.lesson.id,text:inspected.lesson.text})}>Retire lesson</button>}{own&&<button disabled={busy} onClick={()=>setEditing(value=>!value)}>Propose new version</button>}</div>
        {editing&&<LessonForm key={inspected.lesson.id} decisionId={inspected.lesson.decision_id} initialRole={inspected.lesson.scope_role} initialCategory={inspected.lesson.category} previous={inspected.lesson} onCancel={()=>setEditing(false)} onProposed={row=>{setEditing(false);choose(row.id);setNotice('New lesson version proposed.');refresh();}}/>}
        <LessonVersions key={inspected.lesson.id} lessonId={inspected.lesson.lesson_id} onSelect={choose}/>
      </>}
    </dialog>
    <dialog onKeyDown={wrapDialogFocus} ref={selfDialog} className="lesson-confirmation" aria-labelledby="self-approval-title" onClose={()=>{setConfirmation(null);(approveButton.current??detailHeading.current)?.focus();}}>
      <h2 id="self-approval-title">Confirm self-approval</h2>{confirmation&&<><p className="notice warn">{confirmation.warning}</p><LessonPreview preview={confirmation.preview}/><p>Confirmation expires at {utc(confirmation.expires_at)} (UTC).</p>{!!error&&<p role="alert">{errorMessage(error)}</p>}<div className="actions"><button autoFocus disabled={busy} onClick={()=>selfDialog.current?.close()}>Cancel self-approval</button><button disabled={busy||!confirmation.preview.filter_result.passed} onClick={()=>void act('approve',confirmation.confirmation_token)}>Confirm self-approval{busy?'…':''}</button></div></>}
    </dialog>
    <dialog onKeyDown={wrapDialogFocus} ref={actionDialog} aria-labelledby="lesson-action-title" onClose={()=>{setDestructive(null);detailHeading.current?.focus();}}><h2 id="lesson-action-title">{destructive?.action==='retire'?'Retire':'Reject'} this lesson?</h2><p>{destructive?.text}</p><p>{destructive?.action==='retire'?'The lesson will be excluded from new runs. Use Disable lessons to stop later lesson use in active runs.':'This proposal will be rejected; its history remains available.'}</p>{!!error&&<p role="alert">{errorMessage(error)}</p>}<div className="actions"><button autoFocus disabled={busy} onClick={()=>actionDialog.current?.close()}>Cancel</button><button className="destructive" disabled={busy||!destructive} onClick={()=>destructive&&void act(destructive.action)}>Confirm {destructive?.action??'action'}</button></div></dialog>
  </section>;
}
