import {afterEach,expect,it,vi} from 'vitest';
import {api,ApiError} from '../api/client';
import {getPreferences,hydratePreferences,updatePreferences,retrySave} from './preferences';
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
