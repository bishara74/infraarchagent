import { useEffect,useRef,useState,useSyncExternalStore } from 'react';
import { BrowserRouter,Link,Route,Routes,useLocation } from 'react-router';
import { InputScreen } from './screens/InputScreen';
import { ProgressScreen } from './screens/ProgressScreen';
import { ComparisonScreen } from './screens/ComparisonScreen';
import { PackageScreen } from './screens/PackageScreen';
import { PageState } from './components/PageState';
import {Authentication} from './components/Authentication';
import {api} from './api/client';
import {getSessionStatus,setSessionStatus,subscribeSession} from './lib/sessionState';
const positions=new Map<string,number>();
function Access({children}:{children:React.ReactNode}){const status=useSyncExternalStore(subscribeSession,getSessionStatus);const [error,setError]=useState<unknown>(null);useEffect(()=>{let active=true;void api.session().then(value=>{if(active)setSessionStatus(value);}).catch(cause=>{if(active)setError(cause);});return()=>{active=false;};},[]);if(error)return <PageState error={error}/>;if(!status)return <p role="status">Checking session…</p>;if((status.setup_required||status.auth_required)&&!status.authenticated)return <Authentication setup={status.setup_required} onSaved={()=>undefined}/>;return <>{status.mode==='local'?<p className="notice" role="status">No authentication (local mode)</p>:<button onClick={()=>void api.logout().catch(setError)}>Log out</button>}{children}</>;}
function Shell(){const location=useLocation();const lastLocation=useRef(location.key);useEffect(()=>{const route=location.pathname;document.title=`${route.includes('/packages/')?'Package':route.endsWith('/compare')?'Comparison':route.startsWith('/runs/')?'Progress':'Generate'} · InfraArchAgent`;if(lastLocation.current!==location.key) document.getElementById('main-content')?.focus();lastLocation.current=location.key;window.scrollTo(0,positions.get(location.key)??0);return()=>{positions.set(location.key,window.scrollY);};},[location]);
 return <><a className="skip-link" href="#main-content">Skip to content</a><header className="app-header"><Link to="/" className="brand" translate="no"><svg aria-hidden="true" viewBox="0 0 24 24" width="24" height="24"><rect x="2" y="2" width="20" height="20" rx="4" fill="none" stroke="currentColor"/><path d="M7 2v8h10v12M7 10v12" fill="none" stroke="currentColor"/></svg><span>InfraArch<span className="brand-neutral">Agent</span></span></Link><Link to="/">New request</Link></header><main id="main-content" tabIndex={-1}><Access><Routes><Route path="/" element={<InputScreen/>}/><Route path="/runs/:runId" element={<ProgressScreen/>}/><Route path="/runs/:runId/compare" element={<ComparisonScreen/>}/><Route path="/runs/:runId/packages/:variant" element={<PackageScreen/>}/><Route path="*" element={<PageState empty="Page not found."/>}/></Routes></Access></main></>;
}
export default function App(){return <BrowserRouter><Shell/></BrowserRouter>;}
