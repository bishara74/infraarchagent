import {useState} from 'react';
import {api,ApiError,errorMessage} from '../api/client';
import {PasswordField} from './PasswordField';
export function Authentication({onSaved,setup=false}:{onSaved:()=>void;setup?:boolean}) {
 const [username,setUsername]=useState('');const [password,setPassword]=useState('');const [confirmation,setConfirmation]=useState('');
 const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);const [validation,setValidation]=useState('');
 return <div className="auth-layout"><form className="panel auth" onSubmit={event=>{event.preventDefault();if(busy)return;if(setup&&password!==confirmation){setValidation('Passwords must match.');return;}setValidation('');setBusy(true);setError(null);void api.login(username,password,setup).then(onSaved).catch(setError).finally(()=>{setBusy(false);setPassword('');setConfirmation('');});}}>
 <h1>{setup?'Create admin account':'Log in'}</h1><p className="muted">Sign in to generate and review secure infrastructure packages.</p>{setup&&<p>Create the first administrator from 127.0.0.1. Use at least 12 characters for your password.</p>}
 <label>Username<input name="username" autoComplete="username" value={username} onChange={event=>setUsername(event.target.value)} required maxLength={120} spellCheck={false}/></label>
 <PasswordField label="Password" name="password" autoComplete={setup?'new-password':'current-password'} value={password} onChange={event=>setPassword(event.target.value)} required minLength={12}/>
 {setup&&<PasswordField label="Confirm password" autoComplete="new-password" value={confirmation} onChange={event=>setConfirmation(event.target.value)} required minLength={12}/>}
 {validation&&<p role="alert">{validation}</p>}{error?<p role="alert">{!setup&&error instanceof ApiError&&error.status===401?'Username or password is incorrect':errorMessage(error)}</p>:null}
 <button className="primary" disabled={busy} type="submit">{setup?'Create admin account':'Log in'}{busy?'…':''}</button>
 {!setup&&<p className="muted auth-footer">Forgot your password? Ask an administrator to reset it.</p>}
 </form></div>;
}
