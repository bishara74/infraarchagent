import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { Link, useNavigate } from 'react-router';
import { api, errorMessage } from '../api/client';
import type { Catalog, RunConfig } from '../api/types';
import { examples } from '../constants/examples';
import { inputLength, MIN_INPUT, MAX_INPUT } from '../constants/inputRules';
import { useRunStream } from '../hooks/useRunStream';
import { getActiveRun, setActiveRun, subscribeSession } from '../lib/sessionState';
import { isSettled } from '../api/sse';
import { usePreferences, updatePreferences, rememberRun, recoverDraft, retrySave } from '../lib/preferences';
import { ModelControls } from '../components/ModelControls';
function ActiveRun({ id }: {
    id: string;
}) { const stream = useRunStream(id); useEffect(() => { if (stream.results && isSettled(stream.results))
    setActiveRun(null); }, [stream.results]); return <p role="status">A run is active. <Link to={`/runs/${id}`}>View progress</Link></p>; }
export function InputScreen() {
    const navigate = useNavigate();
    const active = useSyncExternalStore(subscribeSession, getActiveRun);
    const prefs = usePreferences();
    const value = prefs.data.prompt_draft;
    const config = prefs.data.draft_config;
    const [catalog, setCatalog] = useState<Catalog | null>(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<unknown>(null);
    const input = useRef<HTMLTextAreaElement>(null);
    useEffect(() => { const controller = new AbortController(); void api.request<Catalog>('/api/models', 'GET', undefined, controller.signal).then(setCatalog).catch(() => undefined); return () => controller.abort(); }, []);
    function configure(change: Partial<RunConfig>) { updatePreferences({ draft_config: { ...config, ...change } }); }
    async function submit() { if (busy || active)
        return; setBusy(true); setError(null); try {
        const result = await api.submitRun(value.trim(), config);
        rememberRun(result.run_id);
        setActiveRun(result.run_id);
        navigate(`/runs/${result.run_id}`);
    }
    catch (cause) {
        setError(cause);
        input.current?.focus();
    }
    finally {
        setBusy(false);
    } }
    if (!prefs.ready)
        return <p role="status">Loading saved preferences…</p>;
    return <><h1>Generate infrastructure</h1><p className="muted">Describe what you want to deploy in plain English. Compare the generated packages, checks and fixes before downloading.</p>{active && <ActiveRun id={active}/>}<p className="muted" role="status">Preferences: {prefs.status}</p>{prefs.status === 'offline' && <button onClick={() => void retrySave()}>Retry saving</button>}{prefs.conflictDraft && <p className="notice">Saved preferences changed elsewhere. <button onClick={recoverDraft}>Restore my unsaved draft</button></p>}{catalog?.status === 'setup_required' && <p className="notice">No provider key configured. <Link to="/settings/provider">Set up a provider</Link></p>}
 <form className="input-form" noValidate onSubmit={event => { event.preventDefault(); void submit(); }}><label className="sr-only" htmlFor="description">Infrastructure description</label><textarea ref={input} id="description" name="description" rows={6} value={value} onChange={event => updatePreferences({ prompt_draft: event.target.value })} placeholder="Describe your services, database, deployment and monitoring…" aria-describedby="input-count input-error" onKeyDown={event => { if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        void submit();
    } }}/><p id="input-count" className="counter muted">{inputLength(value)} / {MAX_INPUT} characters · minimum {MIN_INPUT}</p><p id="input-error" className="form-error" role="alert">{error ? errorMessage(error) : ''}</p>
 <details className="panel config" open={prefs.data.ui.config_open} onToggle={event => { if (event.currentTarget.open !== prefs.data.ui.config_open)
        updatePreferences({ ui: { ...prefs.data.ui, config_open: event.currentTarget.open } }); }}><summary>Configuration options</summary><div className="config-fields"><label>Secondary assessment<select value={config.policy_profile ?? 'strict'} onChange={event => configure({ policy_profile: event.target.value as 'strict' | 'contextual-v1' })}><option value="strict">Strict (default)</option><option value="contextual-v1">Contextual-v1 (experimental)</option></select></label><ModelControls catalog={catalog} value={config.agent_models ?? {}} defaults={{ ...catalog?.environment_defaults, ...catalog?.defaults, ...prefs.data.role_defaults }} onChange={agent_models => configure({ agent_models })}/><label>Max remediation iterations<input name="max_iterations" type="number" min={1} inputMode="numeric" value={config.max_iterations ?? ''} onChange={event => configure({ max_iterations: event.target.value ? Number(event.target.value) : undefined })} placeholder="Server default…"/></label></div></details>
 <button className="primary generate" type="submit" disabled={busy || !!active}>Generate{busy ? '…' : ''}</button>{busy && <span role="status" className="spinner">Submitting…</span>}</form><section className="examples"><h2>Example prompts</h2><div className="actions">{examples.map(example => <button key={example.label} onClick={() => { updatePreferences({ prompt_draft: example.text }); input.current?.focus(); }}>{example.label}</button>)}</div></section></>;
}
