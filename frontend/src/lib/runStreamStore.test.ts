import { expect, it, vi } from 'vitest';
import { api } from '../api/client';
import pending from '../test/fixtures/pending-results.json';
import { runStore } from './runStreamStore';
import type { ResultsResponse } from '../api/types';
it('FR-P-04 shares one stream for consumers, retains events and aborts on final disposal',async()=>{
 const cancel=vi.fn(); vi.spyOn(api,'getResults').mockResolvedValue(pending as ResultsResponse); const open=vi.spyOn(api,'openStream').mockResolvedValue(new Response(new ReadableStream({cancel})));
 const store=runStore('shared-test'); expect(runStore('shared-test')).toBe(store); store.acquire(); store.acquire(); await vi.waitFor(()=>expect(store.getSnapshot().state).toBe('live')); expect(open).toHaveBeenCalledTimes(1); store.release(); expect(cancel).not.toHaveBeenCalled(); store.release(); await vi.waitFor(()=>expect(cancel).toHaveBeenCalledTimes(1)); expect(runStore('other-test').getSnapshot().results).toBeNull();
});
it('ignores snapshots completed after disposal',async()=>{
 let finish!:(value:ResultsResponse)=>void; vi.spyOn(api,'getResults').mockImplementation(()=>new Promise(resolve=>{finish=resolve;})); vi.spyOn(api,'openStream').mockResolvedValue(new Response(new ReadableStream()));
 const store=runStore('stale-test'); store.acquire(); await vi.waitFor(()=>expect(store.getSnapshot().state).toBe('live')); store.release(); finish(pending as ResultsResponse); await Promise.resolve(); expect(store.getSnapshot().results).toBeNull();
});
