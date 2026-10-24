import {afterEach,expect,it,vi} from 'vitest';
import {render,screen,fireEvent,within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter,Routes,Route} from 'react-router';
import pending from '../test/fixtures/pending-results.json';
import repaired from '../test/fixtures/repaired-results.json';
import type {ResultsResponse} from '../api/types';
import {api,ApiError} from '../api/client';
import {applySnapshot,initialModel} from '../lib/runReducer';
import {InputScreen} from './InputScreen';
import {ProgressScreen} from './ProgressScreen';
import {ComparisonScreen} from './ComparisonScreen';
import {PackageScreen} from './PackageScreen';
import {setActiveRun} from '../lib/sessionState';
const state=vi.hoisted(()=>({current:{} as Record<string,unknown>}));
vi.mock('../hooks/useRunStream',()=>({useRunStream:()=>state.current}));
vi.mock('../hooks/useRunResults',()=>({useRunResults:()=>state.current}));
function snapshot(value:ResultsResponse|null=pending as ResultsResponse,error:unknown=null){state.current={results:value,error,events:[],model:value?applySnapshot(initialModel(),value):initialModel(),state:'closed',pendingRetries:[],reconnect:vi.fn(),reopenRetry:vi.fn(),refresh:vi.fn(async()=>value)};}
function show(component:React.ReactNode,path='/runs/run'){if((component as {type?:unknown}).type===PackageScreen&&path.includes('/packages/')&&!path.includes('?'))path+='?tab=review';return render(<MemoryRouter initialEntries={[path]}><Routes><Route path="/" element={component}/><Route path="/runs/:runId" element={component}/><Route path="/runs/:runId/compare" element={component}/><Route path="/runs/:runId/packages/:variant" element={component}/></Routes></MemoryRouter>);}
afterEach(()=>{sessionStorage.clear();});
it.each([ProgressScreen,ComparisonScreen,PackageScreen])('screen loading and safe errors',Component=>{snapshot(null);const root=show(<Component/>,'/runs/run/packages/security');expect(screen.getByRole('status')).toHaveTextContent('Loading');root.unmount();snapshot(null,new ApiError(404,'run_not_found','Run not found.'));show(<Component/>);expect(screen.getByRole('alert')).toHaveTextContent('Run not found.');});
it('FR-UI-01 incomplete submissions reach validation and empty config is omitted',async()=>{snapshot();vi.spyOn(api,'submitRun').mockRejectedValue(new ApiError(400,'invalid_input','Description is too short.'));show(<InputScreen/>,'/');await userEvent.click(screen.getByRole('button',{name:'Generate'}));expect(api.submitRun).toHaveBeenCalledWith('',{});expect(screen.getByText('Description is too short.')).toBeVisible();expect(screen.getByLabelText('Infrastructure description')).toHaveFocus();});
it('FR-UI-01 guard survives route reload and submission starts immediately',async()=>{snapshot({...pending,run:{...pending.run,status:'running'}} as ResultsResponse);setActiveRun('run');show(<InputScreen/>,'/');expect(screen.getByRole('button',{name:'Generate'})).toBeDisabled();});
it('FR-UI-01 successful submit stores ID and pending request disables Generate',async()=>{snapshot(null);let finish!:(value:{run_id:string;status:'created';stream_url:string})=>void;vi.spyOn(api,'submitRun').mockImplementation(()=>new Promise(resolve=>{finish=resolve;}));show(<InputScreen/>,'/');await userEvent.click(screen.getByRole('button',{name:'Generate'}));expect(screen.getByRole('button',{name:'Generate…'})).toBeDisabled();finish({run_id:'new-run',status:'created',stream_url:'/stream'});await vi.waitFor(()=>expect(sessionStorage.getItem('infraarch.activeRun')).toBe('new-run'));});
it('FR-UI-03 missing variants, actual counts and URL selection',async()=>{snapshot({...pending,missing_variants:[{variant:'cost',error:'Generation failed.'}]} as ResultsResponse);show(<ComparisonScreen/>,'/runs/run/compare?variant=security');expect(screen.getByText(/Cost variant unavailable:/i)).toBeVisible();expect(screen.getAllByText('0 → 0')).toHaveLength(3);expect(screen.getByRole('article',{name:'security variant'})).toHaveClass('selected');expect(screen.getAllByRole('link',{name:'Inspect this variant'})).toHaveLength(3);});
it('comparison empty state',()=>{snapshot({...pending,packages:[]} as ResultsResponse);show(<ComparisonScreen/>,'/runs/run/compare');expect(screen.getByText('No packages were generated.')).toBeVisible();});
it('FR-UI-06/07 review replaces download and repaired packages expose it',()=>{snapshot();const root=show(<PackageScreen/>,'/runs/run/packages/security');expect(screen.getByRole('button',{name:'Approve'})).toBeVisible();expect(screen.queryByRole('button',{name:'Download ZIP'})).toBeNull();root.unmount();snapshot(repaired as ResultsResponse);show(<PackageScreen/>,'/runs/run/packages/security');expect(screen.getByRole('button',{name:'Download ZIP'})).toBeVisible();expect(screen.queryByRole('button',{name:'Approve'})).toBeNull();fireEvent.click(screen.getByRole('tab',{name:'Security fixes'}));expect(document.querySelector('.diff-row.add .marker')).toHaveTextContent('+');});
it('FR-UI-05 validation statuses and file links are accessible',async()=>{snapshot();show(<PackageScreen/>,'/runs/run/packages/security');await userEvent.click(screen.getByRole('tab',{name:'Findings'}));expect(screen.getAllByText('failed').length).toBeGreaterThan(0);expect(screen.getByText('warning')).toBeVisible();expect(screen.getByText('terraform.local_ref · builtin')).toBeVisible();await userEvent.click(screen.getAllByRole('button',{name:'terraform/main.tf:4'})[0]!);expect(screen.getByRole('heading',{name:'terraform/main.tf'})).toBeVisible();});
it('unavailable variant and missing selected file are honest states',()=>{snapshot();const root=show(<PackageScreen/>,'/runs/run/packages/absent');expect(screen.getByText('This variant is unavailable.')).toBeVisible();root.unmount();show(<PackageScreen/>,'/runs/run/packages/security?file=absent');expect(screen.getByText(/requested file is unavailable/)).toBeVisible();});
it('generated text is escaped',()=>{const value=structuredClone(pending) as ResultsResponse;value.packages[2]!.files['terraform/main.tf']='<img src=x onerror=alert(1)>';snapshot(value);show(<PackageScreen/>,'/runs/run/packages/security?tab=files');expect(document.querySelector('img')).toBeNull();expect(screen.getByText('<img src=x onerror=alert(1)>')).toBeVisible();});
it('401 permits account login on the current route',async()=>{snapshot(null,new ApiError(401,'unauthorized','Authentication required.'));vi.spyOn(api,'login').mockResolvedValue(undefined);show(<PackageScreen/>,'/runs/run/packages/security');fireEvent.change(screen.getByLabelText('Username'),{target:{value:'reviewer'}});fireEvent.change(screen.getByLabelText('Password'),{target:{value:'test-password-only'}});await userEvent.click(screen.getByRole('button',{name:'Log in'}));expect(sessionStorage.getItem('infraarch.apiKey')).toBeNull();expect(api.login).toHaveBeenCalledWith('reviewer','test-password-only',false);expect(state.current.reconnect).toHaveBeenCalled();});


