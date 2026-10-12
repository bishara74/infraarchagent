export function statusLabel(status:string){return status.replaceAll('_',' ');}
export function StatusBadge({status,seq,testId}:{status:string;seq?:number;testId?:string}){
 const tone=['completed','production_ready','valid','passed','resolved','clean','success'].includes(status)?'ok':['running','scanning','remediating','validating'].includes(status)?'running':['failed','invalid','validation_error','unresolved','not_production_ready','CRITICAL','HIGH'].includes(status)?'danger':['pending_review','warning','MEDIUM','partial_success'].includes(status)?'warn':'queued';
 return <span className={`badge ${tone}`} data-testid={testId} data-seq={seq}>{statusLabel(status)}</span>;
}
