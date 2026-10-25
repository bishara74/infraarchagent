import {useEffect,useRef,useState} from 'react';
import {api,errorMessage} from '../api/client';
import type {LessonFilterResult,LessonInput,LessonRevision,LessonRole,LessonTag,ReviewCategory} from '../api/types';
import {lessonRoles,lessonTags} from '../lib/lessonLabels';
import {reviewCategories} from '../lib/reviewCategories';
import {LessonFilter} from './LessonFilter';

interface CheckResult {normalized_text:string|null;filter_result:LessonFilterResult}
export function LessonForm({decisionId,initialRole,initialCategory,previous,onProposed,onCancel}:{
  decisionId:string;initialRole:LessonRole;initialCategory:ReviewCategory;
  previous?:LessonRevision;onProposed:(lesson:LessonRevision)=>void;onCancel:()=>void;
}){
  const [role,setRole]=useState<LessonRole>(previous?.scope_role??initialRole);
  const [category,setCategory]=useState<ReviewCategory>(previous?.category??initialCategory);
  const [tags,setTags]=useState<LessonTag[]>(previous?.applies_to??[]);
  const [text,setText]=useState(previous?.text??'');
  const [busy,setBusy]=useState(false);const [error,setError]=useState<string|null>(null);
  const [check,setCheck]=useState<{key:string;data?:CheckResult;error?:unknown}|null>(null);
  const textField=useRef<HTMLTextAreaElement>(null);const focusAfter=useRef(false);
  const input:LessonInput={scope_role:role,category,applies_to:tags,text};
  const key=JSON.stringify(input);const count=Array.from(text.normalize('NFKC').trim()).length;
  const current=check?.key===key?check:null;
  useEffect(()=>{
    if(!text.trim())return;
    const controller=new AbortController();
    const timer=setTimeout(()=>{
      void api.request<CheckResult>('/api/lessons/check','POST',JSON.parse(key),controller.signal)
        .then(data=>{if(!controller.signal.aborted)setCheck({key,data});})
        .catch(error=>{if(!controller.signal.aborted)setCheck({key,error});});
    },300);
    return()=>{clearTimeout(timer);controller.abort();};
  },[key,text]);
  useEffect(()=>{if(!busy&&focusAfter.current){focusAfter.current=false;textField.current?.focus();}},[busy]);
  async function submit(){
    if(busy)return;
    if(!count||count>280){setError('Use one plain-text lesson of 1–280 characters.');textField.current?.focus();return;}
    setBusy(true);setError(null);
    try{
      const checked=await api.request<CheckResult>('/api/lessons/check','POST',input);
      setCheck({key,data:checked});
      if(!checked.filter_result.passed){setError('Revise the lesson using the filter feedback.');focusAfter.current=true;return;}
      const proposed=await api.request<LessonRevision>('/api/lessons','POST',{...input,decision_id:decisionId,...(previous?{previous_id:previous.id}:{})});
      onProposed(proposed);
    }catch(cause){setError(errorMessage(cause));focusAfter.current=true;}
    finally{setBusy(false);}
  }
  return <form className="panel settings-form lesson-form" noValidate onSubmit={event=>{event.preventDefault();void submit();}}>
    <h3>{previous?'Propose a new lesson version':'Propose a lesson'}</h3>
    <p>Write one short reviewer preference. An administrator must approve it before it can be used.</p>
    <fieldset disabled={busy}><legend className="sr-only">Lesson proposal</legend>
      <div className="lesson-fields"><label>Lesson role<select aria-label="Lesson role" name="lesson_role" value={role} onChange={event=>setRole(event.target.value as LessonRole)}>{Object.entries(lessonRoles).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
      <label>Lesson category<select aria-label="Lesson category" name="lesson_category" value={category} onChange={event=>setCategory(event.target.value as ReviewCategory)}>{Object.entries(reviewCategories).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label></div>
      <fieldset className="lesson-tags"><legend>Applies to (optional curation tags)</legend>{lessonTags.map(tag=><label className="checkbox" key={tag}><input type="checkbox" name="lesson_tags" value={tag} checked={tags.includes(tag)} onChange={event=>setTags(previous=>event.target.checked?[...previous,tag].sort():previous.filter(value=>value!==tag))}/>{tag.replaceAll('_',' ')}</label>)}</fieldset>
      <label>Lesson text<textarea aria-label="Lesson text" ref={textField} name="lesson_text" rows={3} value={text} aria-describedby="lesson-text-help lesson-count" aria-invalid={count>280||undefined} onChange={event=>{setText(event.target.value);setError(null);}}/></label>
      <p id="lesson-count" className={count>280?'danger':'muted'}>{count} / 280 characters after normalization</p>
      <p id="lesson-text-help" className="muted">Use one line of plain text. Links, code, hidden characters and instruction overrides are rejected. Tags support curation; selection uses the lesson role.</p>
    </fieldset>
    {current?.data&&<LessonFilter result={current.data.filter_result}/>}
    {!!current?.error&&<p className="danger" role="status">{errorMessage(current.error)} Use one line of 1–280 characters.</p>}
    {error&&<p role="alert">{error}</p>}
    <div className="actions"><button type="submit" disabled={busy}>{previous?'Propose new version':'Submit lesson proposal'}{busy?'…':''}</button><button type="button" disabled={busy} onClick={onCancel}>Cancel proposal</button></div>
  </form>;
}