it('FR-UI-06/07 screen 4 has one readiness badge beside download and a clear pending review heading',()=>{
 snapshot(repaired as ResultsResponse);const root=show(<PackageScreen/>,'/runs/run/packages/security');
 const panel=screen.getByRole('region',{name:'Package readiness and review'});
 expect(screen.getAllByText('checks passed',{exact:true})).toHaveLength(1);
 expect(within(panel).getByText('checks passed')).toBeVisible();
 expect(within(panel).getByRole('button',{name:'Download ZIP'}).parentElement).toContainElement(within(panel).getByText('checks passed'));
 expect(document.querySelector('.page-heading .badge')).toBeNull();
 root.unmount();snapshot();show(<PackageScreen/>,'/runs/run/packages/security');
 expect(screen.getByRole('heading',{name:'Pending review'})).toBeVisible();
 expect(screen.getByRole('button',{name:'Approve'})).toBeVisible();
 expect(screen.queryByRole('button',{name:'Download ZIP'})).toBeNull();
});

it.each(['approve','reject'] as const)('FR-UI-07/FR-P-04 %s resumes closed SSE to recover its label-origin event without a retry latch',async action=>{
 snapshot();expect(state.current.state).toBe('closed');
 vi.spyOn(api,'review').mockResolvedValue({run_id:'run',variant:'security',status:action==='approve'?'engineer_approved':'rejected'});
 show(<PackageScreen/>,'/runs/run/packages/security');
 await userEvent.type(screen.getByLabelText('Reviewer name'),' Test engineer ');
 await userEvent.selectOptions(screen.getByLabelText('Reason category'),'other');
 await userEvent.type(screen.getByLabelText('Decision reason'),' Reviewed remaining checks. ');
 if(action==='reject'){
  // jsdom lacks native dialog methods; keep the real Reject/Confirm UI path.
  const dialog=document.querySelector('dialog')!;
  dialog.showModal=()=>{dialog.open=true;};dialog.close=()=>{dialog.open=false;};
  await userEvent.click(screen.getByRole('button',{name:'Reject'}));
  await userEvent.click(screen.getByRole('button',{name:'Confirm reject'}));
 }else await userEvent.click(screen.getByRole('button',{name:'Approve'}));
 await vi.waitFor(()=>expect(state.current.reconnect).toHaveBeenCalledExactlyOnceWith());
 expect(api.review).toHaveBeenCalledExactlyOnceWith('run','security',{action,reviewer_name:'Test engineer',category:'other',reason:'Reviewed remaining checks.'});
 expect(state.current.reopenRetry).not.toHaveBeenCalled();expect(state.current.refresh).toHaveBeenCalled();
});

