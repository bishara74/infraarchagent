import {expect,it,vi} from 'vitest';
import {render,screen,fireEvent} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import pending from '../test/fixtures/pending-results.json';
import type {PackageResult,ReviewResponse} from '../api/types';
import {api} from '../api/client';
import {ReviewPanel} from './ReviewPanel';
import {ReportPanel} from './ReportPanel';
const item=()=>structuredClone(pending.packages[2]) as PackageResult;
it('retry picker is limited to five existing files and only one request is active',async()=>{const value=item();value.retry_targets=[];value.files=Object.fromEntries(Array.from({length:6},(_,i)=>[`f${i}`,'text']));let finish!:(value:ReviewResponse)=>void;vi.spyOn(api,'review').mockImplementation(()=>new Promise(resolve=>{finish=resolve;}));const reopen=vi.fn();const refresh=vi.fn(async()=>undefined);render(<ReviewPanel item={value} runId="r" onRetry={reopen} onRefresh={refresh}/>);await userEvent.click(screen.getByRole('button',{name:'Retry with feedback'}));const inputs=screen.getAllByRole('checkbox');for(const input of inputs.slice(0,5))fireEvent.click(input);expect(inputs[5]).toBeDisabled();fireEvent.change(screen.getByLabelText('Feedback'),{target:{value:'Fix selected files.'}});await userEvent.click(screen.getByRole('button',{name:'Submit retry'}));expect(screen.getByRole('button',{name:'Approve'})).toBeDisabled();expect(api.review).toHaveBeenCalledExactlyOnceWith('r','security',{action:'retry',feedback:'Fix selected files.',target_files:['f0','f1','f2','f3','f4']});finish({run_id:'r',variant:'security',status:'scanning'});await vi.waitFor(()=>expect(reopen).toHaveBeenCalledTimes(1));expect(refresh).toHaveBeenCalled();});
it('marker-only retry suppresses review and download',()=>{const value=item();value.retry_in_progress=true;render(<ReviewPanel item={value} runId="r" onRetry={vi.fn()} onRefresh={vi.fn()}/>);expect(screen.getByRole('status')).toHaveTextContent('Retry in progress');expect(screen.queryByRole('button',{name:'Approve'})).toBeNull();expect(screen.queryByRole('button',{name:'Download ZIP'})).toBeNull();});
it('resolved and unresolved security evidence remain distinct',()=>{const value=item();value.security_report={sessions:[{kind:'automated',iterations:[{fixes:[{file:'a',accepted:true,rule_ids:['CKV_1'],summaries:['Fixed']}]}]}],final:{outcome:'exhausted',remaining_blocking:[{severity:'HIGH',rule_id:'CKV_2',message:'Still blocked',file_path:'a'}]}};render(<ReportPanel item={value} onFile={vi.fn()}/>);expect(screen.getByText('resolved')).toHaveClass('ok');expect(screen.getByText('unresolved')).toHaveClass('danger');expect(screen.getByText('HIGH')).toHaveClass('danger');});
it('FR-UI-07 retains the accepted retry lock until a settled EOF snapshot',async()=>{const value=item();vi.spyOn(api,'review').mockResolvedValue({run_id:'r',variant:'security',status:'remediating',stream_url:'/stream'});const reopen=vi.fn();const refresh=vi.fn(async()=>undefined);const props={item:value,runId:'r',onRetry:reopen,onRefresh:refresh};const root=render(<ReviewPanel {...props} retryPending={false}/>);await userEvent.click(screen.getByRole('button',{name:'Retry with feedback'}));await userEvent.click(screen.getByRole('button',{name:'Submit retry'}));await vi.waitFor(()=>expect(reopen).toHaveBeenCalled());root.rerender(<ReviewPanel {...props} retryPending/>);expect(screen.getByRole('status')).toHaveTextContent('Retry in progress');expect(screen.queryByRole('button',{name:'Approve'})).toBeNull();expect(screen.queryByRole('button',{name:'Download ZIP'})).toBeNull();root.rerender(<ReviewPanel {...props} retryPending={false}/>);await vi.waitFor(()=>expect(screen.getByRole('button',{name:'Approve'})).toBeVisible());});

it.each(['automatic (clean scan and valid validation)','automatic after an engineer-requested retry (clean scan and valid validation)','engineer decision'])('FR-UI-06 labelled action panel displays origin: %s',origin=>{
 const value=item();value.readiness_label='checks_passed';value.downloadable=true;value.review_available=false;
 render(<ReviewPanel item={value} origin={origin} runId="r" onRetry={vi.fn()} onRefresh={vi.fn()}/>);
 expect(screen.getByText('Label origin: '+origin,{exact:true})).toBeVisible();
 expect(screen.getByRole('button',{name:'Download ZIP'})).toBeVisible();
});

it('FR-S-04 contextual success leaves strict findings and the official pending label visible',()=>{
 const value=item();value.profile_assessments={strict:{checks_passed:false,remaining_blocking:1,excepted:[]},'contextual-v1':{checks_passed:true,remaining_blocking:0,excepted:[{rule_id:'AWS-0132',resource:'aws_s3_bucket.logs',file_path:'terraform/logs.tf',entry_id:'s3-log-target-sse-s3',classification:'excepted',justification:'Proven log destination'}]}};
 value.security_report={final:{outcome:'exhausted',remaining_blocking:[{rule_id:'AWS-0132',resource:'aws_s3_bucket.logs',file_path:'terraform/logs.tf',severity:'HIGH',message:'KMS required'}]}};
 render(<><ReviewPanel item={value} runId="r" onRetry={vi.fn()} onRefresh={vi.fn()}/><ReportPanel item={value} onFile={vi.fn()}/></>);
 expect(screen.getByRole('heading',{name:'Pending review'})).toBeVisible();
 expect(screen.queryByRole('button',{name:'Download ZIP'})).toBeNull();
 expect(screen.getByText('excepted')).toHaveClass('warn');
 expect(screen.getByText('unresolved')).toBeVisible();
 expect(screen.getByText('KMS required')).toBeVisible();
});
