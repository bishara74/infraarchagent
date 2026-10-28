import type {PackageResult,PlanConflict} from '../api/types';
export function planConflictMessage(conflict:PlanConflict){
  if(conflict.message)return `${conflict.assessment==='unknown'?'Informational':'Plan conflict'}: ${conflict.message}`;
  return conflict.assessment==='unknown'?'Kept open: the exposure change could not be verified against the plan.':conflict.expected==='public'?"Kept open: required by the plan's internet exposure.":"Kept open: required by the plan's private exposure.";
}
export function PlanConformanceNotice({item,finding}:{item:PackageResult;finding?:Record<string,unknown>}){
  const conflicts=(item.plan_conflicts??[]).filter(row=>!finding||(row.rule_id===finding.rule_id&&row.resource===finding.resource&&row.file_path===finding.file_path));
  const notes=conflicts.filter(row=>row.assessment==='unknown'&&row.message);
  const visible=conflicts.filter(row=>!notes.includes(row));
  return <>{[...new Set(visible.map(planConflictMessage))].map(message=><p className="plan-conformance-notice" key={message}>{message}</p>)}{notes.length>0&&<details><summary>Plan conformance information ({notes.length})</summary>{[...new Set(notes.map(planConflictMessage))].map(message=><p className="muted" key={message}>{message}</p>)}</details>}</>;
}