it('FR-UI-07 empty decisions focus the missing field without sending a request',async()=>{snapshot();const request=vi.spyOn(api,'review');show(<PackageScreen/>,'/runs/run/packages/security');await userEvent.click(screen.getByRole('button',{name:'Approve'}));expect(request).not.toHaveBeenCalled();expect(screen.getByRole('alert')).toHaveTextContent('Enter a reviewer name and decision reason.');expect(screen.getByLabelText('Reviewer name')).toHaveFocus();await userEvent.type(screen.getByLabelText('Reviewer name'),'Engineer');await userEvent.selectOptions(screen.getByLabelText('Reason category'),'other');await userEvent.click(screen.getByRole('button',{name:'Approve'}));expect(screen.getByLabelText('Decision reason')).toHaveFocus();expect(request).not.toHaveBeenCalled();});

it('FR-UI-05 strict and contextual totals are adjacent without promoting the label',()=>{const value=structuredClone(pending) as ResultsResponse;const item=value.packages[2]!;item.profile_assessments={'strict':{checks_passed:false,remaining_blocking:1,excepted:[]},'contextual-v1':{checks_passed:true,remaining_blocking:0,excepted:[]}};snapshot(value);show(<ComparisonScreen/>,'/runs/run/compare');expect(screen.getByText(/Assessment pass counts — strict: 2\/3 · contextual-v1: 3\/3/)).toBeVisible();expect(screen.getAllByText('pending review').length).toBeGreaterThan(0);});

it('FR-UI-05 v2 totals are additive and missing v2 remains unavailable',()=>{
 const value=structuredClone(pending) as ResultsResponse;
 for(const item of value.packages){item.profile_assessments!['contextual-v2']={checks_passed:true,remaining_blocking:0,excepted:[]};}
 snapshot(value);const root=show(<ComparisonScreen/>,'/runs/run/compare');
 expect(screen.getByText(/contextual-v2: 3\/3/)).toBeVisible();
 root.unmount();snapshot(pending as ResultsResponse);show(<ComparisonScreen/>,'/runs/run/compare');
 expect(screen.getAllByText(/contextual-v2: unavailable/).length).toBeGreaterThan(0);
});

it('FR-UI-01 configuration starts collapsed and shows actual server defaults and experimental guidance',async()=>{
 snapshot();vi.spyOn(api,'request').mockResolvedValue({provider:'stub',credential_id:null,models:[],defaults:{},server_default_max_iterations:7,environment_defaults:{architect:{model:'stub',thinking_mode:null},generator_cost:{model:'stub',thinking_mode:null},generator_performance:{model:'stub',thinking_mode:null},generator_security:{model:'stub',thinking_mode:null},fixer:{model:'stub',thinking_mode:null}}});
 show(<InputScreen/>,'/');await vi.waitFor(()=>expect(screen.getByText(/Defaults: stub · provider default · strict/)).toBeInTheDocument());
 expect(document.querySelector('details.config')).not.toHaveAttribute('open');
 await userEvent.click(screen.getByText('Configuration options',{exact:false,selector:'summary'}));
 expect(screen.getByPlaceholderText('Server default: 7')).toBeVisible();expect(screen.getByLabelText('Additional assessment (experimental)')).toBeVisible();expect(screen.getByText('Strict checks always decide the readiness label.')).toBeVisible();
 expect(screen.getByRole('button',{name:'Use defaults'}).closest('.input-actions')).not.toBeNull();
});

it('FR-UI-03 comparison explains static labels and offers downloads only when authorised',()=>{
 snapshot(repaired as ResultsResponse);show(<ComparisonScreen/>,'/runs/run/compare');
 expect(screen.getByText('Labels reflect static checks and engineer decisions only, not a deployment.')).toBeVisible();
 expect(screen.getAllByRole('button',{name:'Download this variant'})).toHaveLength(repaired.packages.filter(item=>item.downloadable).length);
 expect(document.querySelector('.file-tree')).toBeNull();expect(screen.getAllByRole('link',{name:'Inspect this variant'})).toHaveLength(3);
});

it('FR-UI-03 secondary check details remain available in compact comparison cards',async()=>{
 snapshot();show(<ComparisonScreen/>,'/runs/run/compare');const details=document.querySelectorAll('.variant-details');expect(details).toHaveLength(3);expect(details[0]).not.toHaveAttribute('open');await userEvent.click(screen.getAllByText('Check details')[0]!);expect(details[0]).toHaveAttribute('open');
});

it('FR-UI-01 model validation errors open configuration with actionable guidance',async()=>{
 snapshot();vi.spyOn(api,'submitRun').mockRejectedValue(new ApiError(400,'invalid_model','Choose a structured-output model for Generators and Fixer.'));
 show(<InputScreen/>,'/');await userEvent.click(screen.getByRole('button',{name:'Generate'}));expect(await screen.findByText(/Check the model and thinking fields in Configuration options/)).toBeVisible();expect(document.querySelector('details.config')).toHaveAttribute('open');
});
