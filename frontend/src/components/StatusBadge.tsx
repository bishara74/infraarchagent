import {Icon} from './Icon';
export function statusLabel(status:string){return ({pending:'queued',completed:'complete'} as Record<string,string>)[status]??status.replaceAll('_',' ');}
export function StatusBadge({status,seq,testId}:{status:string;seq?:number;testId?:string}){
 const tone=status==='engineer_approved'?'engineer-approved':['completed','checks_passed','valid','passed','resolved','clean','success','active','approved'].includes(status)?'ok':['running','scanning','remediating','validating'].includes(status)?'running':['failed','invalid','validation_error','unresolved','rejected','CRITICAL','HIGH','disabled'].includes(status)?'danger':['excepted','pending_review','warning','MEDIUM','partial_success'].includes(status)?'warn':'queued';
 return <span className={`badge ${tone}`} data-testid={testId} data-seq={seq}>{status==='engineer_approved'&&<Icon name="person"/>}{statusLabel(status)}</span>;
}
