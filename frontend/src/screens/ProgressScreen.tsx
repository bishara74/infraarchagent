import { Link,useParams } from 'react-router';
import { useRunStream } from '../hooks/useRunStream';
import { stageFor,blankStage } from '../lib/runReducer';
import { StageCard } from '../components/StageCard';
import { StatusBadge } from '../components/StatusBadge';
import { LiveLog } from '../components/LiveLog';
import { PageState } from '../components/PageState';
import { RunNotice } from '../components/RunNotice';
import { variants } from '../api/types';
export function ProgressScreen(){const {runId=''}=useParams();const stream=useRunStream(runId);const terminal=['success','partial_success','failed'].includes(stream.model.runStatus);
 if(stream.error)return <PageState error={stream.error} onRetry={stream.reconnect}/>;
 if(!stream.results&&!stream.events.length)return <PageState loading onRetry={stream.reconnect}/>;
 return <><p className="muted run-meta" title={stream.results?.run.input_text}>Run <code>{runId}</code> · {stream.results?.run.input_text}</p><div className="page-heading"><h1>Pipeline progress</h1><StatusBadge status={stream.model.runStatus}/>{terminal&&<Link className="button primary" to={`/runs/${runId}/compare`}>View results</Link>}</div><RunNotice state={stream.state} onReconnect={stream.reconnect}/>{stream.results?.run.error_message&&<p role="alert">{stream.results.run.error_message}</p>}<div className="stages"><StageCard name="ArchitectAgent" id="architect" stage={stageFor(stream.model,'architect')}/><StageCard name="GeneratorAgents" id="generators" stage={stageFor(stream.model,'generators')}>{variants.map(variant=>{const stage=stream.model.stages[`generator_${variant}:${variant}`]??blankStage();return <div className="generator-row" key={variant}><span className="capitalize">{variant} variant</span><StatusBadge status={stage.status} seq={stage.seq} testId={`stage-generator-${variant}`}/></div>;})}</StageCard><StageCard name="SecurityAgent" id="security" stage={stageFor(stream.model,'security')}/><StageCard name="ValidatorAgent" id="validator" stage={stageFor(stream.model,'validator')}/></div><LiveLog events={stream.events} live={!terminal&&stream.state!=='closed'}/></>;
}
