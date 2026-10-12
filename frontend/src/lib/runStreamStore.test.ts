import { expect, it, vi } from 'vitest';
import { api } from '../api/client';
import pending from '../test/fixtures/pending-results.json';
import { runStore } from './runStreamStore';
import type { ResultsResponse } from '../api/types';
it('FR-P-04 shares one stream for consumers, retains events and aborts on final disposal',async()=>{
 const cancel=vi.fn(); vi.spyOn(api,'getResults').mockResolvedValue(pending as ResultsResponse); const open=vi.spyOn(api,'openStream').mockResolvedValue(new Response(new ReadableStream({cancel}),{headers:{'Content-Type':'text/event-stream'}}));
 const store=runStore('shared-test'); expect(runStore('shared-test')).toBe(store); store.acquire(); store.acquire(); await vi.waitFor(()=>expect(store.getSnapshot().state).toBe('live')); expect(open).toHaveBeenCalledTimes(1); store.release(); expect(cancel).not.toHaveBeenCalled(); store.release(); await vi.waitFor(()=>expect(cancel).toHaveBeenCalledTimes(1)); expect(runStore('other-test').getSnapshot().results).toBeNull();
});
it('ignores snapshots completed after disposal',async()=>{
 let finish!:(value:ResultsResponse)=>void; vi.spyOn(api,'getResults').mockImplementation(()=>new Promise(resolve=>{finish=resolve;})); vi.spyOn(api,'openStream').mockResolvedValue(new Response(new ReadableStream(),{headers:{'Content-Type':'text/event-stream'}}));
 const store=runStore('stale-test'); store.acquire(); await vi.waitFor(()=>expect(store.getSnapshot().state).toBe('live')); store.release(); finish(pending as ResultsResponse); await Promise.resolve(); expect(store.getSnapshot().results).toBeNull();
});
it('accepts successive frames synchronously and discards older snapshots',async()=>{
 let finish!:(value:ResultsResponse)=>void;vi.spyOn(api,'getResults').mockImplementation(()=>new Promise(resolve=>{finish=resolve;}));let push!:ReadableStreamDefaultController<Uint8Array>;vi.spyOn(api,'openStream').mockResolvedValue(new Response(new ReadableStream({start(controller){push=controller;}}),{headers:{'Content-Type':'text/event-stream'}}));const store=runStore('immediate-test');const states:string[]=[];const unsubscribe=store.subscribe(()=>{const status=store.getSnapshot().model.stages.architect?.status;if(status)states.push(status);});store.acquire();await vi.waitFor(()=>expect(store.getSnapshot().state).toBe('live'));const frame=(seq:number,status:string)=>`id: ${seq}\nevent: agent_state\ndata: ${JSON.stringify({seq,kind:'agent_state',agent:'architect',status,previous_status:null,message:status,variant:null,timestamp:'2026-10-12T12:00:00Z',payload:{}})}\n\n`;push.enqueue(new TextEncoder().encode(frame(1,'running')+frame(2,'completed')));await vi.waitFor(()=>expect(states).toEqual(['running','completed']));finish(pending as ResultsResponse);await Promise.resolve();expect(store.getSnapshot().results).toBeNull();store.release();unsubscribe();
});
