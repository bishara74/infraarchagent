import {reviewCategories,categoryLabel} from '../lib/reviewCategories';
import { getSessionStatus } from '../lib/sessionState';
import { useRef, useState } from 'react';
import { api, ApiError, errorMessage, saveDownload } from '../api/client';
import type { PackageResult, ReviewRequest, ReviewCategory } from '../api/types';
import { reviewReason } from '../lib/reviewReasons';
import { Authentication } from './Authentication';
import { Icon } from './Icon';
import { StatusBadge } from './StatusBadge';
export function ReviewPanel({ item, runId, onRetry, onRefresh, onDecision, retryPending = false, origin = null }: {
    onDecision?: () => void;
    origin?: string | null;
    retryPending?: boolean;
    item: PackageResult;
    runId: string;
    onRetry: () => void;
    onRefresh: () => Promise<unknown>;
}) {
    const account = getSessionStatus()?.user;
    const categoryField = useRef<HTMLSelectElement>(null);
    const [category,setCategory]=useState<ReviewCategory|''>('');
    const actions=item.review_actions??(item.review_available?['approve','retry','reject']:[]);
    const reviewerField = useRef<HTMLInputElement>(null);
    const reasonField = useRef<HTMLTextAreaElement>(null);
    const [decisionError, setDecisionError] = useState<string | null>(null);
    const [reviewer, setReviewer] = useState('');
    const [reason, setReason] = useState('');
    const [busy, setBusy] = useState(false);
    const [editing, setEditing] = useState(false);
    const [feedback, setFeedback] = useState('');
    const [targets, setTargets] = useState<string[]>([]);
    const [error, setError] = useState<unknown>(null);
    const dialog = useRef<HTMLDialogElement>(null);
    const reject = useRef<HTMLButtonElement>(null);
    const invalidField=useRef<HTMLElement|null>(null);
    async function action(request: ReviewRequest) { if (busy)
        return; setBusy(true); setError(null); try {
        await api.review(runId, item.variant, request);
        if (request.action === 'retry') {
            onRetry();
            setEditing(false);
        }
        else {
            onDecision?.();
        }
        await onRefresh();
    }
    catch (cause) {
        setError(cause);
    }
    finally {
        setBusy(false);
    } }
    function invalid(message:string,field:HTMLElement|null){
        setDecisionError(message);invalidField.current=field;field?.focus();
    }
    function decide(kind:'approve'|'reject'){
        const name=account?.username??reviewer.trim();const explanation=reason.trim();
        if(!name){invalid('Enter a reviewer name and decision reason.',reviewerField.current);return;}
        if(!category){invalid('Choose a reason category.',categoryField.current);return;}
        if(!explanation){invalid('Enter a reviewer name and decision reason.',reasonField.current);return;}
        setDecisionError(null);void action({action:kind,reviewer_name:name,reason:explanation,category});
    }
    return <section className="panel review" aria-label="Package readiness and review">{(retryPending || item.retry_in_progress) ? <p role="status">Retry in progress…</p> : actions.length>0 ? <>{item.review_available?<h2>Pending review</h2>:<p>No review needed — this package passed all automatic checks.</p>}{item.review_reasons.map(reason => <p key={reason}>{reviewReason(reason)}</p>)}{account ? <p>Reviewer: {account.username} · authenticated account</p> : <><label>Reviewer name<input ref={reviewerField} aria-describedby="decision-help" autoComplete="name" name="reviewer_name" value={reviewer} onChange={event => setReviewer(event.target.value)} maxLength={120}/></label><p className="muted">Self-declared identity; authentication does not verify your name.</p></>}<label>Reason category<select name="review_category" aria-describedby="decision-help" aria-invalid={decisionError==='Choose a reason category.'||undefined} aria-label="Reason category" ref={categoryField} value={category} onChange={event=>setCategory(event.target.value as ReviewCategory|'')} required><option value="">Choose a category…</option>{Object.entries(reviewCategories).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><label>Decision reason<textarea ref={reasonField} aria-describedby="decision-help" name="decision_reason" value={reason} onChange={event => setReason(event.target.value)} maxLength={2000}/></label><p id="decision-help" className="muted">A category and decision reason are required; account identity is recorded automatically.</p>{decisionError && <p role="alert">{decisionError}</p>}<div className="actions">{item.downloadable&&item.readiness_label&&<StatusBadge status={item.readiness_label}/>} {actions.includes('approve')&&<button disabled={busy} onClick={() => decide('approve')}>Approve</button>}{actions.includes('retry')&&<button disabled={busy} onClick={() => setEditing(value => !value)}>Retry with feedback</button>}<button ref={reject} disabled={busy} className="destructive" onClick={() => {invalidField.current=null;dialog.current?.showModal();}}>Reject</button>{item.downloadable&&<button className="primary" disabled={busy} onClick={()=>{setBusy(true);setError(null);void saveDownload(runId,item.variant).catch(setError).finally(()=>setBusy(false));}}><Icon name="cloud-download"/>Download ZIP{busy?'…':''}</button>}</div>{editing && <form onSubmit={event => { event.preventDefault(); void action({ action: 'retry', ...(feedback.trim() ? { feedback: feedback.trim() } : {}), ...(targets.length ? { target_files: targets } : {}) }); }}><label htmlFor="review-feedback">Feedback</label><textarea id="review-feedback" name="feedback" rows={3} value={feedback} disabled={busy} onChange={event => setFeedback(event.target.value)} autoFocus/><p className="muted">{Array.from(feedback.trim()).length} / 2000 characters</p>{item.retry_targets.length === 0 && <fieldset disabled={busy}><legend>Target files (up to 5)</legend>{Object.keys(item.files).sort().map(path => <label className="checkbox" key={path}><input type="checkbox" name="target_files" checked={targets.includes(path)} disabled={!targets.includes(path) && targets.length >= 5} onChange={event => setTargets(previous => event.target.checked ? [...previous, path] : previous.filter(value => value !== path))}/>{path}</label>)}</fieldset>}<button disabled={busy} type="submit">Submit retry{busy ? '…' : ''}</button></form>}</> : item.downloadable ? <div className="actions">{item.readiness_label && <StatusBadge status={item.readiness_label}/>}<button className="primary" disabled={busy} onClick={() => { setBusy(true); setError(null); void saveDownload(runId, item.variant).catch(cause => setError(cause)).finally(() => setBusy(false)); }}><Icon name="cloud-download"/>Download ZIP{busy ? '…' : ''}</button></div> : <p className="muted">Download becomes available when this package has a readiness label.</p>}
 {item.downloadable && item.readiness_label && !(retryPending || item.retry_in_progress) && <p className="muted">Label origin: {origin ?? 'unavailable (transition event not recorded)'}</p>}
 {item.review_decision && <div className="notice"><p>Reviewer: {item.review_decision.reviewer_name ?? 'unavailable'} — {item.review_decision.identity_basis}</p><p>Decision time: {item.review_decision.decided_at ?? 'unavailable'}</p><p>Category: {categoryLabel(item.review_decision.category)}</p><p>Reason: {item.review_decision.reason ?? 'unavailable'}</p></div>}
 {busy && <span role="status" className="spinner">Request in progress…</span>}{error instanceof ApiError && error.status === 401 ? <Authentication onSaved={() => { setError(null); void onRefresh().catch(cause => setError(cause)); }}/> : error ? <p role="alert">{errorMessage(error)}</p> : null}
 <dialog ref={dialog} aria-labelledby="reject-title" onClose={() => {(invalidField.current??reject.current)?.focus();invalidField.current=null;}}><h2 id="reject-title">Reject this package?</h2><p>The package will be labelled rejected. Its ZIP will remain available.</p><div className="actions"><button autoFocus onClick={() => dialog.current?.close()}>Cancel</button><button className="destructive" disabled={busy} onClick={() => { dialog.current?.close(); decide('reject'); }}>Confirm reject</button></div></dialog></section>;
}
