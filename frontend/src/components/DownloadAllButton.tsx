import {useState} from 'react';
import {Link} from 'react-router';
import {errorMessage,saveAllDownload} from '../api/client';
import type {Variant} from '../api/types';
import {Icon} from './Icon';
import {ActionButton} from './ActionGate';
export interface DownloadBlock {variant:Variant;review:boolean;missing?:boolean}
export function DownloadAllButton({runId,available,blocked=[]}:{runId:string;available:boolean;blocked?:DownloadBlock[]}) {
 const [busy,setBusy]=useState(false),[error,setError]=useState<unknown>(null);
 const names=blocked.map(item=>item.variant[0]!.toUpperCase()+item.variant.slice(1));
 const reason=blocked.length?`Resolve ${names.join(' and ')} before downloading all three.`:'All three variants need readiness labels. Resolve each pending review first.';
 const next=blocked.length?<>{blocked.map(item=><span key={item.variant}><Link to={item.missing?'/':item.review?`/runs/${runId}/packages/${item.variant}?tab=review`:`/runs/${runId}`}>{item.missing?`Start a new request for ${item.variant}`:item.review?`Review ${item.variant}`:`View ${item.variant} progress`}</Link>. </span>)}</>:'Inspect the unavailable variants and complete their reviews.';
 return <div className="download-all"><ActionButton className="primary" disabled={!available||busy} persistentHint={!available} unavailableReason={busy?'The download is being prepared.':reason} nextStep={busy?'Wait for the download to finish.':next} onClick={()=>{setBusy(true);setError(null);void saveAllDownload(runId).catch(setError).finally(()=>setBusy(false));}}><Icon name="cloud-download"/>Download all three{busy?'…':''}</ActionButton>{!!error&&<p role="alert">{errorMessage(error)}</p>}</div>;
}
