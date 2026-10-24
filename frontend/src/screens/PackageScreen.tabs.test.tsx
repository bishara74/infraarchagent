import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {MemoryRouter,Routes,Route} from 'react-router';
import {expect,it,vi} from 'vitest';
import pending from '../test/fixtures/pending-results.json';
import repaired from '../test/fixtures/repaired-results.json';
import {PackageScreen} from './PackageScreen';
import {ComparisonScreen} from './ComparisonScreen';
import {api} from '../api/client';
import {setSessionStatus} from '../lib/sessionState';
const current=vi.hoisted(()=>({results:null as unknown}));
vi.mock('../hooks/useRunResults',()=>({useRunResults:()=>({results:current.results,events:[],state:'closed',pendingRetries:[],reconnect:vi.fn(),refresh:vi.fn(async()=>current.results),reopenRetry:vi.fn()})}));
function show(path='/runs/run/packages/security'){return render(<MemoryRouter initialEntries={[path]}><Routes><Route path="/runs/:runId/compare" element={<ComparisonScreen/>}/><Route path="/runs/:runId/packages/:variant" element={<PackageScreen/>}/></Routes></MemoryRouter>);}
it('FR-UI-03/04/05/07 overview starts without file trees; inspection exposes accessible on-demand tabs',async()=>{
 current.results=pending;show('/runs/run/compare');expect(screen.queryByRole('region',{name:'security package files'})).toBeNull();expect(screen.getByRole('button',{name:'Download all three'})).toBeDisabled();
 fireEvent.click(screen.getAllByRole('link',{name:'Inspect this variant'})[2]!);expect(screen.getByRole('heading',{name:'security package'})).toBeVisible();expect(screen.getByRole('region',{name:'Current file content'})).toBeVisible();expect(screen.queryByRole('button',{name:'Approve'})).toBeNull();
 fireEvent.click(screen.getByRole('tab',{name:'Security fixes'}));expect(screen.getByRole('region',{name:'Unified file diff'})).toBeVisible();expect(screen.getByRole('checkbox',{name:'Hide whitespace-only changes'})).toBeChecked();expect(screen.getByRole('link',{name:'terraform/main.tf'})).toHaveAttribute('href','/runs/run/packages/security?tab=fixes&file=terraform%2Fmain.tf');expect(screen.getAllByRole('tablist')).toHaveLength(1);
 fireEvent.click(screen.getByRole('tab',{name:'Findings'}));expect(screen.getByRole('heading',{name:'Validation report'})).toBeVisible();
 fireEvent.click(screen.getByRole('tab',{name:'Review'}));expect(screen.getByRole('button',{name:'Approve'})).toBeVisible();
 fireEvent.keyDown(screen.getByRole('tab',{name:'Review'}),{key:'Home'});await waitFor(()=>expect(screen.getByRole('tab',{name:'Files'})).toHaveFocus());expect(screen.getByRole('tab',{name:'Files'})).toHaveAttribute('aria-selected','true');
});
it('FR-UI-06 overview enables the bundle only for all three downloadable packages',()=>{
 current.results=repaired;const root=show('/runs/run/compare');expect(screen.getByRole('button',{name:'Download all three'})).toBeEnabled();expect(screen.getAllByRole('button',{name:'Download this variant'})).toHaveLength(3);root.unmount();
 current.results={...repaired,packages:repaired.packages.slice(1),missing_variants:[{variant:'cost',error:'failed'}]};show('/runs/run/compare');expect(screen.getByRole('button',{name:'Download all three'})).toBeDisabled();
});
it('FR-UI-07 review targets only the selected variant and restores the review deep link',async()=>{
 const value=structuredClone(pending);value.packages[1]={...pending.packages[2]!,variant:'performance'};current.results=value;setSessionStatus({authenticated:true,auth_required:true,mode:'account',user:{id:'reviewer',username:'Reviewer',role:'reviewer'}});
 const request=vi.spyOn(api,'review').mockResolvedValue({run_id:'run',variant:'performance',status:'engineer_approved'});
 show('/runs/run/packages/performance?tab=review');expect(screen.getByRole('tab',{name:'Review'})).toHaveAttribute('aria-selected','true');fireEvent.change(screen.getByLabelText('Reason category'),{target:{value:'other'}});fireEvent.change(screen.getByLabelText('Decision reason'),{target:{value:'Selected performance only.'}});fireEvent.click(screen.getByRole('button',{name:'Approve'}));
 await waitFor(()=>expect(request).toHaveBeenCalledExactlyOnceWith('run','performance',{action:'approve',reviewer_name:'Reviewer',category:'other',reason:'Selected performance only.'}));
});
