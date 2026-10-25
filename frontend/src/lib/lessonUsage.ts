import type {LessonManifest,RunEvent} from '../api/types';

export function lessonUsage(manifest:LessonManifest|null|undefined,events:RunEvent[]=[]){
  const identities=new Set(manifest?.used_lesson_ids??[]);
  let version=manifest?.set_version??0;let hash=manifest?.set_hash??null;
  let selfApproved=manifest?.self_approved??false;let disabled=manifest?.disabled_during_run??false;
  for(const event of events){
    const candidates:unknown[]=event.payload.notice==='lesson use'?[event.payload.lessons]
      :event.payload.notice==='runtime telemetry'&&Array.isArray(event.payload.telemetry)?event.payload.telemetry.map((row:unknown)=>row&&typeof row==='object'&&'lesson_usage' in row?row.lesson_usage:null):[];
    for(const candidate of candidates){
      if(!candidate||typeof candidate!=='object')continue;
      const row=candidate as Record<string,unknown>;
      if(row.reason==='disabled_during_run')disabled=true;
      if(row.enabled!==true||!Array.isArray(row.lesson_ids))continue;
      for(const identity of row.lesson_ids)if(typeof identity==='string')identities.add(identity);
      if(typeof row.set_version==='number')version=row.set_version;
      if(typeof row.set_hash==='string')hash=row.set_hash;
      if(row.self_approved===true)selfApproved=true;
    }
  }
  return {ids:[...identities],count:identities.size,version,hash,selfApproved,disabled};
}
