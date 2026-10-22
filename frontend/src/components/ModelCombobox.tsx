import {useId,useRef,useState,type KeyboardEvent} from 'react';
import {Icon} from './Icon';
export interface ModelOption {value:string;label:string;detail:string;disabled?:boolean;explanation?:string}
const rowHeight=80;
export function ModelCombobox({label,value,options,onChange,error}:{label:string;value:string;options:ModelOption[];onChange:(value:string)=>void;error?:string}) {
 const id=useId();const input=useRef<HTMLInputElement>(null);const list=useRef<HTMLUListElement>(null);
 const [open,setOpen]=useState(false);const [query,setQuery]=useState('');const [active,setActive]=useState(-1);const [top,setTop]=useState(0);
 const selected=options.find(option=>option.value===value);
 const filtered=options.filter(option=>!query||`${option.value} ${option.label}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()));
 const start=Math.max(0,Math.floor(top/rowHeight)-3);const end=Math.min(filtered.length,start+16);
 const invalidHelp=filtered.find(option=>option.disabled)?.explanation;
 function show(){setOpen(true);setActive(-1);setTop(0);if(list.current)list.current.scrollTop=0;}
 function choose(index:number){const option=filtered[index];if(!option||option.disabled)return;onChange(option.value);setOpen(false);setQuery('');input.current?.focus();}
 function move(next:number){
  setActive(next);const node=list.current;if(!node){setTop(Math.max(0,(next-3)*rowHeight));return;}
  if(next*rowHeight<node.scrollTop)node.scrollTop=next*rowHeight;
  else if((next+1)*rowHeight>node.scrollTop+node.clientHeight)node.scrollTop=(next+1)*rowHeight-node.clientHeight;
  setTop(node.scrollTop);
 }
 function keys(event:KeyboardEvent<HTMLInputElement>){
  if(event.key==='Escape'){event.preventDefault();setOpen(false);setQuery('');return;}
  if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){
   event.preventDefault();setOpen(true);const direction=event.key==='ArrowUp'||event.key==='End'?-1:1;
   let next=event.key==='Home'?-1:event.key==='End'?filtered.length:!open?(direction===1?-1:0):direction===-1&&active<0?0:active;
   for(let i=0;i<filtered.length;i++){next=(next+direction+filtered.length)%filtered.length;if(!filtered[next]?.disabled){move(next);break;}}
  }else if(event.key==='Enter'&&open){event.preventDefault();choose(active);}
  else if(event.key==='Tab'){setOpen(false);setQuery('');}
 }
 return <div className="model-combobox" onBlur={event=>{if(!event.currentTarget.contains(event.relatedTarget)){setOpen(false);setQuery('');}}}>
 <label htmlFor={id}>{label}</label><div className="combobox-input"><Icon name="search"/><input ref={input} id={id} role="combobox" aria-autocomplete="list" aria-expanded={open} aria-controls={`${id}-list`} aria-activedescendant={open&&active>=0?`${id}-${active}`:undefined} aria-invalid={!!error||selected?.disabled||undefined} aria-describedby={error||selected?.disabled?`${id}-error`:undefined} autoComplete="off" title={selected?.label} value={open?query:selected?.label??value} placeholder={selected?.label??'Search models…'} onFocus={show} onClick={show} onChange={event=>{setQuery(event.target.value);show();}} onKeyDown={keys}/><button type="button" aria-label={`Show ${label.toLowerCase()} options`} tabIndex={-1} onClick={()=>{setOpen(!open);setQuery('');setTop(0);input.current?.focus();}}><Icon name={open?'chevron-up':'chevron-down'}/></button></div>
 {(error||selected?.disabled)&&<p id={`${id}-error`} className="form-error">{error??selected?.explanation}</p>}
 {open&&<div className="model-popup"><ul ref={list} id={`${id}-list`} role="listbox" aria-label={`${label} options`} className="model-options" style={{paddingTop:start*rowHeight,paddingBottom:(filtered.length-end)*rowHeight}} onScroll={event=>setTop(event.currentTarget.scrollTop)}>
 {filtered.slice(start,end).map((option,offset)=>{const index=start+offset;return <li id={`${id}-${index}`} key={option.value} role="option" aria-selected={value===option.value} aria-disabled={option.disabled||undefined} aria-describedby={option.disabled?`${id}-invalid-help`:undefined} aria-setsize={filtered.length} aria-posinset={index+1} title={`${option.label}. ${option.detail}${option.disabled?`. ${option.explanation}`:''}`} className={active===index?'highlighted':''} onMouseDown={event=>event.preventDefault()} onClick={()=>choose(index)}><span>{option.label}</span><small>{option.detail}</small></li>;})}
 {!filtered.length&&<li role="presentation">No matching models. Search by model name or ID.</li>}</ul>{invalidHelp&&<p id={`${id}-invalid-help`} className="combobox-help">{invalidHelp}</p>}</div>}
 </div>;
}
