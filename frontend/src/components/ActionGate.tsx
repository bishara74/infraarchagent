import {Icon} from './Icon';
import {Children,isValidElement,useId,useLayoutEffect,useRef,useState,type ButtonHTMLAttributes,type ReactNode,type Ref} from 'react';

interface GateProps {
 disabled?:boolean;
 reason:string;
 nextStep?:ReactNode;
 persistent?:boolean;
 children:ReactNode;
 describedBy?:string;
 hintId?:string;
 label?:string;
}

/** Keep native disabled semantics while making the explanation operable. */
export function ActionGate({disabled,reason,nextStep,children,persistent=false,describedBy,hintId,label}:GateProps){
 const generated=useId();const id=hintId??generated;const [open,setOpen]=useState(false);const [dismissed,setDismissed]=useState(false);
 const root=useRef<HTMLSpanElement>(null);const hint=useRef<HTMLSpanElement>(null);
 const [position,setPosition]=useState({left:8,top:8});
 useLayoutEffect(()=>{
  if(!disabled||persistent)return;
  const place=()=>{const bounds=root.current?.getBoundingClientRect();if(!bounds)return;const height=hint.current?.getBoundingClientRect().height||140;const top=bounds.bottom+height+8>window.innerHeight?Math.max(8,bounds.top-height-4):bounds.bottom+4;const left=Math.max(8,Math.min(bounds.left,window.innerWidth-328));setPosition(previous=>previous.left===left&&previous.top===top?previous:{left,top});};
  place();if(!open)return;window.addEventListener('resize',place);window.addEventListener('scroll',place,true);return()=>{window.removeEventListener('resize',place);window.removeEventListener('scroll',place,true);};
 },[disabled,open,persistent]);
 return <span ref={root} data-dismissed={dismissed?'true':undefined} className={disabled?'action-gate':'action-gate-enabled'} role={disabled?'group':undefined} tabIndex={disabled?0:undefined} aria-label={disabled?`${label??'Action'} unavailable`:undefined} aria-describedby={disabled?[describedBy,id].filter(Boolean).join(' '):undefined}
  onMouseEnter={()=>{if(disabled){setDismissed(false);setOpen(true);}}} onMouseLeave={event=>{if(!event.currentTarget.contains(document.activeElement))setOpen(false);}}
  onFocus={()=>{if(disabled){setDismissed(false);setOpen(true);}}} onBlur={event=>{if(!event.currentTarget.contains(event.relatedTarget))setOpen(false);}}
  onClick={()=>{if(disabled){setDismissed(false);setOpen(true);}}} onKeyDown={event=>{if(!disabled)return;if(event.key==='Escape'){event.preventDefault();event.stopPropagation();setDismissed(true);setOpen(false);return;}if(event.target!==event.currentTarget)return;if(event.key==='Enter'||event.key===' '){event.preventDefault();setDismissed(false);setOpen(true);}}}>
  {children}
  {disabled&&<span ref={hint} style={persistent?undefined:position} id={id} className={`action-gate-help${persistent?' persistent':''}`} data-open={persistent||open?'true':undefined}><Icon name="info"/><span className="action-gate-copy">{reason}{nextStep&&<span className="action-gate-next">{nextStep}</span>}</span></span>}
  {disabled&&open&&<span className="sr-only" role="status">{reason}</span>}
 </span>;
}

type ActionButtonProps=ButtonHTMLAttributes<HTMLButtonElement>&{
 ref?:Ref<HTMLButtonElement>;
 unavailableReason?:string;
 nextStep?:ReactNode;
 persistentHint?:boolean;
};
export function ActionButton({unavailableReason='A request is in progress.',nextStep='Wait for it to finish, then try again.',persistentHint,ref,...props}:ActionButtonProps){
 const id=useId();
 return <ActionGate disabled={props.disabled} reason={unavailableReason} nextStep={nextStep} persistent={persistentHint} describedBy={props['aria-describedby']} hintId={id} label={props['aria-label']??actionName(props.children)}>
  <button ref={ref} {...props} aria-describedby={props.disabled?[props['aria-describedby'],id].filter(Boolean).join(' '):props['aria-describedby']}/>
 </ActionGate>;
}

function actionName(children:ReactNode):string {
 return Children.toArray(children).map(child=>typeof child==='string'||typeof child==='number'?String(child):isValidElement<{children?:ReactNode}>(child)?actionName(child.props.children):'').join('');
}
