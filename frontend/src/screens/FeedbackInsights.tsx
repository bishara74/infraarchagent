import {useEffect,useState} from 'react';
import {Link} from 'react-router';
import {api,errorMessage} from '../api/client';
import type {FeedbackInsightsData,InsightGroup} from '../api/types';
import {categoryLabel} from '../lib/reviewCategories';

function decisionsLink(filters:Record<string,string>){
  return `/settings/review-history?${new URLSearchParams(filters)}`;
}

export function FeedbackInsights({query}:{query:string}){
  const [attempt,setAttempt]=useState(0);
  const [state,setState]=useState<{query:string;data?:FeedbackInsightsData;error?:unknown}>({query:''});
  useEffect(()=>{
    const controller=new AbortController();
    void api.request<FeedbackInsightsData>(`/api/reviews/history/insights?${query}`,'GET',undefined,controller.signal)
      .then(data=>{if(!controller.signal.aborted)setState({query,data});})
      .catch(error=>{if(!controller.signal.aborted)setState({query,error});});
    return()=>controller.abort();
  },[query,attempt]);
  const current=state.query===query?state:undefined;
  if(current?.error)return <div role="alert"><p>{errorMessage(current.error)}</p><button onClick={()=>{setState({query});setAttempt(value=>value+1);}}>Retry insights</button></div>;
  const data=current?.data;
  if(!data)return <p role="status">Loading feedback insights…</p>;
  function group(title:string,rows:InsightGroup[],label=(value:string)=>value.replaceAll('_',' ')){
    return <section className="panel"><h3>{title}</h3>{rows.length===0?<p>No decisions recorded.</p>:<div className="history-table"><table><caption className="sr-only">{title}</caption><thead><tr><th scope="col">Group</th><th scope="col">Decisions</th></tr></thead><tbody>{rows.map(row=><tr key={row.value}><th scope="row">{label(row.value)}</th><td><Link to={decisionsLink(row.filters)} aria-label={`View ${row.count} decisions: ${label(row.value)}`}>{row.count}</Link></td></tr>)}</tbody></table></div>}</section>;
  }
  return <div aria-label="Feedback insights">
    <h3>Feedback insights</h3><p>{data.total} recorded {data.total===1?'decision matches':'decisions match'} these filters. Use these counts to prepare lesson proposals.</p>
    <div className="insight-groups">{group('By category',data.by_category,categoryLabel)}{group('By variant',data.by_variant)}{group('By decision',data.by_decision)}</div>
    <section className="panel"><h3>Remaining blocking rules at rejection</h3><p>{data.blocking_snapshot_available} of {data.rejected_total} rejected {data.rejected_total===1?'decision has':'decisions have'} recorded blocking-rule snapshots. {data.blocking_snapshot_unavailable} unavailable.</p><p className="muted">Each rule counts once per rejected decision. Historical decisions without a snapshot are excluded from this ranking.</p>
      {data.blocking_rules.length===0?<p>No recorded blocking rules match these filters.</p>:<div className="history-table"><table><caption className="sr-only">Blocking rules in rejected decisions</caption><thead><tr><th scope="col">Rule</th><th scope="col">Rejected decisions</th></tr></thead><tbody>{data.blocking_rules.map(row=><tr key={row.rule_id}><th scope="row">{row.rule_id}</th><td><Link to={decisionsLink(row.filters)} aria-label={`View ${row.count} rejected decisions for ${row.rule_id}`}>{row.count}</Link></td></tr>)}</tbody></table></div>}
    </section>
  </div>;
}
