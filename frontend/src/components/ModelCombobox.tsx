import {useId,useRef,useState,type KeyboardEvent} from 'react';
import {Icon} from './Icon';
export interface ModelOption {value:string;label:string;detail:string;disabled?:boolean;explanation?:string}
export function ModelCombobox({label,value,options,onChange}:{label:string;value:string;options:ModelOption[];onChange:(value:string)=>void}) {
 const id=useId();const input=useRef<HTMLInputElement>(null);const [open,setOpen]=useState(false);const [query,setQuery]=useState('');const [active,setActive]=useState(-1);
 const selected=options.find(option=>option.value===value);
 const filtered=options.filter(option=>!query||`${option.value} ${option.label}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()));
 function show(){setOpen(true);setActive(-1);}
 function choose(index:number){const option=filtered[index];if(!option||option.disabled)return;onChange(option.value);setOpen(false);setQuery('');input.current?.focus();}
 function keys(event:KeyboardEvent<HTMLInputElement>){
  if(event.key==='Escape'){event.preventDefault();setOpen(false);setQuery('');return;}
  if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();setOpen(true);const direction=event.key==='ArrowDown'?1:-1;let next=active;for(let i=0;i<filtered.length;i++){next=(next+direction+filtered.length)%filtered.length;if(!filtered[next]?.disabled){setActive(next);document.getElementById(`${id}-${next}`)?.scrollIntoView?.({block:'nearest'});break;}}}
  else if(event.key==='Enter'&&open){event.preventDefault();choose(active);}
  else if(event.key==='Tab'){setOpen(false);setQuery('');}
 }
 return <div className="model-combobox" onBlur={event=>{if(!event.currentTarget.contains(event.relatedTarget)){setOpen(false);setQuery('');}}}><label htmlFor={id}>{label}</label><div className="combobox-input"><Icon name="search"/><input ref={input} id={id} role="combobox" aria-autocomplete="list" aria-expanded={open} aria-controls={`${id}-list`} aria-activedescendant={open&&active>=0?`${id}-${active}`:undefined} aria-describedby={selected?.disabled?`${id}-error`:undefined} autoComplete="off" value={open?query:selected?.label??value} placeholder={selected?.label??'Search models…'} onFocus={show} onClick={show} onChange={event=>{setQuery(event.target.value);setActive(-1);show();}} onKeyDown={keys}/><button type="button" aria-label={`Show ${label.toLowerCase()} options`} tabIndex={-1} onClick={()=>{setOpen(!open);setQuery('');input.current?.focus();}}><Icon name={open?'chevron-up':'chevron-down'}/></button></div>
 {selected?.disabled&&<p id={`${id}-error`} className="form-error">{selected.explanation}</p>}
 {open&&<ul id={`${id}-list`} role="listbox" aria-label={`${label} options`} className="model-options">{filtered.map((option,index)=><li id={`${id}-${index}`} key={option.value} role="option" aria-selected={value===option.value} aria-disabled={option.disabled||undefined} className={active===index?'highlighted':''} onMouseDown={event=>event.preventDefault()} onClick={()=>choose(index)}><span>{option.label}</span><small>{option.detail}</small>{option.disabled&&<small>{option.explanation}</small>}</li>)}{!filtered.length&&<li role="presentation">No matching models. Search by model name or ID.</li>}</ul>}
 </div>;
}
