import { useLayoutEffect,useRef,useState,type ReactNode } from 'react';
export function WindowedRows({count,row,follow=false,label,className=''}:{count:number;row:(index:number)=>ReactNode;follow?:boolean;label:string;className?:string}){
 const ref=useRef<HTMLDivElement>(null); const [top,setTop]=useState(0); const pinned=useRef(true);const height=24;const start=Math.max(0,Math.floor(top/height)-5);const end=Math.min(count,start+45);
 useLayoutEffect(()=>{if(follow&&pinned.current&&ref.current){ref.current.scrollTop=ref.current.scrollHeight;setTop(ref.current.scrollTop);}},[count,follow]);
 return <div ref={ref} className={`windowed ${className}`} role="region" aria-label={label} tabIndex={0} onScroll={event=>{const node=event.currentTarget;pinned.current=node.scrollHeight-node.scrollTop-node.clientHeight<height;setTop(node.scrollTop);}}><div style={{paddingTop:start*height,paddingBottom:(count-end)*height}}>{Array.from({length:end-start},(_,offset)=>row(start+offset))}</div></div>;
}
