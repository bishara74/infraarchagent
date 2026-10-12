import { api, ApiError } from './client';
import type { ResultsResponse, RunEvent } from './types';

export interface SseFrame { id: string | null; event: string; data: string }
export function createSseParser(emit: (frame: SseFrame) => void) {
  let buffer = ''; let id: string | null = null; let event = ''; let data: string[] = [];
  function line(value: string) {
    if (!value) {
      if (data.length) emit({ id, event: event || 'message', data: data.join('\n') });
      id = null; event = ''; data = []; return;
    }
    if (value.startsWith(':')) return;
    const colon = value.indexOf(':');
    const field = colon < 0 ? value : value.slice(0, colon);
    let content = colon < 0 ? '' : value.slice(colon + 1);
    if (content.startsWith(' ')) content = content.slice(1);
    if (field === 'data') data.push(content);
    else if (field === 'event') event = content;
    else if (field === 'id' && !content.includes('\0')) id = content;
  }
  return {
    feed(chunk: string) {
      buffer += chunk;
      let at: number;
      while ((at = buffer.search(/[\r\n]/)) >= 0) {
        if (buffer[at] === '\r' && at === buffer.length - 1) break;
        const length = buffer[at] === '\r' && buffer[at + 1] === '\n' ? 2 : 1;
        line(buffer.slice(0, at)); buffer = buffer.slice(at + length);
      }
    },
  };
}
const kinds = ['run_status', 'agent_state', 'plan_created', 'package_status', 'package_generated', 'stage_notice'];
export function eventFromFrame(frame: SseFrame): RunEvent {
  const data = JSON.parse(frame.data) as RunEvent;
  if (!Number.isSafeInteger(data.seq) || data.seq < 1 || frame.id !== String(data.seq)
    || frame.event !== data.kind || !kinds.includes(data.kind) || typeof data.agent !== 'string'
    || typeof data.status !== 'string' || typeof data.timestamp !== 'string'
    || !Number.isFinite(Date.parse(data.timestamp))
    || !(data.message === null || typeof data.message === 'string')
    || !(data.previous_status === null || typeof data.previous_status === 'string')
    || !(data.variant === null || ['cost', 'performance', 'security'].includes(data.variant))
    || !data.payload || typeof data.payload !== 'object' || Array.isArray(data.payload)) throw new Error('Invalid event frame.');
  return data;
}
export function isSettled(results: ResultsResponse) {
  return ['success', 'partial_success', 'failed'].includes(results.run.status)
    && results.packages.every(item => !['scanning', 'remediating', 'validating'].includes(item.status) && !item.retry_in_progress);
}
export type StreamState = 'connecting' | 'live' | 'reconnecting' | 'closed' | 'paused' | 'error';
export interface StreamOptions {
  runId: string; signal: AbortSignal; cursor?: number;
  event: (event: RunEvent) => void; snapshot: (results: ResultsResponse) => void;
  state: (state: StreamState, error?: unknown) => void;
  client?: Pick<typeof api, 'openStream' | 'getResults'>;
  delay?: (milliseconds: number, signal: AbortSignal) => Promise<void>;
}
export function abortableDelay(milliseconds: number, signal: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const abort = () => { clearTimeout(timer); signal.removeEventListener('abort', abort); reject(new DOMException('Aborted', 'AbortError')); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve(); }, milliseconds);
    signal.addEventListener('abort', abort, { once: true });
    if (signal.aborted) abort();
  });
}
export async function streamRun(options: StreamOptions) {
  const client = options.client ?? api; const delay = options.delay ?? abortableDelay;
  let cursor = options.cursor; let eofRetries = 0; let backoff = 0;
  while (!options.signal.aborted) {
    let protocolError = false;
    try {
      options.state(backoff ? 'reconnecting' : 'connecting');
      const response = await client.openStream(options.runId, options.signal, cursor);
      if (!response.body) throw new Error('No event stream.');
      options.state('live');
      const reader = response.body.getReader(); const decoder = new TextDecoder();
      const cancel = () => { void reader.cancel().catch(() => undefined); };
      options.signal.addEventListener('abort', cancel, { once: true });
      const parser = createSseParser(frame => {
        let event: RunEvent;
        try { event = eventFromFrame(frame); } catch { protocolError = true; throw new Error('Invalid event stream.'); }
        if (cursor !== undefined && event.seq <= cursor) return;
        options.event(event); cursor = event.seq; eofRetries = 0; backoff = 0;
      });
      try {
        while (!options.signal.aborted) {
          const chunk = await reader.read();
          if (chunk.done) { parser.feed(decoder.decode()); break; }
          parser.feed(decoder.decode(chunk.value, { stream: true }));
        }
      } finally { options.signal.removeEventListener('abort', cancel); await reader.cancel().catch(() => undefined); reader.releaseLock(); }
      if (options.signal.aborted) return;
      try {
        const results = await client.getResults(options.runId, options.signal);
        options.snapshot(results);
        if (isSettled(results)) { options.state('closed'); return; }
      } catch (error) {
        if (options.signal.aborted) return;
        if (error instanceof ApiError && error.status < 500) { options.state('error', error); return; }
      }
      if (eofRetries >= 5) { options.state('paused'); return; }
      eofRetries += 1;
    } catch (error) {
      if (options.signal.aborted) return;
      if (protocolError || (error instanceof ApiError && error.status < 500)) {
        options.state('error', error); return;
      }
    }
    options.state('reconnecting');
    try { await delay(Math.min(250 * 2 ** backoff++, 8000), options.signal); } catch { return; }
  }
}
