import { expect, it, vi } from 'vitest';
import pending from '../test/fixtures/pending-results.json';
import recorded from '../test/fixtures/run.sse?raw';
import { ApiError } from './client';
import { createSseParser, eventFromFrame, isSettled, streamRun, abortableDelay } from './sse';
import type { ResultsResponse, RunEvent } from './types';
const snapshot = (): ResultsResponse => structuredClone(pending) as ResultsResponse;
const bytes = (value: string) => new TextEncoder().encode(value);
const response = (value = '') => new Response(new ReadableStream({ start(controller) { controller.enqueue(bytes(value)); controller.close(); } }),{headers:{'Content-Type':'text/event-stream'}});
const frame = (seq: number) => `id: ${seq}\nevent: run_status\ndata: ${JSON.stringify({ seq, kind: 'run_status', agent: 'orchestrator', status: 'partial_success', previous_status: 'running', message: 'é界', variant: null, timestamp: '2026-10-12T12:00:00Z', payload: {} })}\n\n`;
function harness(results = snapshot(), streams: (Response | Error)[] = [response()]) {
  const controller = new AbortController();
  const client = { openStream: vi.fn<(id: string, signal: AbortSignal, cursor?: number) => Promise<Response>>(async () => {
    const next = streams.shift();
    if (!next) { controller.abort(); throw new Error('Bounded stream response list exhausted'); }
    if (next instanceof Error) throw next;
    return next;
  }), getResults: vi.fn(async () => results) };
  return { runId: 'recorded', signal: controller.signal, controller, client, event: vi.fn(), state: vi.fn(), snapshot: vi.fn(), delay: vi.fn<(ms: number, signal: AbortSignal) => Promise<void>>(async () => undefined) };
}
it('FR-P-04 recorded UTF-8 stream byte by byte', () => {
 const events: RunEvent[] = []; const parser = createSseParser(value => events.push(eventFromFrame(value))); const decoder = new TextDecoder();
 for (const byte of bytes(recorded)) parser.feed(decoder.decode(new Uint8Array([byte]), { stream: true })); parser.feed(decoder.decode()); expect(events.length).toBeGreaterThan(10);
});
it('CRLF, Unicode, comments, multiline data and incomplete frames', () => {
 const emit=vi.fn(); const parser=createSseParser(emit); for(const value of ': comment\r\nid: 5\r\nevent: test\r\ndata: é\r\ndata: 界\r\n\r\ndata: unfinished') parser.feed(value);
 expect(emit).toHaveBeenCalledExactlyOnceWith({id:'5',event:'test',data:'é\n界'});
});
it.each(['scanning','remediating','validating'])('does not settle %s packages', status=>{const value=snapshot(); value.packages[0]!.status=status as ResultsResponse['packages'][number]['status']; expect(isSettled(value)).toBe(false);});
it('marker-only activity and nonterminal runs prevent settlement',()=>{const value=snapshot(); value.packages[0]!.retry_in_progress=true; expect(isSettled(value)).toBe(false); value.packages[0]!.retry_in_progress=false; value.run.status='running'; expect(isSettled(value)).toBe(false);});
it('settled EOF closes normally after one snapshot',async()=>{const h=harness(); await streamRun(h); expect(h.client.openStream).toHaveBeenCalledTimes(1); expect(h.client.getResults).toHaveBeenCalledTimes(1); expect(h.state).toHaveBeenLastCalledWith('closed');});
it('caps EOF retries; comments and duplicates cannot reset the counter',async()=>{
 const value=snapshot(); value.packages[0]!.retry_in_progress=true; const h=harness(value,Array.from({length:6},()=>response(': keepalive\n\n'+frame(9)))); await streamRun(h);
 expect(h.client.openStream,'EOF cap must stop after six opens despite duplicate seq values').toHaveBeenCalledTimes(6); expect(h.event,'Replayed seq values must be de-duplicated').toHaveBeenCalledTimes(1); expect(h.state).toHaveBeenLastCalledWith('paused'); expect(h.delay.mock.calls.map(call=>call[0])).toEqual([250,500,1000,2000,4000]);
},2000);
it('failed EOF snapshot cannot establish settlement',async()=>{const h=harness(snapshot(),Array.from({length:6},()=>response())); h.client.getResults.mockRejectedValue(new Error('offline')); await streamRun(h); expect(h.client.openStream,'Failed snapshots must still obey the EOF reconnect cap').toHaveBeenCalledTimes(6); expect(h.state).toHaveBeenLastCalledWith('paused'); expect(h.snapshot).not.toHaveBeenCalled();},2000);
it('reconnects on network failure and accepts ordered gaps',async()=>{const h=harness(snapshot(),[new Error('network'),response(frame(2)+frame(2)+frame(8))]); await streamRun(h); expect(h.event.mock.calls.map(call=>call[0].seq)).toEqual([2,8]); expect(h.delay).toHaveBeenCalledWith(250,h.signal);expect(h.client.openStream).toHaveBeenCalledTimes(2);expect(h.state).toHaveBeenLastCalledWith('closed');},2000);
it('retains cursor across reconnect, manual recovery and retry reopening',async()=>{
 const h=harness(snapshot(),[response(frame(15)),response(frame(14)+frame(20))]); const active=snapshot(); active.packages[0]!.retry_in_progress=true; h.client.getResults.mockResolvedValueOnce(active).mockResolvedValue(snapshot()); await streamRun(h);
 expect(h.client.openStream,'Cursor recovery should need exactly two streams').toHaveBeenCalledTimes(2);expect(h.state).toHaveBeenLastCalledWith('closed');expect(h.client.openStream.mock.calls[1]?.[2],'Reconnect must advance Last-Event-ID to accepted seq').toBe(15); expect(h.event.mock.calls.map(call=>call[0].seq)).toEqual([15,20]); const reopened=harness(); await streamRun({...reopened,cursor:20}); expect(reopened.client.openStream).toHaveBeenCalledTimes(1);expect(reopened.state).toHaveBeenLastCalledWith('closed');expect(reopened.client.openStream).toHaveBeenCalledWith('recorded',reopened.signal,20);
},2000);
it('unique events reset the EOF cap',async()=>{const active=snapshot(); active.packages[0]!.retry_in_progress=true; const h=harness(active,Array.from({length:8},(_,i)=>response(frame(i+1))));h.client.getResults.mockResolvedValue(snapshot());for(let i=0;i<7;i++)h.client.getResults.mockResolvedValueOnce(active);await streamRun(h);expect(h.client.openStream,'Each new seq must reset the EOF budget').toHaveBeenCalledTimes(8);expect(h.event.mock.calls.map(call=>call[0].seq)).toEqual([1,2,3,4,5,6,7,8]);expect(h.state).toHaveBeenLastCalledWith('closed');},2000);
it.each([401,400,404])('stops on HTTP %s',async status=>{const h=harness(); h.client.openStream.mockRejectedValue(new ApiError(status,'failed','safe')); await streamRun(h); expect(h.state).toHaveBeenLastCalledWith('error',expect.any(ApiError)); expect(h.delay).not.toHaveBeenCalled();});
it('stops malformed protocol data',async()=>{const h=harness(); h.client.openStream.mockResolvedValue(response('id: 1\nevent: run_status\ndata: {}\n\n')); await streamRun(h); expect(h.state).toHaveBeenLastCalledWith('error',expect.any(Error));});
it('aborts reader and backoff wait',async()=>{const h=harness(); const cancel=vi.fn(); h.client.openStream.mockResolvedValue(new Response(new ReadableStream({cancel}),{headers:{'Content-Type':'text/event-stream'}})); const running=streamRun(h); await vi.waitFor(()=>expect(h.state).toHaveBeenCalledWith('live')); h.controller.abort(); await running; expect(cancel).toHaveBeenCalled(); const controller=new AbortController(); const waiting=abortableDelay(8000,controller.signal); controller.abort(); await expect(waiting).rejects.toMatchObject({name:'AbortError'});});
it('network backoff reaches and retains its 8 second maximum',async()=>{const h=harness(snapshot(),[...Array.from({length:8},()=>new Error('offline')),response()]);await streamRun(h);expect(h.client.openStream).toHaveBeenCalledTimes(9);expect(h.state).toHaveBeenLastCalledWith('closed');expect(h.delay.mock.calls.map(call=>call[0])).toEqual([250,500,1000,2000,4000,8000,8000,8000]);},2000);
it('stops unexpected successful response protocols',async()=>{const h=harness();h.client.openStream.mockResolvedValue(new Response('HTML',{headers:{'Content-Type':'text/html'}}));await streamRun(h);expect(h.state).toHaveBeenLastCalledWith('error',expect.any(Error));expect(h.client.getResults).not.toHaveBeenCalled();});
