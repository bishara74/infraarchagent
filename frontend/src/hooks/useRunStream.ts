// AI assistance: written with OpenAI Codex from the author's task
// descriptions; reviewed and modified by the author. See AI_USE.md.
import { useEffect, useMemo, useSyncExternalStore } from 'react';
import { runStore } from '../lib/runStreamStore';

export function useRunStream(runId: string) {
  const store = useMemo(() => runStore(runId), [runId]);
  const state = useSyncExternalStore(store.subscribe, store.getSnapshot);
  useEffect(() => { store.acquire(); return () => store.release(); }, [store]);
  return { ...state, events: state.model.events, reconnect: store.start, reopenRetry: store.reopenRetry, refresh: store.refresh };
}
