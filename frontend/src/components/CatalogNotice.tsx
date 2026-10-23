import {Link} from 'react-router';
import type {Catalog} from '../api/types';
import {errorMessage} from '../api/client';

export function CatalogNotice({catalog,error,retry}:{catalog:Catalog|null;error:unknown;retry:()=>void}) {
 if(!catalog&&!error)return <p role="status">Loading model catalogue…</p>;
 const guidance=error?`Unable to load model catalogue. ${errorMessage(error)}`:
 catalog?.status==='setup_required'?'No provider selected or environment key configured. Set up a provider to load models.':
 catalog?.status==='invalid'?'The selected provider credential is invalid. Update it in Provider settings.':
 catalog?.status==='no_credit'?'The selected provider has no credit. Add credit or raise its spending limit, then retry.':
 catalog?.status==='unavailable'?(catalog.error_code==='network_error'?'Network error loading the provider catalogue. Check the connection and retry.':'The provider catalogue is unavailable. Check the endpoint and retry.'):
 !catalog?.models.length?'The provider returned no models. Check provider access or configure a custom catalogue.':null;
 if(!guidance)return null;
 return <div className="notice" role="status"><p>{guidance}</p><div className="actions"><button type="button" onClick={retry}>Retry</button><Link to="/settings/provider">Provider settings</Link></div></div>;
}
