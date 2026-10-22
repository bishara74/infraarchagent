import { afterEach, expect, it, vi } from 'vitest';
import { api, ApiError, createApiClient, errorMessage, saveDownload } from './client';
import { getSessionStatus, getActiveRun, setSessionStatus, setActiveRun } from '../lib/sessionState';
afterEach(()=>{sessionStorage.clear();vi.useRealTimers();});
it('NFR-01 fresh key headers, resume cursor and request bodies',async()=>{
 const transport=vi.fn<typeof fetch>(async()=>new Response('{}')); const client=createApiClient({fetch:transport}); await client.openStream('run',new AbortController().signal,7);
 expect(new Headers(transport.mock.calls[0]?.[1]?.headers).get('Last-Event-ID')).toBe('7'); expect(new Headers(transport.mock.calls[0]?.[1]?.headers).get('X-API-Key')).toBeNull(); expect(transport.mock.calls[0]?.[1]?.credentials).toBe('same-origin'); await client.submitRun('text',{provider:'stub'}); expect(new Headers(transport.mock.calls[1]?.[1]?.headers).has('X-API-Key')).toBe(false); expect(JSON.parse(transport.mock.calls[1]?.[1]?.body as string)).toEqual({text:'text',config:{provider:'stub'}});
 await client.review('r','security',{action:'retry',feedback:'fix',target_files:['terraform/main.tf']}); expect(JSON.parse(transport.mock.calls[2]?.[1]?.body as string)).toEqual({action:'retry',feedback:'fix',target_files:['terraform/main.tf']});
});
it.each(['run_in_progress','not_pending_review','feedback_needs_target','nothing_to_retry','too_many_runs','not_downloadable'])('maps %s safely',async code=>{const client=createApiClient({fetch:vi.fn(async()=>new Response(JSON.stringify({error:code,message:'Safe response'}),{status:409}))}); await expect(client.getResults('x')).rejects.toMatchObject({status:409,code,message:'Safe response'}); expect(errorMessage(new Error('secret'))).not.toContain('secret');});
it('401 clears credentials, preserving active run',async()=>{setSessionStatus({auth_required:true,authenticated:true,mode:'shared_key'}); setActiveRun('run'); const client=createApiClient({fetch:vi.fn(async()=>new Response('{}',{status:401}))}); await expect(client.getResults('x')).rejects.toBeInstanceOf(ApiError); expect(getSessionStatus()?.authenticated).toBe(false); expect(getActiveRun()).toBe('run');});
it.each([false,true])('eventually releases download Blob URLs even when click fails: %s',async fail=>{
 vi.useFakeTimers();vi.spyOn(api,'download').mockResolvedValue({blob:new Blob(['zip']),filename:'package.zip'});
 Object.defineProperty(URL,'createObjectURL',{value:vi.fn(()=>'blob:test'),configurable:true});
 const revoke=vi.fn();Object.defineProperty(URL,'revokeObjectURL',{value:revoke,configurable:true});
 vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{if(fail)throw new Error('synthetic click failure');});
 if(fail)await expect(saveDownload('r','security')).rejects.toThrow('synthetic click failure');else await saveDownload('r','security');
 expect(revoke).not.toHaveBeenCalled();expect(document.querySelector('a[download]')).toBeNull();
 await vi.advanceTimersByTimeAsync(999);expect(revoke).not.toHaveBeenCalled();
 await vi.advanceTimersByTimeAsync(1);expect(revoke).toHaveBeenCalledExactlyOnceWith('blob:test');
});

it('FR-UI-01 finite JSON requests time out after 15 seconds without timing out SSE',async()=>{
 vi.useFakeTimers();
 const transport=vi.fn<typeof fetch>((_url,init)=>new Promise((_resolve,reject)=>init?.signal?.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')))));
 const client=createApiClient({fetch:transport});
 const pending=client.session();const assertion=expect(pending).rejects.toMatchObject({code:'request_timeout'});
 await vi.advanceTimersByTimeAsync(15000);await assertion;
 const controller=new AbortController();const stream=client.openStream('r',controller.signal);const aborted=expect(stream).rejects.toMatchObject({name:'AbortError'});
 await vi.advanceTimersByTimeAsync(30000);expect(controller.signal.aborted).toBe(false);controller.abort();await aborted;
});
