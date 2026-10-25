import {useState} from 'react';
import type {LessonRole,PackageResult} from '../api/types';
import {getSessionStatus} from '../lib/sessionState';
import {LessonForm} from './LessonForm';

export function LessonProposalAction({item}:{item:PackageResult}){
  const [open,setOpen]=useState(false);const [proposed,setProposed]=useState(false);
  const account=getSessionStatus()?.user;const decision=item.review_decision;
  if(!account||!decision?.decision_id||decision.user_id!==account.id||decision.identity_basis!=='authenticated account')return null;
  return <section className="lesson-proposal" aria-label="Optional lesson proposal">
    {proposed&&<p role="status">Lesson proposed for administrator review.</p>}
    {!open?<button onClick={()=>{setOpen(true);setProposed(false);}}>Propose a lesson</button>:<LessonForm decisionId={decision.decision_id} initialRole={`generator_${item.variant}` as LessonRole} initialCategory={decision.category??'other'} onCancel={()=>setOpen(false)} onProposed={()=>{setOpen(false);setProposed(true);}}/>}
  </section>;
}
