import {useSyncExternalStore} from 'react';
import {api,ApiError} from '../api/client';
import type {AgentChoice,RunConfig,ResultsResponse} from '../api/types';
export interface PreferenceData {prompt_draft:string;role_defaults:Record<string,AgentChoice>;draft_config:RunConfig;ui:{auto_scroll:boolean;config_open:boolean;report_tab:'security'|'validation'}}
export interface RecentRun {id:string;title:string;time:string;status:string;last_seq:number}
interface Stored {version:1;data:PreferenceData;recent:RecentRun[]}
const defaults=():PreferenceData=>({prompt_draft:'',role_defaults:{},draft_config:{},ui:{auto_scroll:true,config_open:false,report_tab:'security'}});
let owner='local';let generation=0;let timer:ReturnType<typeof setTimeout>|undefined;let saving=false;let dirty=false;
let state={data:defaults(),recent:[] as RecentRun[],revision:0,ready:true,status:'saved',conflictDraft:null as PreferenceData|null};
const listeners=new Set<()=>void>();
function notify(){listeners.forEach(fn=>fn());}
function scrub(text:string){return text.replace(/sk-(?:ant-)?[A-Za-z0-9_-]{16,}/g,'[REDACTED]').replace(/\bBearer\s+\S+/gi,'Bearer [REDACTED]');}
function validated(value:unknown):PreferenceData{
 if(!value||typeof value!=='object')return defaults();
 const input=value as Partial<PreferenceData>;const result=defaults();
 if(typeof input.prompt_draft==='string')result.prompt_draft=scrub(input.prompt_draft.slice(0,10000));
 for(const [role,choice] of Object.entries(input.role_defaults??{}))if(['architect','generators','fixer','generator_cost','generator_performance','generator_security'].includes(role)&&choice&&typeof choice.model==='string'&&(choice.thinking_mode==null||['off','low','medium','high'].includes(choice.thinking_mode)))result.role_defaults[role]={model:scrub(choice.model.slice(0,128)),thinking_mode:choice.thinking_mode};
 const config=input.draft_config;
 if(config&&typeof config==='object'){
  if(config.agent_models)result.draft_config.agent_models=validated({role_defaults:config.agent_models}).role_defaults;
  if(config.policy_profile==='strict'||config.policy_profile==='contextual-v1')result.draft_config.policy_profile=config.policy_profile;
  if(typeof config.max_iterations==='number'&&Number.isInteger(config.max_iterations)&&config.max_iterations>0)result.draft_config.max_iterations=config.max_iterations;
  if(['stub','openai','anthropic'].includes(config.provider??''))result.draft_config.provider=config.provider;
  if(typeof config.model==='string')result.draft_config.model=scrub(config.model.slice(0,128));
 }
 if(input.ui&&typeof input.ui==='object')result.ui={auto_scroll:input.ui.auto_scroll!==false,config_open:input.ui.config_open===true,report_tab:input.ui.report_tab==='validation'?'validation':'security'};
 return result;
}
function recentValue(value:unknown):RecentRun[]{return Array.isArray(value)?value.filter((v):v is RecentRun=>!!v&&typeof v.id==='string'&&typeof v.title==='string'&&typeof v.time==='string'&&typeof v.status==='string'&&Number.isSafeInteger(v.last_seq)&&v.last_seq>=0).slice(0,100).map(v=>({id:v.id,title:scrub(v.title.slice(0,120)),time:v.time,status:v.status,last_seq:v.last_seq})):[];}
function cache(){try{const value:Stored={version:1,data:validated(state.data),recent:recentValue(state.recent)};localStorage.setItem(`infraarch.preferences.v1.${owner}`,JSON.stringify(value));}catch{/* Cache is optional. */}}
function readCache(){try{const value=JSON.parse(localStorage.getItem(`infraarch.preferences.v1.${owner}`)??'null') as Stored|null;if(value?.version===1)return {data:validated(value.data),recent:recentValue(value.recent)};}catch{/* Invalid or blocked storage. */}return {data:defaults(),recent:[]};}
export const getPreferences=()=>state;
export const subscribePreferences=(fn:()=>void)=>{listeners.add(fn);return()=>{listeners.delete(fn);};};
export function usePreferences(){return useSyncExternalStore(subscribePreferences,getPreferences);}
export async function hydratePreferences(userId:string|null){
 clearTimeout(timer);owner=userId??'local';const active=++generation;dirty=false;state={...state,...readCache(),revision:0,ready:!userId,status:userId?'loading':'local',conflictDraft:null};notify();
 if(!userId)return;
 try{const [saved,recent]=await Promise.all([api.request<{revision:number;data:unknown}>('/api/me/preferences'),api.request<unknown>('/api/me/recent-runs')]);if(active!==generation)return;state={...state,data:validated(saved.data),recent:recentValue(recent),revision:saved.revision,status:'saved',ready:true};cache();}
 catch{if(active===generation)state={...state,ready:true,status:'offline'};}
 if(active===generation)notify();
}
async function save(){
 cache();if(owner==='local'||saving||!dirty)return;
 saving=true;dirty=false;const active=generation;const data=state.data;state={...state,status:'saving'};notify();
 try{const value=await api.request<{revision:number;data:PreferenceData}>('/api/me/preferences','PUT',{revision:state.revision,data});if(active!==generation)return;state={...state,revision:value.revision,status:'saved',...(dirty?{}:{data:validated(value.data)})};cache();}
 catch(error){if(active!==generation)return;if(error instanceof ApiError&&error.code==='preference_conflict'){const saved=await api.request<{revision:number;data:PreferenceData}>('/api/me/preferences');if(active!==generation)return;state={...state,data:validated(saved.data),revision:saved.revision,status:'conflict',conflictDraft:data};cache();dirty=false;}else{state={...state,status:'offline'};dirty=true;}}
 finally{saving=false;if(active===generation){notify();if(dirty&&state.status!=='offline')timer=setTimeout(()=>void save(),400);}}
}
export function updatePreferences(change:Partial<PreferenceData>){state={...state,data:validated({...state.data,...change})};dirty=true;clearTimeout(timer);timer=setTimeout(()=>void save(),400);notify();}
export function recoverDraft(){if(state.conflictDraft){const data=state.conflictDraft;state={...state,conflictDraft:null};updatePreferences(data);}}
export async function retrySave(){await save();}
export function cursorFor(runId:string){return state.recent.find(r=>r.id===runId)?.last_seq;}
const cursorTimers=new Map<string,ReturnType<typeof setTimeout>>();
export function rememberRun(runId:string,seq=0,results?:ResultsResponse){
 const previous=state.recent.find(r=>r.id===runId);const row:RecentRun={id:runId,title:results?.run.input_text.slice(0,120)??previous?.title??'Infrastructure request',time:results?.run.start_time??previous?.time??new Date().toISOString(),status:results?.run.status??previous?.status??'running',last_seq:Math.max(seq,previous?.last_seq??0)};
 state={...state,recent:[row,...state.recent.filter(r=>r.id!==runId)].slice(0,100)};
 clearTimeout(cursorTimers.get(runId));const active=generation;cursorTimers.set(runId,setTimeout(()=>{if(active!==generation)return;cache();if(owner!=='local')void api.request(`/api/me/recent-runs/${encodeURIComponent(runId)}`,'PUT',{seq:row.last_seq}).catch(()=>undefined);},250));
}
