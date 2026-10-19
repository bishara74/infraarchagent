import {useState} from 'react';
import {api,errorMessage} from '../api/client';
export function Authentication({onSaved}:{onSaved:()=>void}){
 const [key,setKey]=useState('');const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);
 return <form className="panel auth" onSubmit={event=>{event.preventDefault();if(busy)return;setBusy(true);setError(null);const submitted=key;setKey('');void api.login(submitted).then(onSaved).catch(setError).finally(()=>setBusy(false));}}><h2>API key required</h2><p>Log in to continue on this page.</p><label htmlFor="login-key">API key</label><input id="login-key" name="api-key" type="password" autoComplete="off" value={key} onChange={event=>setKey(event.target.value)} disabled={busy}/><button disabled={busy} type="submit">Continue{busy?'…':''}</button>{error?<p role="alert">{errorMessage(error)}</p>:null}</form>;
}
