import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router';
import { api, errorMessage } from '../api/client';
import type { AgentChoice, CatalogModel } from '../api/types';
import { getSessionStatus } from '../lib/sessionState';
import { usePreferences, updatePreferences, registerBrowserSecret } from '../lib/preferences';
import { UsersSettings } from './UsersSettings';
import { AccountSettings } from './AccountSettings';
import { PasswordField } from '../components/PasswordField';
import { Icon, type IconName } from '../components/Icon';
import {useModelCatalog} from '../hooks/useModelCatalog';
import {CatalogNotice} from '../components/CatalogNotice';
import { ModelControls } from '../components/ModelControls';
interface Credential {
    id: string;
    provider: string;
    label: string;
    base_url: string;
    last4: string;
    revoked: boolean;
}
interface Providers {
    storage_enabled: boolean;
    default_credential_id: string | null;
    credentials: Credential[];
}
export function ProviderPage() {
    const revokeDialog=useRef<HTMLDialogElement>(null);
    const revokeTrigger=useRef<HTMLButtonElement|null>(null);
    const [revoking,setRevoking]=useState<Credential|null>(null);
    const [saved, setSaved] = useState<Providers | null>(null);
    const [provider, setProvider] = useState('openrouter');
    const [url, setUrl] = useState('');
    const [label, setLabel] = useState('My provider');
    const [key, setKey] = useState('');
    const [probe, setProbe] = useState<{
        status: string;
        models: CatalogModel[];
    } | null>(null);
    const [error, setError] = useState<unknown>(null);
    const [busy, setBusy] = useState(false);
    const [probing, setProbing] = useState(false);
    const probeController = useRef<AbortController | null>(null);
    const working = busy || probing;
    function resetProbe() { probeController.current?.abort(); setProbing(false); setProbe(null); setError(null); }
    const [retry, setRetry] = useState(0);
    const [probeDelay, setProbeDelay] = useState(300);
    const refresh = useCallback(() => api.request<Providers>('/api/providers').then(setSaved).catch(setError), []);
    useEffect(() => { void refresh(); }, [refresh]);
    useEffect(() => { if (key.trim().length < 8 || (provider === 'custom' && !url))
        return; const controller = new AbortController(); probeController.current = controller; const timer = setTimeout(() => { setProbe(null); setProbing(true); void api.request<{
        status: string;
        models: CatalogModel[];
    }>('/api/providers/probe', 'POST', { provider, base_url: url, label, api_key: key }, controller.signal).then(result => { if (!controller.signal.aborted) setProbe(result); }).catch(cause => { if (!controller.signal.aborted)
        setError(cause); }).finally(() => { if (!controller.signal.aborted)
        setProbing(false); }); }, probeDelay); return () => { clearTimeout(timer); controller.abort(); }; }, [provider, url, key, label, retry, probeDelay]);
    async function save() { setBusy(true); setError(null); try {
        const created = await api.request<{
            id: string;
        }>('/api/providers', 'POST', { provider, base_url: url, label, api_key: key });
        await api.request(`/api/providers/${created.id}/default`, 'POST');
        setKey('');
        resetProbe();
        updatePreferences({ draft_config: {} });
        await refresh();
    }
    catch (cause) {
        setError(cause);
    }
    finally {
        setBusy(false);
    } }
    async function action(path: string) { setBusy(true); try {
        const result = await api.request<{
            status?: string;
            models?: CatalogModel[];
        }>(path, 'POST');
        if (result.status)
            setProbe({ status: result.status, models: result.models ?? [] });
        await refresh();
    }
    catch (cause) {
        setError(cause);
    }
    finally {
        setBusy(false);
    } }
    return <><h2>LLM provider</h2><p>A provider key lets this application call language models using your provider account. It is separate from your InfraArchAgent password. <a href="https://openrouter.ai/settings/keys" target="_blank" rel="noreferrer">Create an OpenRouter key</a>; add provider credit if required.</p>{saved && !saved.storage_enabled && <div className="notice"><p>Credential storage is disabled. Export CREDENTIAL_ENCRYPTION_KEY in the backend environment, then restart. Generate a key outside this browser:</p><pre>python3 -c 'import base64,secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())'</pre></div>}<form className="panel settings-form" onSubmit={event => { event.preventDefault(); void save(); }}><h3>Add provider</h3><label>Provider<select value={provider} onChange={event => { resetProbe(); setProvider(event.target.value); setKey(''); }}><option value="openrouter">OpenRouter (recommended)</option><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option><option value="custom">Custom OpenAI-compatible endpoint</option></select></label>{provider === 'custom' && <label>Base URL<input type="url" value={url} onChange={event => { resetProbe(); setUrl(event.target.value); }} required/></label>}<label>Label<input value={label} onChange={event => { resetProbe(); setLabel(event.target.value); }} maxLength={120} required/></label><PasswordField label="Provider API key" autoComplete="off" minLength={8} onPaste={() => setProbeDelay(0)} onKeyDown={() => setProbeDelay(300)} value={key} onChange={event => { registerBrowserSecret(event.target.value); resetProbe(); setKey(event.target.value); }} required/><p role="status" className={probe?.status==='ok'?'status-line ok':probe?.status==='invalid'?'status-line danger':'status-line warn'}>{working ? 'Testing or saving…' : probe ? `Provider test: ${probe.status}${probe.status==='ok'?' — valid':probe.status==='no_credit'?' — no credit':''}. ${probe.models.length} models loaded.` : 'Enter a key to test it and load models automatically.'}</p>{probe?.status === 'invalid' && <p>Check the key or create a replacement at the provider.</p>}{probe?.status === 'no_credit' && <p className="notice">This key can be saved without credit. Add provider credit or raise its spending limit before generating.</p>}{probe?.status === 'unavailable' && <p>Check the endpoint and connection, then test again.</p>}<div className="actions"><button type="button" disabled={!key || working} onClick={() => setRetry(value => value + 1)}>Test</button><button className="primary" disabled={!saved?.storage_enabled || working || !['ok','no_credit'].includes(probe?.status??'')}>Save and use provider</button></div></form>{probe && <p>Catalog preview: {probe.models.slice(0, 10).map(m => m.name).join(', ')}{probe.models.length > 10 ? '…' : ''}</p>}<h2>Saved credentials</h2>{!saved&&!error&&<p role="status">Loading saved credentials…</p>}{saved?.credentials.length ? <ul className="credential-list">{saved.credentials.map(item => <li key={item.id}><strong>{item.label}</strong> · {item.provider} · •••• {item.last4} <span className={`badge ${item.revoked?'danger':saved.default_credential_id===item.id?'ok':'queued'}`}>{item.revoked ? 'revoked' : saved.default_credential_id === item.id ? 'selected' : 'available'}</span><div className="actions"><button disabled={busy || item.revoked} onClick={() => void action(`/api/providers/${item.id}/test`)}>Test</button><button disabled={busy || item.revoked || saved.default_credential_id === item.id} onClick={() => void action(`/api/providers/${item.id}/default`)}>Use</button><button disabled={busy || item.revoked} onClick={event=>{revokeTrigger.current=event.currentTarget;setRevoking(item);revokeDialog.current?.showModal();}}>Revoke</button></div></li>)}</ul> : <p>No saved provider keys. Add one above.</p>}<button onClick={() => void action('/api/providers/environment')}>Use environment fallback</button>{error && <div role="alert"><p>{errorMessage(error)}</p><button onClick={()=>{setError(null);void refresh();}}>Retry</button></div>}<dialog ref={revokeDialog} aria-labelledby="revoke-title" onClose={()=>revokeTrigger.current?.focus()}><h2 id="revoke-title">Revoke {revoking?.label}?</h2><p>This credential will no longer be usable for new runs.</p><div className="actions"><button autoFocus onClick={()=>revokeDialog.current?.close()}>Cancel</button><button className="destructive" disabled={busy} onClick={()=>{if(revoking)void action(`/api/providers/${revoking.id}/revoke`).finally(()=>requestAnimationFrame(()=>revokeTrigger.current?.focus()));revokeDialog.current?.close();}}>Confirm revoke</button></div></dialog><p><Link to="/settings/models">Choose models and thinking modes</Link></p></>;
}
function ManualModel({ onAdd }: {
    onAdd: (item: Record<string, unknown>) => void;
}) {
    const [id, setId] = useState('');
    const [structured, setStructured] = useState(false);
    const [reasoning, setReasoning] = useState(false);
    const [modes, setModes] = useState<string[]>([]);
    return <form className="panel settings-form" onSubmit={event => { event.preventDefault(); onAdd({ id, name: id, capabilities: { structured_output: structured, reasoning, thinking_modes: reasoning ? modes : [] } }); setId(''); }}><h3>Declare model capabilities</h3><p>Use the provider's model documentation. Unknown capabilities cannot qualify an explicit model for any pipeline role.</p><label>Model ID<input required value={id} onChange={event => setId(event.target.value)} maxLength={128}/></label><label className="checkbox"><input type="checkbox" checked={structured} onChange={event => setStructured(event.target.checked)}/>Structured output supported</label><label className="checkbox"><input type="checkbox" checked={reasoning} onChange={event => setReasoning(event.target.checked)}/>Reasoning supported</label>{reasoning && <fieldset><legend>Supported thinking modes</legend>{['off', 'low', 'medium', 'high'].map(mode => <label className="checkbox" key={mode}><input type="checkbox" checked={modes.includes(mode)} onChange={event => setModes(previous => event.target.checked ? [...previous, mode] : previous.filter(m => m !== mode))}/>{mode}</label>)}</fieldset>}<button>Add to offline catalog</button></form>;
}
export function ModelsPage() {
    const prefs = usePreferences();
    const admin = getSessionStatus()?.user?.role === 'admin';
    const {catalog,error:catalogError,retry:retryCatalog}=useModelCatalog();
    const [global, setGlobal] = useState<Record<string, AgentChoice>>({});
    const [staticModels, setStatic] = useState<Record<string, unknown>[]>([]);
    const [error, setError] = useState<unknown>(null);
    const [notice, setNotice] = useState('');
    const load = useCallback(async () => { try {
        if (admin) {
            const settings = await api.request<{
                defaults: Record<string, AgentChoice>;
                static_models: Record<string, unknown>[];
            }>('/api/models/defaults');
            setGlobal(settings.defaults);
            setStatic(settings.static_models);
        }
    }
    catch (cause) {
        setError(cause);
    } }, [admin]);
    useEffect(() => { let active = true; void Promise.resolve().then(() => { if (active)
        void load(); }); return () => { active = false; }; }, [load]);
    async function saveGlobal(items = staticModels) { try {
        await api.request('/api/models/defaults', 'PUT', { defaults: global, static_models: items });
        setNotice('Global model settings saved.');
        await load();
        retryCatalog();
    }
    catch (cause) {
        setError(cause);
    } }
    return <><h2>Models and thinking</h2><CatalogNotice catalog={catalog} error={catalogError} retry={retryCatalog}/><p>Explicit request choices override personal defaults. Personal defaults override administrator defaults; environment settings supply the remaining roles. Per-generator choices take precedence over the Generators group. A null thinking mode uses the provider default.</p><section className="panel settings-form models-form"><h3>My defaults</h3><ModelControls catalog={catalog} defaults={{ ...catalog?.defaults }} value={prefs.data.role_defaults} onChange={role_defaults => updatePreferences({ role_defaults })}/><p role="status">Preferences: {prefs.status}</p></section>{admin && <section className="panel settings-form models-form"><h3>Administrator defaults</h3><ModelControls catalog={catalog} value={global} defaults={{}} onChange={setGlobal}/><button onClick={() => void saveGlobal()}>Save administrator defaults</button>{catalog?.provider==='custom'&&<details><summary>Declare model capabilities</summary><ManualModel onAdd={item => { const next = [...staticModels.filter(m => !(m.id === item.id && m.credential_id === catalog?.credential_id)), { ...item, credential_id: catalog?.credential_id ?? null }]; setStatic(next); void saveGlobal(next); }}/></details>}{staticModels.length > 0 && <button onClick={() => { setStatic([]); void saveGlobal([]); }}>Use live catalog</button>}</section>}{notice && <p role="status">{notice}</p>}{error && <div role="alert"><p>{errorMessage(error)}</p><button onClick={()=>{setError(null);void load();}}>Retry</button></div>}<p>Cost ranges describe illustrative initial calls; retries and remediation add cost. Unknown prices remain unavailable.</p></>;
}
const settingsIcons:Record<string,IconName>={provider:'key',models:'gear',users:'person',account:'account'};
export function SettingsScreen() { const { section } = useParams(); const admin = getSessionStatus()?.user?.role === 'admin'; const permitted = section === 'account' || section === 'models' || admin; return <><h1>Settings</h1><nav className="settings-nav" aria-label="Settings">{[['provider', 'Provider'], ['models', 'Models'], ['users', 'Users'], ['account', 'Account']].filter(([id]) => admin || id === 'models' || id === 'account').map(([id, label]) => <Link aria-current={section === id ? 'page' : undefined} key={id} to={`/settings/${id}`}><Icon name={settingsIcons[id!]!}/>{label}</Link>)}</nav>{!permitted ? <p>Ask an administrator to manage this setting.</p> : section === 'provider' ? <ProviderPage /> : section === 'models' ? <ModelsPage /> : section === 'users' ? <UsersSettings /> : section === 'account' ? <AccountSettings /> : <p>Select a setting above.</p>}</>; }
