import { Icon } from '../components/Icon';
import { Link,useParams,useSearchParams } from 'react-router';
import { useRunResults } from '../hooks/useRunResults';
import { FileTree } from '../components/FileTree';
import { DiffView } from '../components/DiffView';
import { ReportPanel } from '../components/ReportPanel';
import { ReviewPanel } from '../components/ReviewPanel';
import { PageState } from '../components/PageState';
import { RunNotice } from '../components/RunNotice';
import { readinessOrigin } from '../lib/readinessOrigin';
export function PackageScreen(){const {runId='',variant=''}=useParams();const [query,setQuery]=useSearchParams();const stream=useRunResults(runId);
 if(stream.error)return <PageState error={stream.error} onRetry={stream.reconnect}/>;if(!stream.results)return <PageState loading/>;const item=stream.results.packages.find(value=>value.variant===variant);
 if(!item)return <><Link to={`/runs/${runId}/compare`} className="back-link"><Icon name="arrow-left"/>Back to comparison</Link><PageState empty="This variant is unavailable."/></>;
 const requested=query.get('file');const paths=Object.keys(item.files).sort();const path=requested&&Object.hasOwn(item.files,requested)?requested:paths[0];
 return <><div className="page-heading"><div><Link to={`/runs/${runId}/compare?variant=${item.variant}`} className="back-link"><Icon name="arrow-left"/>Back to comparison</Link><h1 className="capitalize">{item.variant} package</h1></div></div><RunNotice state={stream.state} onReconnect={stream.reconnect}/>{requested&&!Object.hasOwn(item.files,requested)&&<p className="notice">The requested file is unavailable. Showing the first existing file.</p>}<ReviewPanel onDecision={stream.reconnect} origin={readinessOrigin(stream.events,item)} retryPending={stream.pendingRetries.includes(item.variant)} item={item} runId={runId} onRetry={()=>stream.reopenRetry(item.variant)} onRefresh={stream.refresh}/><div className="package-layout"><aside className="panel files"><h2>Files</h2><FileTree item={item} runId={runId} selected={path}/></aside>{path?<DiffView item={item} path={path}/>:<PageState empty="No files available."/>}<ReportPanel item={item} onFile={file=>setQuery({file})}/></div></>;
}
