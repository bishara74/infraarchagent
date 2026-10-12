import { useState } from 'react';
import { setApiKey } from '../lib/sessionState';
export function Authentication({onSaved}:{onSaved:()=>void}){
 const [key,setKey]=useState('');return <form className="panel auth" onSubmit={event=>{event.preventDefault();setApiKey(key.trim()||null);onSaved();}}><h2>API key required</h2><p>Enter your key to continue on this page.</p><label htmlFor="reentry-key">API key</label><input id="reentry-key" name="api-key" type="password" autoComplete="current-password" value={key} onChange={event=>setKey(event.target.value)}/><button type="submit">Continue</button></form>;
}
