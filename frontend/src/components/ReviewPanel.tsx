import {ActionButton,ActionGate} from './ActionGate';
import {approvalCategories,rejectionCategories,categoryLabel} from '../lib/reviewCategories';
import { getSessionStatus } from '../lib/sessionState';
import { useRef, useState } from 'react';
import { api, ApiError, errorMessage, saveDownload } from '../api/client';
import type { PackageResult, ReviewRequest, ReviewCategory } from '../api/types';
import { reviewReason } from '../lib/reviewReasons';
import { Authentication } from './Authentication';
import { Icon } from './Icon';
import { StatusBadge } from './StatusBadge';
import {LessonProposalAction} from './LessonProposalAction';
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
    const [decisionKind,setDecisionKind]=useState<'approve'|'reject'>('reject');
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
        setDecisionKind(kind);
        const allowed=kind==='approve'?approvalCategories:rejectionCategories;
        if(category&&!(category in allowed)){setCategory('');invalid('Choose a reason category.',categoryField.current);return;}
        if(!name){invalid('Enter a reviewer name and decision reason.',reviewerField.current);return;}
        if(!category){invalid('Choose a reason category.',categoryField.current);return;}
        if(!explanation){invalid('Enter a reviewer name and decision reason.',reasonField.current);return;}
        setDecisionError(null);void action({action:kind,reviewer_name:name,reason:explanation,category});
    }
    return <section className="panel review" aria-label="Package readiness and review">{(retryPending || item.retry_in_progress) ? <div><p role="status">Retry in progress…</p><UnavailableReviewActions reason="A remediation retry is in progress." nextStep="Wait for the retry to finish, then inspect its updated findings."/></div> : actions.length>0 ? <>{item.review_available?<h2>Pending review</h2>:<p>No review needed — this package passed all automatic checks.</p>}{item.review_reasons.map(reason => <p key={reason}>{reviewReason(reason)}</p>)}{account ? <p>Reviewer: {account.username} · authenticated account</p> : <><label>Reviewer name<input ref={reviewerField} aria-describedby="decision-help" autoComplete="name" name="reviewer_name" value={reviewer} onChange={event => setReviewer(event.target.value)} maxLength={120}/></label><p className="muted">Self-declared identity; authentication does not verify your name.</p></>}<label>Decision<select aria-label="Decision" value={decisionKind} onChange={event=>{setDecisionKind(event.target.value as 'approve'|'reject');setCategory('');}}>{actions.includes('approve')&&<option value="approve">Approve</option>}<option value="reject">Reject</option></select></label><label>Reason category<select name="review_category" aria-describedby="decision-help" aria-invalid={decisionError==='Choose a reason category.'||undefined} aria-label="Reason category" ref={categoryField} value={category} onChange={event=>setCategory(event.target.value as ReviewCategory|'')} required><option value="">Choose a category…</option>{Object.entries(decisionKind==='approve'?approvalCategories:rejectionCategories).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><label>Decision reason<textarea ref={reasonField} aria-describedby="decision-help" name="decision_reason" value={reason} onChange={event => setReason(event.target.value)} maxLength={2000}/></label><p id="decision-help" className="muted">A category and decision reason are required; account identity is recorded automatically.</p>{decisionError && <p role="alert">{decisionError}</p>}<div className="actions">{item.downloadable&&item.readiness_label&&<StatusBadge status={item.readiness_label}/>} {<ActionButton disabled={busy||!actions.includes('approve')} unavailableReason={busy?'A review request is in progress.':'Approval is available only for a pending package after the run finishes.'} nextStep={busy?'Wait for the request to finish.':'Review the retained label and reports, or wait for the run to finish.'} onClick={() => decide('approve')}>Approve</ActionButton>}{<ActionButton disabled={busy||!actions.includes('retry')} unavailableReason={busy?'A review request is in progress.':'Retry is available only for a pending package after the run finishes.'} nextStep={busy?'Wait for the request to finish.':'Review the retained reports, or wait for the run to finish.'} onClick={() => setEditing(value => !value)}>Retry with feedback</ActionButton>}<ActionButton ref={reject} disabled={busy} className="destructive" onClick={() => {invalidField.current=null;dialog.current?.showModal();}}>Reject</ActionButton>{<ActionButton unavailableReason="This package needs an engineer decision before download." nextStep="Approve or reject after reviewing the findings." className="primary" disabled={busy||!item.downloadable} onClick={()=>{setBusy(true);setError(null);void saveDownload(runId,item.variant).catch(setError).finally(()=>setBusy(false));}}><Icon name="cloud-download"/>Download ZIP{busy?'…':''}</ActionButton>}</div>{editing && <form onSubmit={event => { event.preventDefault(); void action({ action: 'retry', ...(feedback.trim() ? { feedback: feedback.trim() } : {}), ...(targets.length ? { target_files: targets } : {}) }); }}><label htmlFor="review-feedback">Feedback</label><ActionGate disabled={busy} label="Retry feedback" reason="A review request is in progress." nextStep="Wait for it to finish before editing feedback."><textarea id="review-feedback" name="feedback" rows={3} value={feedback} disabled={busy} onChange={event => setFeedback(event.target.value)} autoFocus/></ActionGate><p className="muted">{Array.from(feedback.trim()).length} / 2000 characters</p>{item.retry_targets.length === 0 && <ActionGate disabled={busy} label="Retry target files" reason="A review request is in progress." nextStep="Wait for the request to finish before changing targets."><fieldset disabled={busy}><legend>Target files (up to 5)</legend>{Object.keys(item.files).sort().map(path => <ActionGate key={path} disabled={!targets.includes(path) && targets.length >= 5} label={path} reason="Five target files are already selected." nextStep="Uncheck a selected file to choose another."><label className="checkbox"><input type="checkbox" name="target_files" checked={targets.includes(path)} disabled={!targets.includes(path) && targets.length >= 5} onChange={event => setTargets(previous => event.target.checked ? [...previous, path] : previous.filter(value => value !== path))}/>{path}</label></ActionGate>)}</fieldset></ActionGate>}<ActionButton disabled={busy} type="submit">Submit retry{busy ? '…' : ''}</ActionButton></form>}</> : item.downloadable ? <div className="actions">{item.readiness_label && <StatusBadge status={item.readiness_label}/>}<ActionButton className="primary" disabled={busy} onClick={() => { setBusy(true); setError(null); void saveDownload(runId, item.variant).catch(cause => setError(cause)).finally(() => setBusy(false)); }}><Icon name="cloud-download"/>Download ZIP{busy ? '…' : ''}</ActionButton></div> : <div><p className="muted">Download becomes available when this package has a readiness label.</p><ActionButton disabled unavailableReason="This package is still processing or needs an engineer decision." nextStep="Wait for processing to finish, then review its findings.">Download ZIP</ActionButton></div>}
 {item.downloadable && item.readiness_label && !(retryPending || item.retry_in_progress) && <p className="muted">Label origin: {origin ?? 'unavailable (transition event not recorded)'}</p>}
 {item.review_decision && <div className="decision-summary" aria-label="Recorded decision"><p>Reviewer: {item.review_decision.reviewer_name ?? 'unavailable'} — {item.review_decision.identity_basis}</p><p>Decision time: {item.review_decision.decided_at ?? 'unavailable'}</p><p>Category: {categoryLabel(item.review_decision.category)}</p><p>Reason: {item.review_decision.reason ?? 'unavailable'}</p></div>}
 <LessonProposalAction item={item}/>
 {busy && <span role="status" className="spinner">Request in progress…</span>}{error instanceof ApiError && error.status === 401 ? <Authentication onSaved={() => { setError(null); void onRefresh().catch(cause => setError(cause)); }}/> : error ? <p role="alert">{errorMessage(error)}</p> : null}
 <dialog ref={dialog} aria-labelledby="reject-title" onClose={() => {(invalidField.current??reject.current)?.focus();invalidField.current=null;}}><h2 id="reject-title">Reject this package?</h2><p>The package will be labelled rejected. Its ZIP will remain available.</p><div className="actions"><button autoFocus onClick={() => dialog.current?.close()}>Cancel</button><ActionButton className="destructive" disabled={busy} onClick={() => { dialog.current?.close(); decide('reject'); }}>Confirm reject</ActionButton></div></dialog></section>;
}

function UnavailableReviewActions({reason,nextStep}:{reason:string;nextStep:string}){return <div className="actions">{['Approve','Retry with feedback','Reject','Download ZIP'].map(label=><ActionButton key={label} disabled unavailableReason={reason} nextStep={nextStep}>{label}</ActionButton>)}</div>;}
