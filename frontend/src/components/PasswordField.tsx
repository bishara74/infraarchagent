import {useId,useState,type InputHTMLAttributes} from 'react';
import {registerBrowserSecret} from '../lib/preferences';
import {Icon} from './Icon';
export function PasswordField({label,...props}:InputHTMLAttributes<HTMLInputElement>&{label:string}) {
 const generated=useId();const id=props.id??generated;
 const [visible,setVisible]=useState(false);const [caps,setCaps]=useState(false);
 return <div><label htmlFor={id}>{label}</label><div className="password-field"><input {...props} id={id} type={visible?'text':'password'} aria-describedby={caps?`${id}-caps`:props['aria-describedby']} onChange={event=>{registerBrowserSecret(event.target.value);props.onChange?.(event);}} onKeyDown={event=>{setCaps(event.getModifierState('CapsLock'));props.onKeyDown?.(event);}} onKeyUp={event=>{setCaps(event.getModifierState('CapsLock'));props.onKeyUp?.(event);}} onBlur={event=>{setCaps(false);props.onBlur?.(event);}}/><button type="button" aria-label={`${visible?'Hide':'Show'} ${label.toLowerCase()}`} aria-pressed={visible} onClick={()=>setVisible(!visible)}><Icon name={visible?'eye-closed':'eye'}/></button></div>{caps&&<p id={`${id}-caps`} className="warn-text" role="status">Caps Lock is on.</p>}</div>;
}
