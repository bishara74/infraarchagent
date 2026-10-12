import { flushSync } from 'react-dom';
import { api } from '../api/client';
import { isSettled, streamRun, type StreamState } from '../api/sse';
import type { ResultsResponse, Variant } from '../api/types';
import { applySnapshot, initialModel, reduceEvent } from './runReducer';

function createStore(runId: string) {
  let value = { model: initialModel(), results: null as ResultsResponse | null, state: 'connecting' as StreamState, error: null as unknown, pendingRetries: [] as Variant[] };
  let controller: AbortController | null = null;
  let generation = 0; let users = 0; let refreshRevision = 0; let lease = 0;
  const listeners = new Set<() => void>();
  const update = (change: Partial<typeof value>) => { value = { ...value, ...change }; listeners.forEach(listener => listener()); };
  const store = {
    getSnapshot: () => value,
    subscribe(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; },
    async refresh() {
      const current = generation; const revision=++refreshRevision; const cursor=value.model.events.at(-1)?.seq;
      const result = await api.getResults(runId, controller?.signal);
      if (current === generation && revision===refreshRevision && cursor===value.model.events.at(-1)?.seq) update({ results: result, model: applySnapshot(value.model, result), error: null });
      return result;
    },
    start() {
      controller?.abort(); controller = new AbortController(); const current = ++generation;
      update({ error: null });
      void streamRun({ runId, signal: controller.signal, cursor: value.model.events.at(-1)?.seq,
        event: event => { if (current === generation) flushSync(() => update({ model: reduceEvent(value.model, event) })); },
        snapshot: result => { if (current === generation) { ++refreshRevision; update({ results: result, model: applySnapshot(value.model, result), pendingRetries: isSettled(result) ? [] : value.pendingRetries }); } },
        state: (state, error = null) => { if (current === generation) update({ state, error }); },
      });
    },
    reopenRetry(variant: Variant) {
      update({ pendingRetries: [...new Set([...value.pendingRetries, variant])] });
      store.start();
    },
    acquire() {
      if (users++ !== 0) return;
      const currentLease = ++lease;
      // Route replacement and StrictMode cleanup/setup transfer ownership in
      // the same turn. Do not issue requests for a discarded mount.
      queueMicrotask(() => {
        if (!users || currentLease !== lease || controller) return;
        store.start(); const current = generation;
        void store.refresh().catch(error => { if (current === generation) update({ error }); });
      });
    },
    release() {
      if (--users !== 0) return;
      const currentLease = ++lease;
      queueMicrotask(() => {
        if (users || currentLease !== lease) return;
        ++generation; controller?.abort(); controller = null;
      });
    },
  };
  return store;
}
const stores = new Map<string, ReturnType<typeof createStore>>();
export function runStore(runId: string) {
  let store = stores.get(runId);
  if (!store) { store = createStore(runId); stores.set(runId, store); }
  return store;
}
