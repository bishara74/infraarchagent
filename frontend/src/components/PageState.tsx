import { Link } from 'react-router';
import { ApiError,errorMessage } from '../api/client';
import { Authentication } from './Authentication';
export function PageState({error,loading,empty,onRetry}:{error?:unknown;loading?:boolean;empty?:string;onRetry?:()=>void}){
 if(error instanceof ApiError && error.status===401) return <Authentication onSaved={()=>onRetry?.()}/>;
 if(error) return <div className="panel" role="alert"><h2>Unable to load this run</h2><p>{errorMessage(error)}</p>{onRetry&&<button onClick={onRetry}>Try again</button>} <Link to="/">New request</Link></div>;
 if(loading) return <div className="panel" role="status">Loading run…</div>;
 return <div className="panel"><p>{empty||'No results are available yet.'}</p><Link to="/">New request</Link></div>;
}
