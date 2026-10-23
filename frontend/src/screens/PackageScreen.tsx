import {useRef} from 'react';
import {Icon} from '../components/Icon';
import {Link,useParams,useSearchParams} from 'react-router';
import {useRunResults} from '../hooks/useRunResults';
import {FileTree} from '../components/FileTree';
import {FileContent} from '../components/FileContent';
import {DiffView} from '../components/DiffView';
import {ReportPanel} from '../components/ReportPanel';
import {ReviewPanel} from '../components/ReviewPanel';
import {PageState} from '../components/PageState';
import {RunNotice} from '../components/RunNotice';
import {StatusBadge} from '../components/StatusBadge';
import {readinessOrigin} from '../lib/readinessOrigin';
const tabs=[['files','Files'],['fixes','Security fixes'],['findings','Findings'],['review','Review']] as const;
export function PackageScreen(){
 const {runId='',variant=''}=useParams();const [query,setQuery]=useSearchParams();const stream=useRunResults(runId);const navigation=useRef<HTMLDivElement>(null);
 if(stream.error)return <PageState error={stream.error} onRetry={stream.reconnect}/>;if(!stream.results)return <PageState loading/>;const item=stream.results.packages.find(value=>value.variant===variant);
 if(!item)return <><Link to={`/runs/${runId}/compare`} className="back-link"><Icon name="arrow-left"/>Back to comparison</Link><PageState empty="This variant is unavailable."/></>;
 const requested=query.get('file');const paths=Object.keys(item.files).sort();const path=requested&&Object.hasOwn(item.files,requested)?requested:paths[0];const tab=tabs.find(([id])=>id===query.get('tab'))?.[0]??'files';
 function choose(id:string,focus=false){setQuery(previous=>{const next=new URLSearchParams(previous);next.set('tab',id);return next;});if(focus)navigation.current?.querySelector<HTMLButtonElement>(`[data-tab="${id}"]`)?.focus();}
 function openFile(file:string){setQuery({file,tab:'files'});}
 return <><div className="page-heading"><div><Link to={`/runs/${runId}/compare?variant=${item.variant}`} className="back-link"><Icon name="arrow-left"/>Back to comparison</Link><h1 className="capitalize">{item.variant} package</h1></div>{tab!=='review'&&<StatusBadge status={item.readiness_label??item.status}/>}</div><p className="muted">You are inspecting the {item.variant} variant. Review and approval apply only to this selected variant.</p><RunNotice state={stream.state} onReconnect={stream.reconnect}/>{requested&&!Object.hasOwn(item.files,requested)&&<p className="notice">The requested file is unavailable. Showing the first existing file.</p>}
 <div className="tabs package-tabs" ref={navigation} role="tablist" aria-label="Selected variant details" onKeyDown={event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const index=tabs.findIndex(([id])=>id===tab);const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowLeft'?-1:1)+tabs.length)%tabs.length;choose(tabs[next]![0],true);}}>{tabs.map(([id,label])=><button key={id} id={`package-tab-${id}`} role="tab" data-tab={id} aria-selected={tab===id} aria-controls={`package-panel-${id}`} tabIndex={tab===id?0:-1} onClick={()=>choose(id)}>{label}</button>)}</div>
 <div role="tabpanel" id={`package-panel-${tab}`} aria-labelledby={`package-tab-${tab}`} tabIndex={0}>
 {tab==='review'?<ReviewPanel key={item.variant} onDecision={stream.reconnect} origin={readinessOrigin(stream.events,item)} retryPending={stream.pendingRetries.includes(item.variant)} item={item} runId={runId} onRetry={()=>stream.reopenRetry(item.variant)} onRefresh={stream.refresh}/>:tab==='findings'?<div className="findings-layout"><ReportPanel item={item} section="security" onFile={openFile}/><ReportPanel item={item} section="validation" onFile={openFile}/></div>:<div className={`package-layout ${tab==='files'?'files-layout':''}`}><aside className="panel files"><h2>Package files</h2><FileTree item={item} runId={runId} selected={path} tab={tab}/></aside>{path?(tab==='files'?<FileContent path={path} content={item.files[path]??''}/>:<DiffView item={item} path={path}/>):<PageState empty="No files available."/>}{tab==='fixes'&&<ReportPanel item={item} section="security" onFile={file=>setQuery({file,tab:'fixes'})}/>}</div>}
 </div></>;
}
