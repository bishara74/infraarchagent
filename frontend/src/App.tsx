import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { BrowserRouter, Link, NavLink, Route, Routes, useLocation } from 'react-router';
import { AccountMenu } from './components/AccountMenu';
import { errorMessage } from './api/client';
import { retryHydration } from './lib/preferences';
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
function Access({children,local,onLocal}:{children:React.ReactNode;local:boolean;onLocal:()=>void}) {
 const status=useSyncExternalStore(subscribeSession,getSessionStatus);const preferences=usePreferences();
 const [error,setError]=useState<unknown>(null);const [retry,setRetry]=useState(0);
 useEffect(()=>{const controller=new AbortController();void api.session().then(value=>{if(!controller.signal.aborted)setSessionStatus(value);}).catch(cause=>{if(!controller.signal.aborted)setError(cause);});return()=>controller.abort();},[retry]);
 const userId=status?.user?.id;
 useEffect(()=>{void hydratePreferences(userId??null);},[userId]);
 if(error)return <div className="panel" role="alert"><p>{errorMessage(error)}</p><button onClick={()=>{setError(null);setRetry(value=>value+1);}}>Retry</button></div>;
 if(!status)return <p role="status">Checking session…</p>;
 if(((status.setup_required&&!local)||status.auth_required)&&!status.authenticated)return <><Authentication setup={status.setup_required} onSaved={()=>undefined}/>{!status.auth_required&&<button onClick={onLocal}>Continue in local mode</button>}</>;
 if(status.user&&(!preferences.ready||getPreferenceOwner()!==status.user.id))return <p role="status">Loading saved preferences…</p>;
 return <>{status.mode==='local'&&<p className="notice" role="status">No authentication (local mode)</p>}{preferences.loadError&&location.pathname!=='/recent'?<div className="notice" role="alert"><p>Saved preferences could not be loaded. Showing this account’s cached settings.</p><button onClick={()=>void retryHydration()}>Retry</button></div>:null}{children}</>;
}
function Shell() {
    const location = useLocation();
    const status=useSyncExternalStore(subscribeSession,getSessionStatus);
    const [local,setLocal]=useState(false);
    const allowed=status?.authenticated||(status?.mode==='local'&&(!status.setup_required||local));
    const lastLocation = useRef(location.key);
    useEffect(() => { const route = location.pathname; document.title = `${route.startsWith('/settings/') ? 'Settings' : route === '/recent' ? 'Recent runs' : route.includes('/packages/') ? 'Package' : route.endsWith('/compare') ? 'Comparison' : route.startsWith('/runs/') ? 'Progress' : 'Generate'} · InfraArchAgent`; if (lastLocation.current !== location.key)
        document.getElementById('main-content')?.focus(); lastLocation.current = location.key; window.scrollTo(0, positions.get(location.key) ?? 0); return () => { positions.set(location.key, window.scrollY); }; }, [location]);
    return <><a className="skip-link" href="#main-content">Skip to content</a><header className="app-header"><Link to="/" className="brand" translate="no"><Icon name="circuit-board"/><span>InfraArch<span className="brand-neutral">Agent</span></span></Link>{allowed&&<><nav aria-label="Main"><NavLink to="/" end><Icon name="zap"/>New request</NavLink><NavLink to="/recent"><Icon name="history"/>Recent runs</NavLink><Link aria-current={location.pathname.startsWith('/settings/')?'page':undefined} to="/settings/models"><Icon name="gear"/>Settings</Link></nav>{status?.authenticated&&<AccountMenu username={status.user?.username??'Account'}/>}</>}</header><main id="main-content" tabIndex={-1}><Access local={local} onLocal={()=>setLocal(true)}><Routes><Route path="/" element={<InputScreen />}/><Route path="/recent" element={<RecentRunsScreen />}/><Route path="/settings/:section" element={<SettingsScreen />}/><Route path="/runs/:runId" element={<ProgressScreen />}/><Route path="/runs/:runId/compare" element={<ComparisonScreen />}/><Route path="/runs/:runId/packages/:variant" element={<PackageScreen />}/><Route path="*" element={<PageState empty="Page not found."/>}/></Routes></Access></main></>;
}
export default function App() { return <BrowserRouter><Shell /></BrowserRouter>; }
