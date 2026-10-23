import {afterEach,expect,it,vi} from 'vitest';
import {api,ApiError} from '../api/client';
import {getPreferences,hydratePreferences,updatePreferences,retrySave,discardPromptDraft} from './preferences';
afterEach(()=>{vi.restoreAllMocks();localStorage.clear();});
it('FR-UI-01 server preferences supersede browser cache across accounts',async()=>{
 vi.spyOn(api,'request').mockImplementation(async url=>url.endsWith('recent-runs')?[]:{revision:3,data:{prompt_draft:'server draft'}} as never);
 localStorage.setItem('infraarch.preferences.v1.user-a',JSON.stringify({version:1,data:{prompt_draft:'cached draft'},recent:[]}));
 await hydratePreferences('user-a');expect(getPreferences().data.prompt_draft).toBe('server draft');expect(getPreferences().revision).toBe(3);
 await hydratePreferences('user-b');expect(getPreferences().data.prompt_draft).toBe('server draft');
});
it('NFR-01 allowlisted cache excludes secrets and handles offline storage',async()=>{
 await hydratePreferences(null);updatePreferences({prompt_draft:'Bearer synthetic-test-value',...{password:'must-not-persist'}} as never);await retrySave();
 const stored=localStorage.getItem('infraarch.preferences.v1.local');expect(stored).not.toContain('synthetic-test-value');expect(stored).not.toContain('must-not-persist');
 vi.spyOn(Storage.prototype,'setItem').mockImplementation(()=>{throw new Error('blocked');});expect(()=>updatePreferences({prompt_draft:'safe draft'})).not.toThrow();await retrySave();
});
it('FR-UI-01 conflicting offline edits retain a recoverable draft',async()=>{
 const request=vi.spyOn(api,'request');request.mockImplementation(async url=>url.endsWith('recent-runs')?[]:{revision:1,data:{prompt_draft:'original'}} as never);
 await hydratePreferences('conflict-user');updatePreferences({prompt_draft:'unsaved draft'});
 request.mockImplementation(async(_url,method)=>{if(method==='PUT')throw new ApiError(409,'preference_conflict','changed');return {revision:2,data:{prompt_draft:'new server draft'}} as never;});
 await retrySave();expect(getPreferences().data.prompt_draft).toBe('new server draft');expect(getPreferences().conflictDraft?.prompt_draft).toBe('unsaved draft');
});

it('FR-UI-01 duplicate hydration shares requests and stale accounts cannot replace current data',async()=>{
 let finish!:(value:unknown)=>void;
 const request=vi.spyOn(api,'request').mockImplementation(url=> url.endsWith('recent-runs')?Promise.resolve([]) as never:new Promise(resolve=>{finish=resolve;}) as never);
 const first=hydratePreferences('deduplicated');const again=hydratePreferences('deduplicated');
 expect(first).toBe(again);expect(request).toHaveBeenCalledTimes(2);
 await hydratePreferences(null);finish({revision:1,data:{prompt_draft:'previous account'}});await first;
 expect(getPreferences().data.prompt_draft).toBe('');expect(getPreferences().ready).toBe(true);
});

it('FR-UI-01 failed hydration exposes retry and preserves populated recent rows',async()=>{
 const request=vi.spyOn(api,'request').mockRejectedValue(new Error('synthetic offline'));
 await hydratePreferences('offline-recent');expect(getPreferences().loadError).toBeTruthy();expect(getPreferences().ready).toBe(true);
 request.mockImplementation(async url=>(url.endsWith('recent-runs')?[{id:'run',title:'Real saved run',time:'2026-10-22T10:00:00Z',status:'success',last_seq:2}]:{revision:1,data:{}}) as never);
 await hydratePreferences('offline-recent',true);expect(getPreferences().loadError).toBeNull();expect(getPreferences().recent[0]?.title).toBe('Real saved run');
});

it('FR-UI-01 Discard waits for an in-flight autosave and persists the newer empty draft',async()=>{
 const request=vi.spyOn(api,'request').mockImplementation(async url=>(url.endsWith('recent-runs')?[]:{revision:1,data:{prompt_draft:'initial'},updated_at:'2026-10-23T10:00:00Z'}) as never);
 await hydratePreferences('queued-discard');let finish!:(value:unknown)=>void;let writes=0;
 request.mockImplementation((_url,_method,body)=>{writes++;if(writes===1)return new Promise(resolve=>{finish=resolve;}) as never;return Promise.resolve({revision:3,data:(body as {data:unknown}).data,updated_at:'2026-10-23T11:00:00Z'}) as never;});
 updatePreferences({prompt_draft:'pending autosave'});const pending=retrySave();const discard=discardPromptDraft();
 finish({revision:2,data:{prompt_draft:'pending autosave'},updated_at:'2026-10-23T10:30:00Z'});await pending;await discard;
 expect(writes).toBe(2);expect(getPreferences().data.prompt_draft).toBe('');expect(getPreferences().updatedAt).toBe('2026-10-23T11:00:00Z');
 expect(JSON.parse(localStorage.getItem('infraarch.preferences.v1.queued-discard')!).updatedAt).toBe('2026-10-23T11:00:00Z');
});
