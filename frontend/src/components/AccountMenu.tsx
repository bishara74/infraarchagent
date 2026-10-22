import {useEffect,useRef,useState,type KeyboardEvent} from 'react';
import {Link} from 'react-router';
import {api,errorMessage} from '../api/client';
import {Icon} from './Icon';
export function AccountMenu({username}:{username:string}) {
 const [open,setOpen]=useState(false);const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);
 const root=useRef<HTMLDivElement>(null);const trigger=useRef<HTMLButtonElement>(null);const initial=useRef(0);
 const items=()=>Array.from(root.current?.querySelectorAll<HTMLElement>('[role="menuitem"]')??[]);
 function close(){setOpen(false);trigger.current?.focus();}
 useEffect(()=>{if(!open)return;items()[initial.current]?.focus();const outside=(event:PointerEvent)=>{if(!root.current?.contains(event.target as Node))setOpen(false);};document.addEventListener('pointerdown',outside);return()=>document.removeEventListener('pointerdown',outside);},[open]);
 function keys(event:KeyboardEvent){const options=items();const index=options.indexOf(document.activeElement as HTMLElement);if(event.key==='Escape'){event.preventDefault();close();}else if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?options.length-1:(index+(event.key==='ArrowDown'?1:-1)+options.length)%options.length;options[next]?.focus();}else if(event.key==='Tab')setOpen(false);}
 return <div ref={root} className="account-menu"><button ref={trigger} aria-haspopup="menu" aria-expanded={open} aria-controls="account-actions" onClick={()=>{initial.current=0;setOpen(!open);}} onKeyDown={event=>{if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();initial.current=event.key==='ArrowUp'?1:0;setOpen(true);}}}><Icon name="account"/><span className="account-name" title={username}>{username}</span><Icon name={open?'chevron-up':'chevron-down'}/></button>{open&&<div id="account-actions" className="account-actions panel" role="menu" aria-label="Account actions" onKeyDown={keys}><Link role="menuitem" to="/settings/account" onClick={()=>setOpen(false)}><Icon name="account"/>Account</Link><button role="menuitem" disabled={busy} onClick={()=>{setBusy(true);setError(null);void api.logout().catch(setError).finally(()=>setBusy(false));}}><Icon name="sign-out"/>Log out{busy?'…':''}</button></div>}{error?<p role="alert">{errorMessage(error)}</p>:null}</div>;
}
