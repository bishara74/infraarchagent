import {useId,useLayoutEffect,useRef,useState,type KeyboardEvent} from 'react';
import {Icon} from './Icon';
export interface ModelOption {value:string;label:string;detail:string;disabled?:boolean;explanation?:string;tested?:boolean}
const rowHeight=80;
export function ModelCombobox({label,value,options,onChange,error,selectedLabel}:{label:string;value:string;options:ModelOption[];onChange:(value:string)=>void;error?:string;selectedLabel?:string}) {
 const id=useId();const input=useRef<HTMLInputElement>(null);const list=useRef<HTMLUListElement>(null);
 const [open,setOpen]=useState(false);const [query,setQuery]=useState('');const [active,setActive]=useState(-1);const [top,setTop]=useState(0);
 const [placement,setPlacement]=useState({above:false,height:280});
 const selected=options.find(option=>option.value===value);
 const filtered=options.filter(option=>!query||`${option.value} ${option.label}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()));
 const start=Math.min(Math.max(0,filtered.length-16),Math.max(0,Math.floor(top/rowHeight)-3));const end=Math.min(filtered.length,start+16);
 useLayoutEffect(()=>{
  if(!open)return;
  const position=()=>{const bounds=input.current?.closest('.model-combobox')?.getBoundingClientRect();if(!bounds)return;const below=window.innerHeight-bounds.bottom-12;const above=bounds.top-12;const useAbove=below<Math.min(280,filtered.length*rowHeight)&&above>below;setPlacement({above:useAbove,height:Math.max(80,Math.min(280,useAbove?above:below))});};
  position();window.addEventListener('resize',position);window.addEventListener('scroll',position,true);
  return()=>{window.removeEventListener('resize',position);window.removeEventListener('scroll',position,true);};
 },[open,filtered.length]);
 const invalidHelp=filtered.find(option=>option.disabled)?.explanation;
 function show(){setOpen(true);setActive(-1);setTop(0);if(list.current)list.current.scrollTop=0;}
 function choose(index:number){const option=filtered[index];if(!option||option.disabled)return;onChange(option.value);input.current?.focus();setOpen(false);setQuery('');}
 function move(next:number){
  setActive(next);const node=list.current;if(!node){setTop(Math.max(0,(next-3)*rowHeight));return;}
  const height=node.clientHeight||placement.height;
  if(next*rowHeight<node.scrollTop)node.scrollTop=next*rowHeight;
  else if((next+1)*rowHeight>node.scrollTop+height)node.scrollTop=(next+1)*rowHeight-height;
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
 <label htmlFor={id}>{label}</label><div className="combobox-input"><Icon name="search"/><input ref={input} id={id} role="combobox" aria-autocomplete="list" aria-expanded={open} aria-controls={`${id}-list`} aria-activedescendant={open&&active>=0?`${id}-${active}`:undefined} aria-invalid={!!error||selected?.disabled||undefined} aria-describedby={error||selected?.disabled?`${id}-error`:undefined} autoComplete="off" title={selected?.label??selectedLabel} value={open?query:selected?.label??selectedLabel??value} placeholder={selected?.label??'Search models…'} onFocus={show} onClick={()=>{if(!open)show();}} onChange={event=>{setQuery(event.target.value);show();}} onKeyDown={keys}/><button type="button" aria-label={`Show ${label.toLowerCase()} options`} tabIndex={-1} onMouseDown={event=>event.preventDefault()} onClick={()=>{input.current?.focus();setOpen(!open);setQuery('');setTop(0);if(list.current)list.current.scrollTop=0;}}><Icon name={open?'chevron-up':'chevron-down'}/></button></div>
 {(error||selected?.disabled)&&<p id={`${id}-error`} className="form-error">{error??selected?.explanation}</p>}
 {open&&<div className={`model-popup${placement.above?' above':''}`}><ul ref={list} id={`${id}-list`} role="listbox" aria-label={`${label} options`} className="model-options" style={{maxHeight:placement.height}} onScroll={event=>setTop(event.currentTarget.scrollTop)}>
 {start>0&&<li role="presentation" aria-hidden="true" className="model-spacer" style={{height:start*rowHeight}}/>}
 {filtered.slice(start,end).map((option,offset)=>{const index=start+offset;return <li id={`${id}-${index}`} key={option.value} role="option" aria-selected={value===option.value} aria-disabled={option.disabled||undefined} aria-describedby={option.disabled?`${id}-invalid-help`:undefined} aria-setsize={filtered.length} aria-posinset={index+1} title={`${option.label}. ${option.detail}${option.disabled?`. ${option.explanation}`:''}`} className={active===index?'highlighted':''} onMouseDown={event=>event.preventDefault()} onClick={()=>choose(index)}><span>{option.label}{option.tested&&<span className="badge tested">tested</span>}</span><small>{option.detail}</small></li>;})}
 {end<filtered.length&&<li role="presentation" aria-hidden="true" className="model-spacer" style={{height:(filtered.length-end)*rowHeight}}/>}
 {!filtered.length&&<li role="presentation">No matching models. Search by model name or ID.</li>}</ul>{invalidHelp&&<p id={`${id}-invalid-help`} className="sr-only">{invalidHelp}</p>}</div>}
 </div>;
}
