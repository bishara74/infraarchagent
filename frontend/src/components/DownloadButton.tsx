import {ActionButton} from './ActionGate';
import {useState} from 'react';
import type {Variant} from '../api/types';
import {errorMessage,saveDownload} from '../api/client';
import {Icon} from './Icon';
export function DownloadButton({runId,variant,label='Download ZIP',available=true,unavailableReason='This variant does not have a downloadable readiness label.'}:{runId:string;variant:Variant;label?:string;available?:boolean;unavailableReason?:string}) {
 const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);
 return <div><ActionButton disabled={!available||busy} unavailableReason={busy?'The download is being prepared.':unavailableReason} nextStep={busy?'Wait for the download to finish.':'Inspect this variant and complete its review, or wait for processing to finish.'} onClick={()=>{setBusy(true);setError(null);void saveDownload(runId,variant).catch(setError).finally(()=>setBusy(false));}}><Icon name="cloud-download"/>{label}{busy?'…':''}</ActionButton>{error?<p role="alert">{errorMessage(error)}</p>:null}</div>;
}
