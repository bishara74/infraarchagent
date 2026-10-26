import {ActionButton} from './ActionGate';
import {useState} from 'react';
import type {LessonRole,PackageResult} from '../api/types';
import {getSessionStatus} from '../lib/sessionState';
import {LessonForm} from './LessonForm';

export function LessonProposalAction({item}:{item:PackageResult}){
  const [open,setOpen]=useState(false);const [proposed,setProposed]=useState(false);
  const account=getSessionStatus()?.user;const decision=item.review_decision;
  if(!account||!decision?.decision_id||decision.user_id!==account.id||decision.identity_basis!=='authenticated account')return <ActionButton disabled unavailableReason={!decision?.decision_id?'No eligible engineer decision has been recorded.':'Only the named account that made this decision may propose a lesson.'} nextStep={!decision?.decision_id?'Sign in with a named account and record your own engineer review.':'Sign in as the decision owner or record your own review.'}>Propose a lesson</ActionButton>;
  return <section className="lesson-proposal" aria-label="Optional lesson proposal">
    {proposed&&<p role="status">Lesson proposed for administrator review.</p>}
    {!open?<button onClick={()=>{setOpen(true);setProposed(false);}}>Propose a lesson</button>:<LessonForm decisionId={decision.decision_id} initialRole={`generator_${item.variant}` as LessonRole} initialCategory={decision.category??'other'} onCancel={()=>setOpen(false)} onProposed={()=>{setOpen(false);setProposed(true);}}/>}
  </section>;
}
