// AI assistance: written with OpenAI Codex from the author's task
// descriptions; reviewed and modified by the author. See AI_USE.md.
export function accountTime(value:string|null|undefined,empty='Never') {
 if(!value)return empty;
 const timestamp=new Date(value);
 return Number.isNaN(timestamp.getTime())?'Unavailable':timestamp.toLocaleString();
}
