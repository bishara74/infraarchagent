import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { Link, useNavigate } from 'react-router';
import { api, ApiError, errorMessage } from '../api/client';
import type { RunConfig } from '../api/types';
import { examples } from '../constants/examples';
import { inputLength, MIN_INPUT, MAX_INPUT } from '../constants/inputRules';
import { useRunStream } from '../hooks/useRunStream';
import { getActiveRun, setActiveRun, subscribeSession } from '../lib/sessionState';
import { isSettled } from '../api/sse';
import { usePreferences, updatePreferences, rememberRun, recoverDraft, retrySave, discardPromptDraft } from '../lib/preferences';
import {accountTime} from '../lib/accountTime';
import { Icon } from '../components/Icon';
import { defaultLabel, generatorRoles } from '../lib/modelDefaults';
import {useModelCatalog} from '../hooks/useModelCatalog';
import {CatalogNotice} from '../components/CatalogNotice';
import { ModelControls } from '../components/ModelControls';
function ActiveRun({ id }: {
    id: string;
}) { const stream = useRunStream(id); useEffect(() => { if (stream.results && isSettled(stream.results))
    setActiveRun(null); }, [stream.results]); return <p role="status">A run is active. <Link to={`/runs/${id}`}>View progress</Link></p>; }
export function InputScreen() {
    const navigate = useNavigate();
    const active = useSyncExternalStore(subscribeSession, getActiveRun);
    const prefs = usePreferences();
    const [value,setValue] = useState('');
    const [savedDraft] = useState(()=>({text:prefs.data.prompt_draft,time:prefs.updatedAt}));
    const [draftHidden,setDraftHidden] = useState(false);
    const [discarding,setDiscarding] = useState(false);
    const [draftError,setDraftError] = useState<unknown>(null);
    function editPrompt(text:string){setValue(text);setDraftHidden(true);updatePreferences({prompt_draft:text});}
    async function discard(){setDiscarding(true);setDraftError(null);try{await discardPromptDraft();setDraftHidden(true);}catch(cause){setDraftError(cause);}finally{setDiscarding(false);}}
    const config = prefs.data.draft_config;
    const {catalog,error:catalogError,retry:retryCatalog}=useModelCatalog();
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<unknown>(null);
    const input = useRef<HTMLTextAreaElement>(null);
    function configure(change: Partial<RunConfig>) { updatePreferences({ draft_config: { ...config, ...change } }); }
    async function submit() { if (busy || active)
        return; setBusy(true); setError(null); try {
        const result = await api.submitRun(value.trim(), config);
        rememberRun(result.run_id);
        setActiveRun(result.run_id);
        navigate(`/runs/${result.run_id}`);
    }
    catch (cause) {
        if(cause instanceof ApiError&&cause.code==='invalid_model') {
            setError(new ApiError(cause.status,cause.code,'Check the model and thinking fields in Configuration options. Choose a confirmed structured-output model for each role, or select Use defaults.'));
            updatePreferences({ui:{...prefs.data.ui,config_open:true}});
            requestAnimationFrame(()=>(document.querySelector<HTMLElement>('.model-choice [aria-invalid="true"]')??document.querySelector<HTMLElement>('.model-choice [role="combobox"]'))?.focus());
        } else { setError(cause); input.current?.focus(); }
    }
    finally {
        setBusy(false);
    } }
    const modelDefaults={...catalog?.defaults,...prefs.data.role_defaults};
    const summaryChoice=defaultLabel('architect',catalog,modelDefaults,config.agent_models??{},config);
    const roleLabels=['architect',...generatorRoles,'fixer'].map(role=>defaultLabel(role,catalog,modelDefaults,config.agent_models??{},config));
    const summary=`${Object.keys(config.agent_models??{}).length?'Configuration':'Defaults'}: ${roleLabels.every(label=>label===summaryChoice)?summaryChoice:'per-role models and thinking'} · ${config.policy_profile??'strict'}`;
    if (!prefs.ready)
        return <p role="status">Loading saved preferences…</p>;
    return <><h1>Generate infrastructure</h1><p className="muted">Describe what you want to deploy in plain English. Compare the generated packages, checks and fixes before downloading.</p>{active && <ActiveRun id={active}/>}<p className="muted" role="status">Preferences: {prefs.status}</p>{prefs.status === 'offline' && <button onClick={() => void retrySave()}>Retry saving</button>}{prefs.conflictDraft && <p className="notice">Saved preferences changed elsewhere. <button onClick={()=>{const text=prefs.conflictDraft?.prompt_draft??'';recoverDraft();setValue(text);setDraftHidden(true);}}>Restore my unsaved draft</button></p>}<CatalogNotice catalog={catalog} error={catalogError} retry={retryCatalog}/>
 <section className="variant-intro" aria-label="Generated variants"><p><Icon name="credit-card"/><strong>Cost</strong> Favour economical infrastructure.</p><p><Icon name="dashboard"/><strong>Performance</strong> Favour capacity and responsiveness.</p><p><Icon name="shield"/><strong>Security</strong> Favour protective controls.</p></section>
 <form className="input-form" noValidate onSubmit={event => { event.preventDefault(); void submit(); }}><label className="sr-only" htmlFor="description">Infrastructure description</label><textarea ref={input} id="description" name="description" rows={6} value={value} disabled={discarding} onChange={event => editPrompt(event.target.value)} placeholder="For example: deploy an AWS web service with a database, private networking, backups and monitoring…" aria-describedby="input-count input-error" onKeyDown={event => { if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        void submit();
    } }}/>{savedDraft.text&&!draftHidden&&!value&&<div className="draft-hint" role="status">You have an unsent draft{savedDraft.time?` from ${accountTime(savedDraft.time)}`:' from an earlier session'} — <button type="button" disabled={discarding} onClick={()=>{editPrompt(savedDraft.text);input.current?.focus();}}>Restore</button> · <button type="button" disabled={discarding} onClick={()=>void discard()}>{draftError?'Retry discard':'Discard'}</button><button type="button" disabled={discarding} aria-label="Dismiss draft hint" onClick={()=>setDraftHidden(true)}>Dismiss</button>{!!draftError&&<p role="alert">{errorMessage(draftError)}</p>}</div>}<p id="input-count" className="counter muted">{inputLength(value)} / {MAX_INPUT} characters · minimum {MIN_INPUT}</p><p id="input-error" className="form-error" role="alert">{error ? errorMessage(error) : ''}</p>
 <details className="panel config" open={prefs.data.ui.config_open} onToggle={event => { if (event.currentTarget.open !== prefs.data.ui.config_open)
        updatePreferences({ ui: { ...prefs.data.ui, config_open: event.currentTarget.open } }); }}><summary>Configuration options <span className="muted config-summary">{summary}</span></summary><div className="config-fields"><label>Additional assessment (experimental)<select aria-label="Additional assessment (experimental)" value={config.policy_profile ?? 'strict'} onChange={event => configure({ policy_profile: event.target.value as 'strict' | 'contextual-v1' })}><option value="strict">Strict (default)</option><option value="contextual-v1">Contextual-v1 (experimental)</option></select><span className="muted">Strict checks always decide the readiness label.</span></label><ModelControls catalog={catalog} value={config.agent_models ?? {}} defaults={modelDefaults} config={config} showReset={false} onChange={agent_models => configure({ agent_models })}/><label>Max remediation iterations<input name="max_iterations" type="number" min={1} inputMode="numeric" value={config.max_iterations ?? ''} onChange={event => configure({ max_iterations: event.target.value ? Number(event.target.value) : undefined })} placeholder={catalog?.server_default_max_iterations?`Server default: ${catalog.server_default_max_iterations}`:"Server default unavailable"}/></label></div></details>
 <div className="form-actions input-actions"><button type="button" onClick={()=>configure({agent_models:{}})}>Use defaults</button><button className="primary generate" type="submit" disabled={busy || !!active || discarding}>Generate{busy ? '…' : ''}</button>{busy && <span role="status" className="spinner">Submitting…</span>}</div></form><section className="examples"><h2>Example prompts</h2><div className="actions">{examples.map(example => <button key={example.label} disabled={discarding} onClick={() => { editPrompt(example.text); input.current?.focus(); }}>{example.label}</button>)}</div></section></>;
}
