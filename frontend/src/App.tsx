import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router';
import { Icon } from './components/Icon';
import { SettingsScreen } from './screens/SettingsScreen';
import { RecentRunsScreen } from './screens/RecentRunsScreen';
import { InputScreen } from './screens/InputScreen';
import { ProgressScreen } from './screens/ProgressScreen';
import { ComparisonScreen } from './screens/ComparisonScreen';
import { PackageScreen } from './screens/PackageScreen';
import { PageState } from './components/PageState';
import { Authentication } from './components/Authentication';
import { api } from './api/client';
import { hydratePreferences, usePreferences, getPreferenceOwner } from './lib/preferences';
import { getSessionStatus, setSessionStatus, subscribeSession } from './lib/sessionState';
const positions = new Map<string, number>();
function Access({ children }: {
    children: React.ReactNode;
}) { const status = useSyncExternalStore(subscribeSession, getSessionStatus); const preferences = usePreferences(); const [error, setError] = useState<unknown>(null); const [local, setLocal] = useState(false); useEffect(() => { let active = true; void api.session().then(value => { if (active)
    setSessionStatus(value); }).catch(cause => { if (active)
    setError(cause); }); return () => { active = false; }; }, []); const userId = status?.user?.id; useEffect(() => { void hydratePreferences(userId ?? null); }, [userId]); if (error)
    return <PageState error={error}/>; if (!status)
    return <p role="status">Checking session…</p>; if (((status.setup_required && !local) || status.auth_required) && !status.authenticated)
    return <><Authentication setup={status.setup_required} onSaved={() => undefined}/>{!status.auth_required && <button onClick={() => setLocal(true)}>Continue in local mode</button>}</>; if (status.user && (!preferences.ready || getPreferenceOwner() !== status.user.id))
    return <p role="status">Loading saved preferences…</p>; return <>{status.mode === 'local' ? <p className="notice" role="status">No authentication (local mode)</p> : <button onClick={() => void api.logout().catch(setError)}>Log out</button>}{children}</>; }
function Shell() {
    const location = useLocation();
    const lastLocation = useRef(location.key);
    useEffect(() => { const route = location.pathname; document.title = `${route.startsWith('/settings/') ? 'Settings' : route === '/recent' ? 'Recent runs' : route.includes('/packages/') ? 'Package' : route.endsWith('/compare') ? 'Comparison' : route.startsWith('/runs/') ? 'Progress' : 'Generate'} · InfraArchAgent`; if (lastLocation.current !== location.key)
        document.getElementById('main-content')?.focus(); lastLocation.current = location.key; window.scrollTo(0, positions.get(location.key) ?? 0); return () => { positions.set(location.key, window.scrollY); }; }, [location]);
    return <><a className="skip-link" href="#main-content">Skip to content</a><header className="app-header"><Link to="/" className="brand" translate="no"><Icon name="circuit-board"/><span>InfraArch<span className="brand-neutral">Agent</span></span></Link><nav aria-label="Main"><Link to="/">New request</Link><Link to="/recent">Recent runs</Link><Link to="/settings/models">Settings</Link></nav></header><main id="main-content" tabIndex={-1}><Access><Routes><Route path="/" element={<InputScreen />}/><Route path="/recent" element={<RecentRunsScreen />}/><Route path="/settings/:section" element={<SettingsScreen />}/><Route path="/runs/:runId" element={<ProgressScreen />}/><Route path="/runs/:runId/compare" element={<ComparisonScreen />}/><Route path="/runs/:runId/packages/:variant" element={<PackageScreen />}/><Route path="*" element={<PageState empty="Page not found."/>}/></Routes></Access></main></>;
}
export default function App() { return <BrowserRouter><Shell /></BrowserRouter>; }
