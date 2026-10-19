import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router';
import { api, errorMessage } from '../api/client';
import type { AgentChoice, Catalog, CatalogModel } from '../api/types';
import { getSessionStatus } from '../lib/sessionState';
import { usePreferences, updatePreferences, registerBrowserSecret } from '../lib/preferences';
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
    const [retry, setRetry] = useState(0);
    const [probeDelay, setProbeDelay] = useState(300);
    const refresh = useCallback(() => api.request<Providers>('/api/providers').then(setSaved).catch(setError), []);
    useEffect(() => { void refresh(); }, [refresh]);
    useEffect(() => { if (key.trim().length < 8 || (provider === 'custom' && !url))
        return; const controller = new AbortController(); const timer = setTimeout(() => { setProbe(null); setBusy(true); void api.request<{
        status: string;
        models: CatalogModel[];
    }>('/api/providers/probe', 'POST', { provider, base_url: url, label, api_key: key }, controller.signal).then(result => { if (!controller.signal.aborted) setProbe(result); }).catch(cause => { if (!controller.signal.aborted)
        setError(cause); }).finally(() => { if (!controller.signal.aborted)
        setBusy(false); }); }, probeDelay); return () => { clearTimeout(timer); controller.abort(); }; }, [provider, url, key, label, retry, probeDelay]);
    async function save() { setBusy(true); setError(null); try {
        const created = await api.request<{
            id: string;
        }>('/api/providers', 'POST', { provider, base_url: url, label, api_key: key });
        await api.request(`/api/providers/${created.id}/default`, 'POST');
        setKey('');
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
    return <><h2>LLM provider</h2><p>A provider key lets this application call language models using your provider account. It is separate from your InfraArchAgent password. <a href="https://openrouter.ai/settings/keys" target="_blank" rel="noreferrer">Create an OpenRouter key</a>; add provider credit if required.</p>{saved && !saved.storage_enabled && <div className="notice"><p>Credential storage is disabled. Export CREDENTIAL_ENCRYPTION_KEY in the backend environment, then restart. Generate a key outside this browser:</p><pre>python3 -c 'import base64,secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())'</pre></div>}<form className="panel settings-form" onSubmit={event => { event.preventDefault(); void save(); }}><label>Provider<select value={provider} onChange={event => { setProvider(event.target.value); setKey(''); }}><option value="openrouter">OpenRouter (recommended)</option><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option><option value="custom">Custom OpenAI-compatible endpoint</option></select></label>{provider === 'custom' && <label>Base URL<input type="url" value={url} onChange={event => setUrl(event.target.value)} required/></label>}<label>Label<input value={label} onChange={event => setLabel(event.target.value)} maxLength={120} required/></label><label>Provider API key<input type="password" autoComplete="off" minLength={8} onPaste={() => setProbeDelay(0)} onKeyDown={() => setProbeDelay(300)} value={key} onChange={event => { registerBrowserSecret(event.target.value); setKey(event.target.value); setProbe(null); setBusy(false); setError(null); }} required/></label><p role="status">{busy ? 'Testing or saving…' : probe ? `Provider test: ${probe.status}. ${probe.models.length} models loaded.` : 'Enter a key to test it and load models automatically.'}</p>{probe?.status === 'invalid' && <p>Check the key or create a replacement at the provider.</p>}{probe?.status === 'no_credit' && <p>Add provider credit or raise its spending limit before generating.</p>}{probe?.status === 'unavailable' && <p>Check the endpoint and connection, then test again.</p>}<div className="actions"><button type="button" disabled={!key || busy} onClick={() => setRetry(value => value + 1)}>Test</button><button className="primary" disabled={!saved?.storage_enabled || busy || probe?.status !== 'ok'}>Save and use provider</button></div></form>{probe && <p>Catalog preview: {probe.models.slice(0, 10).map(m => m.name).join(', ')}{probe.models.length > 10 ? '…' : ''}</p>}<h2>Saved credentials</h2>{saved?.credentials.length ? <ul className="credential-list">{saved.credentials.map(item => <li key={item.id}><strong>{item.label}</strong> · {item.provider} · ending {item.last4} · {item.revoked ? 'revoked' : saved.default_credential_id === item.id ? 'selected' : 'available'}<div className="actions"><button disabled={busy || item.revoked} onClick={() => void action(`/api/providers/${item.id}/test`)}>Test saved key</button><button disabled={busy || item.revoked || saved.default_credential_id === item.id} onClick={() => void action(`/api/providers/${item.id}/default`)}>Use provider</button><button disabled={busy || item.revoked} onClick={() => void action(`/api/providers/${item.id}/revoke`)}>Revoke</button></div></li>)}</ul> : <p>No saved provider keys. Add one above.</p>}<button onClick={() => void action('/api/providers/environment')}>Use environment fallback</button>{error && <p role="alert">{errorMessage(error)}</p>}<p><Link to="/settings/models">Choose models and thinking modes</Link></p></>;
}
function ManualModel({ onAdd }: {
    onAdd: (item: Record<string, unknown>) => void;
}) {
    const [id, setId] = useState('');
    const [structured, setStructured] = useState(false);
    const [reasoning, setReasoning] = useState(false);
    const [modes, setModes] = useState<string[]>([]);
    return <form className="panel settings-form" onSubmit={event => { event.preventDefault(); onAdd({ id, name: id, capabilities: { structured_output: structured, reasoning, thinking_modes: reasoning ? modes : [] } }); setId(''); }}><h3>Declare model capabilities</h3><p>Use the provider's model documentation. Unknown capabilities cannot qualify a Generator or Fixer.</p><label>Model ID<input required value={id} onChange={event => setId(event.target.value)} maxLength={128}/></label><label className="checkbox"><input type="checkbox" checked={structured} onChange={event => setStructured(event.target.checked)}/>Structured output supported</label><label className="checkbox"><input type="checkbox" checked={reasoning} onChange={event => setReasoning(event.target.checked)}/>Reasoning supported</label>{reasoning && <fieldset><legend>Supported thinking modes</legend>{['off', 'low', 'medium', 'high'].map(mode => <label className="checkbox" key={mode}><input type="checkbox" checked={modes.includes(mode)} onChange={event => setModes(previous => event.target.checked ? [...previous, mode] : previous.filter(m => m !== mode))}/>{mode}</label>)}</fieldset>}<button>Add to offline catalog</button></form>;
}
export function ModelsPage() {
    const prefs = usePreferences();
    const admin = getSessionStatus()?.user?.role === 'admin';
    const [catalog, setCatalog] = useState<Catalog | null>(null);
    const [global, setGlobal] = useState<Record<string, AgentChoice>>({});
    const [staticModels, setStatic] = useState<Record<string, unknown>[]>([]);
    const [error, setError] = useState<unknown>(null);
    const [notice, setNotice] = useState('');
    const load = useCallback(async () => { try {
        const value = await api.request<Catalog>('/api/models');
        setCatalog(value);
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
    }
    catch (cause) {
        setError(cause);
    } }
    return <><h2>Models and thinking</h2><p>Choose personal defaults or leave each role on its configured default. A selected model shows its supported thinking modes, context and pricing.</p>{!catalog?.models.length && <p>No models available. <Link to="/settings/provider">Set up a provider</Link> or ask an administrator to configure an offline catalog.</p>}<section className="panel settings-form"><h3>My defaults</h3><ModelControls catalog={catalog} defaults={{ ...catalog?.environment_defaults, ...catalog?.defaults }} value={prefs.data.role_defaults} onChange={role_defaults => updatePreferences({ role_defaults })}/><p role="status">Preferences: {prefs.status}</p></section>{admin && <section className="settings-form"><h3>Administrator defaults</h3><ModelControls catalog={catalog} value={global} defaults={catalog?.environment_defaults} onChange={setGlobal}/><button onClick={() => void saveGlobal()}>Save administrator defaults</button><ManualModel onAdd={item => { const next = [...staticModels.filter(m => !(m.id === item.id && m.credential_id === catalog?.credential_id)), { ...item, credential_id: catalog?.credential_id ?? null }]; setStatic(next); void saveGlobal(next); }}/>{staticModels.length > 0 && <button onClick={() => { setStatic([]); void saveGlobal([]); }}>Use live catalog</button>}</section>}{notice && <p role="status">{notice}</p>}{error && <p role="alert">{errorMessage(error)}</p>}<p>Cost ranges describe illustrative initial calls; retries and remediation add cost. Unknown prices remain unavailable.</p></>;
}
function UsersPage() {
    const [users, setUsers] = useState<{
        id: string;
        username: string;
        role: string;
        disabled: boolean;
    }[]>([]);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [editing, setEditing] = useState<string | null>(null);
    const [error, setError] = useState<unknown>(null);
    const [notice, setNotice] = useState('');
    const load = useCallback(() => api.request<typeof users>('/api/auth/users').then(setUsers).catch(setError), []);
    useEffect(() => { let active = true; void Promise.resolve().then(() => { if (active)
        void load(); }); return () => { active = false; }; }, [load]);
    async function save() { try {
        await api.request(editing ? `/api/auth/users/${editing}/password` : '/api/auth/users', 'POST', editing ? { password } : { username, password });
        setNotice(editing ? 'Password reset; existing sessions revoked.' : 'Reviewer created.');
        setPassword('');
        setEditing(null);
        await load();
    }
    catch (cause) {
        setError(cause);
    } }
    return <><h2>Users</h2><form className="panel settings-form" onSubmit={event => { event.preventDefault(); void save(); }}><h3>{editing ? 'Reset password' : 'Create reviewer'}</h3>{!editing && <label>Username<input value={username} onChange={event => setUsername(event.target.value)} required pattern="[A-Za-z0-9_.-]+" maxLength={120}/></label>}<label>New password<input type="password" autoComplete="new-password" value={password} onChange={event => setPassword(event.target.value)} required minLength={12}/></label><button>{editing ? 'Reset password' : 'Create reviewer'}</button></form><ul>{users.map(user => <li key={user.id}>{user.username} · {user.role} · {user.disabled ? 'disabled' : 'active'}<div className="actions"><button onClick={() => { setEditing(user.id); setPassword(''); }}>Reset password for {user.username}</button>{user.role === 'reviewer' && <button disabled={user.disabled} onClick={() => void api.request(`/api/auth/users/${user.id}/disable`, 'POST').then(load).catch(setError)}>Disable {user.username}</button>}</div></li>)}</ul>{notice && <p role="status">{notice}</p>}{error && <p role="alert">{errorMessage(error)}</p>}</>;
}
function AccountPage() {
    const prefs = usePreferences();
    const [current, setCurrent] = useState('');
    const [password, setPassword] = useState('');
    const [confirmation, setConfirmation] = useState('');
    const [message, setMessage] = useState('');
    return <><h2>Account</h2><p>Signed in as {getSessionStatus()?.user?.username}.</p><form className="panel settings-form" onSubmit={event => { event.preventDefault(); if (password !== confirmation) {
        setMessage('Passwords must match.');
        return;
    } void api.request('/api/auth/password', 'POST', { current_password: current, password }).then(() => api.logout()).catch(error => setMessage(errorMessage(error))).finally(() => { setCurrent(''); setPassword(''); setConfirmation(''); }); }}><label>Current password<input type="password" autoComplete="current-password" value={current} onChange={event => setCurrent(event.target.value)} required/></label><label>New password<input type="password" autoComplete="new-password" value={password} onChange={event => setPassword(event.target.value)} required minLength={12}/></label><label>Confirm password<input type="password" autoComplete="new-password" value={confirmation} onChange={event => setConfirmation(event.target.value)} required minLength={12}/></label><button>Change password and log out</button></form><label className="checkbox"><input type="checkbox" checked={prefs.data.ui.auto_scroll} onChange={event => updatePreferences({ ui: { ...prefs.data.ui, auto_scroll: event.target.checked } })}/>Auto-scroll live log</label>{message && <p role="alert">{message}</p>}</>;
}
export function SettingsScreen() { const { section } = useParams(); const admin = getSessionStatus()?.user?.role === 'admin'; const permitted = section === 'account' || section === 'models' || admin; return <><h1>Settings</h1><nav className="settings-nav" aria-label="Settings">{[['provider', 'Provider'], ['models', 'Models'], ['users', 'Users'], ['account', 'Account']].filter(([id]) => admin || id === 'models' || id === 'account').map(([id, label]) => <Link aria-current={section === id ? 'page' : undefined} key={id} to={`/settings/${id}`}>{label}</Link>)}</nav>{!permitted ? <p>Ask an administrator to manage this setting.</p> : section === 'provider' ? <ProviderPage /> : section === 'models' ? <ModelsPage /> : section === 'users' ? <UsersPage /> : section === 'account' ? <AccountPage /> : <p>Select a setting above.</p>}</>; }
