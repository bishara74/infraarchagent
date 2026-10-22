import {useState} from 'react';
import type {Variant} from '../api/types';
import {errorMessage,saveDownload} from '../api/client';
import {Icon} from './Icon';
export function DownloadButton({runId,variant}:{runId:string;variant:Variant}) {
 const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);
 return <div><button disabled={busy} onClick={()=>{setBusy(true);setError(null);void saveDownload(runId,variant).catch(setError).finally(()=>setBusy(false));}}><Icon name="cloud-download"/>Download ZIP{busy?'…':''}</button>{error?<p role="alert">{errorMessage(error)}</p>:null}</div>;
}
