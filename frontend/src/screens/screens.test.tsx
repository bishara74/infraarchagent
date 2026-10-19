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
function show(component:React.ReactNode,path='/runs/run'){return render(<MemoryRouter initialEntries={[path]}><Routes><Route path="/" element={component}/><Route path="/runs/:runId" element={component}/><Route path="/runs/:runId/compare" element={component}/><Route path="/runs/:runId/packages/:variant" element={component}/></Routes></MemoryRouter>);}
afterEach(()=>{sessionStorage.clear();});
it.each([ProgressScreen,ComparisonScreen,PackageScreen])('screen loading and safe errors',Component=>{snapshot(null);const root=show(<Component/>,'/runs/run/packages/security');expect(screen.getByRole('status')).toHaveTextContent('Loading');root.unmount();snapshot(null,new ApiError(404,'run_not_found','Run not found.'));show(<Component/>);expect(screen.getByRole('alert')).toHaveTextContent('Run not found.');});
it('FR-UI-01 incomplete submissions reach validation and empty config is omitted',async()=>{snapshot();vi.spyOn(api,'submitRun').mockRejectedValue(new ApiError(400,'invalid_input','Description is too short.'));show(<InputScreen/>,'/');await userEvent.click(screen.getByRole('button',{name:'Generate'}));expect(api.submitRun).toHaveBeenCalledWith('',{});expect(screen.getByRole('alert')).toHaveTextContent('Description is too short.');expect(screen.getByLabelText('Infrastructure description')).toHaveFocus();});
it('FR-UI-01 guard survives route reload and submission starts immediately',async()=>{snapshot({...pending,run:{...pending.run,status:'running'}} as ResultsResponse);setActiveRun('run');show(<InputScreen/>,'/');expect(screen.getByRole('button',{name:'Generate'})).toBeDisabled();});
it('FR-UI-01 successful submit stores ID and pending request disables Generate',async()=>{snapshot(null);let finish!:(value:{run_id:string;status:'created';stream_url:string})=>void;vi.spyOn(api,'submitRun').mockImplementation(()=>new Promise(resolve=>{finish=resolve;}));show(<InputScreen/>,'/');await userEvent.click(screen.getByRole('button',{name:'Generate'}));expect(screen.getByRole('button',{name:'Generate…'})).toBeDisabled();finish({run_id:'new-run',status:'created',stream_url:'/stream'});await vi.waitFor(()=>expect(sessionStorage.getItem('infraarch.activeRun')).toBe('new-run'));});
it('FR-UI-03 missing variants, actual counts and URL selection',async()=>{snapshot({...pending,missing_variants:[{variant:'cost',error:'Generation failed.'}]} as ResultsResponse);show(<ComparisonScreen/>,'/runs/run/compare');expect(screen.getByText(/Cost variant unavailable:/i)).toBeVisible();expect(screen.getAllByText('0 → 0')).toHaveLength(3);await userEvent.click(screen.getAllByRole('button',{name:'Select this variant'})[1]!);expect(screen.getByRole('button',{name:'Selected'})).toHaveAttribute('aria-pressed','true');});
it('comparison empty state',()=>{snapshot({...pending,packages:[]} as ResultsResponse);show(<ComparisonScreen/>,'/runs/run/compare');expect(screen.getByText('No packages were generated.')).toBeVisible();});
it('FR-UI-06/07 review replaces download and repaired packages expose it',()=>{snapshot();const root=show(<PackageScreen/>,'/runs/run/packages/security');expect(screen.getByRole('button',{name:'Approve'})).toBeVisible();expect(screen.queryByRole('button',{name:'Download ZIP'})).toBeNull();root.unmount();snapshot(repaired as ResultsResponse);show(<PackageScreen/>,'/runs/run/packages/security');expect(screen.getByRole('button',{name:'Download ZIP'})).toBeVisible();expect(screen.queryByRole('button',{name:'Approve'})).toBeNull();expect(document.querySelector('.diff-row.add .marker')).toHaveTextContent('+');});
it('FR-UI-05 validation statuses and file links are accessible',async()=>{snapshot();show(<PackageScreen/>,'/runs/run/packages/security');await userEvent.click(screen.getByRole('tab',{name:'Validation report'}));expect(screen.getAllByText('failed').length).toBeGreaterThan(0);expect(screen.getByText('warning')).toBeVisible();expect(screen.getByText('terraform.local_ref · builtin')).toBeVisible();await userEvent.click(screen.getAllByRole('button',{name:'terraform/main.tf:4'})[0]!);expect(screen.getByRole('heading',{name:'terraform/main.tf'})).toBeVisible();});
it('unavailable variant and missing selected file are honest states',()=>{snapshot();const root=show(<PackageScreen/>,'/runs/run/packages/absent');expect(screen.getByText('This variant is unavailable.')).toBeVisible();root.unmount();show(<PackageScreen/>,'/runs/run/packages/security?file=absent');expect(screen.getByText(/requested file is unavailable/)).toBeVisible();});
it('generated text is escaped',()=>{const value=structuredClone(pending) as ResultsResponse;value.packages[2]!.files['terraform/main.tf']='<img src=x onerror=alert(1)>';snapshot(value);show(<PackageScreen/>,'/runs/run/packages/security');expect(document.querySelector('img')).toBeNull();expect(screen.getByText('<img src=x onerror=alert(1)>')).toBeVisible();});
it('401 permits key reentry on the current route',async()=>{snapshot(null,new ApiError(401,'unauthorized','Authentication required.'));vi.spyOn(api,'login').mockResolvedValue(undefined);show(<PackageScreen/>,'/runs/run/packages/security');fireEvent.change(screen.getByLabelText('API key'),{target:{value:'test-only'}});await userEvent.click(screen.getByRole('button',{name:'Continue'}));expect(sessionStorage.getItem('infraarch.apiKey')).toBeNull();expect(api.login).toHaveBeenCalledWith('test-only');expect(state.current.reconnect).toHaveBeenCalled();});


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
 if(action==='reject'){
  // jsdom lacks native dialog methods; keep the real Reject/Confirm UI path.
  const dialog=document.querySelector('dialog')!;
  dialog.showModal=()=>{dialog.open=true;};dialog.close=()=>{dialog.open=false;};
  await userEvent.click(screen.getByRole('button',{name:'Reject'}));
  await userEvent.click(screen.getByRole('button',{name:'Confirm reject'}));
 }else await userEvent.click(screen.getByRole('button',{name:'Approve'}));
 await vi.waitFor(()=>expect(state.current.reconnect).toHaveBeenCalledExactlyOnceWith());
 expect(api.review).toHaveBeenCalledExactlyOnceWith('run','security',{action,reviewer_name:'',reason:''});
 expect(state.current.reopenRetry).not.toHaveBeenCalled();expect(state.current.refresh).toHaveBeenCalled();
});
