import {useState} from 'react';
import {errorMessage,saveAllDownload} from '../api/client';
import {Icon} from './Icon';
export function DownloadAllButton({runId,available}:{runId:string;available:boolean}) {
 const [busy,setBusy]=useState(false),[error,setError]=useState<unknown>(null);
 return <div className="download-all"><button className="primary" disabled={!available||busy} aria-describedby={!available?'download-all-help':undefined} onClick={()=>{setBusy(true);setError(null);void saveAllDownload(runId).catch(setError).finally(()=>setBusy(false));}}><Icon name="cloud-download"/>Download all three{busy?'…':''}</button>{!available&&<p id="download-all-help" className="muted">All three variants need readiness labels. Resolve each pending review first.</p>}{!!error&&<p role="alert">{errorMessage(error)}</p>}</div>;
}
