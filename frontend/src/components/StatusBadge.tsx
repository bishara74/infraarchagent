export function statusLabel(status:string){return ({pending:'queued',completed:'complete'} as Record<string,string>)[status]??status.replaceAll('_',' ');}
export function StatusBadge({status,seq,testId}:{status:string;seq?:number;testId?:string}){
 const tone=['completed','checks_passed','valid','passed','resolved','clean','success'].includes(status)?'ok':['running','scanning','remediating','validating'].includes(status)?'running':['failed','invalid','validation_error','unresolved','rejected','CRITICAL','HIGH'].includes(status)?'danger':['engineer_approved','excepted','pending_review','warning','MEDIUM','partial_success'].includes(status)?'warn':'queued';
 return <span className={`badge ${tone}`} data-testid={testId} data-seq={seq}>{statusLabel(status)}</span>;
}
