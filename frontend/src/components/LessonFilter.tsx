// AI assistance: written with OpenAI Codex from the author's task
// descriptions; reviewed and modified by the author. See AI_USE.md.
import type {LessonFilterResult} from '../api/types';
export function LessonFilter({result}:{result:LessonFilterResult}){
  return <div className={result.passed?'lesson-filter ok':'lesson-filter danger'} role="status" aria-live="polite">
    <p>{result.passed?'Passed deterministic filter':'Blocked by deterministic filter'} · v{result.version}</p>
    {!result.passed&&<ul>{result.reasons.map(reason=><li key={reason.id}>{reason.message}</li>)}</ul>}
  </div>;
}
