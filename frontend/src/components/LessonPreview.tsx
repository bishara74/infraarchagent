import type {LessonPreview as Preview} from '../api/types';
import {lessonRoles} from '../lib/lessonLabels';
import {LessonFilter} from './LessonFilter';

export function LessonPreview({preview,inactive=false}:{preview:Preview;inactive?:boolean}){
  return <section aria-label="Exact lesson prompt preview">
    <LessonFilter result={preview.filter_result}/>
    <h3>{inactive?'Inactive revision preview':'Exact prompt preview'}</h3>{inactive&&<p className="notice">This revision is inactive. This hypothetical preview does not mean it is selected for new runs.</p>}<p className="muted">The advisory block appears only in the user message. Whole entries are limited to eight lessons and 2,000 characters per role.</p>
    {Object.entries(preview.roles).map(([role,value],index)=><details key={role} open={index===0}><summary>{lessonRoles[role as keyof typeof lessonRoles]??role} · {value.selected_ids.length} selected</summary>
      {!value.included&&<p className="notice warn">This revision is outside this role's current selection limit.</p>}
      <pre className="lesson-preview" tabIndex={0} aria-label={`${role} advisory block`}>{value.block||'No advisory block for this role.'}</pre>
    </details>)}
  </section>;
}
