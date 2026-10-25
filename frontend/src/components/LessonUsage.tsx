import type {LessonManifest,RunEvent} from '../api/types';
import {lessonUsage} from '../lib/lessonUsage';

export function LessonUsage({manifest,events=[]}:{manifest?:LessonManifest|null;events?:RunEvent[]}){
  const used=lessonUsage(manifest,events);
  const entries=manifest?.entries.filter(entry=>used.ids.includes(entry.id))??[];
  return <div className="lesson-usage">
    <p className="muted" data-testid="lesson-usage" aria-live="polite">Lessons used: {used.count?`set v${used.version} (${used.count} ${used.count===1?'lesson':'lessons'})`:'none'}</p>
    {used.selfApproved&&<p className="notice warn">Includes self-approved lessons; four-eyes review was off.</p>}
    {used.disabled&&<p className="muted">Lessons were disabled during this run.{used.count?' Earlier use remains recorded.':' No lessons were used.'}</p>}
    {(used.count>0||manifest?.recorded===false)&&<details><summary>Lesson provenance</summary>{manifest?.recorded===false?<p>Lesson configuration was not recorded for this run.</p>:<><p>Set v{used.version} · SHA-256: <code className="lesson-hash">{used.hash}</code></p>{entries.length>0&&<ol>{entries.map(entry=><li key={entry.id}>{entry.text}{entry.self_approved?' (self-approved)':''}</li>)}</ol>}</>}</details>}
  </div>;
}
