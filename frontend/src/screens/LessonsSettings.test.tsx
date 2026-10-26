import {fireEvent,render,screen,waitFor,within} from '@testing-library/react';
import {MemoryRouter} from 'react-router';
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {api} from '../api/client';
import {controls,detail,lesson} from '../test/fixtures/lessons';
import type {LessonControls,LessonDetail} from '../api/types';
import {setSessionStatus} from '../lib/sessionState';
import {LessonsSettings} from './LessonsSettings';
import {SettingsScreen} from './SettingsScreen';

beforeEach(()=>{
  setSessionStatus({authenticated:true,auth_required:true,mode:'account',user:{id:'admin',username:'Admin',role:'admin'}});
  HTMLDialogElement.prototype.showModal=function(){this.open=true;};
  HTMLDialogElement.prototype.close=function(){if(!this.open)return;this.open=false;this.dispatchEvent(new Event('close'));};
});
afterEach(()=>{vi.restoreAllMocks();setSessionStatus(null);});

function setup(config:LessonControls=controls,initial:LessonDetail=detail){
  let current=structuredClone(initial);let control=structuredClone(config);
  const request=vi.spyOn(api,'request').mockImplementation(async(url,method,body)=>{
    if(url==='/api/lessons/control'){
      if(method==='PUT'){control={...control,runtime_enabled:(body as {enabled:boolean}).enabled,enabled:control.server_enabled&&(body as {enabled:boolean}).enabled};}
      return control as never;
    }
    if(url.endsWith('/confirmation'))return {confirmation_token:'fixture-confirmation-token',expires_at:'2026-10-25T12:05:00Z',lesson:current.lesson,preview:current.preview,set_version:control.set_version,require_second_approver:false,warning:'Four-eyes review is off. You are approving your own lesson.'} as never;
    if(method==='POST'&&url.endsWith('/approve')){current={...current,lesson:{...current.lesson,status:'approved',approved_by:'admin',approver:'Admin',self_approved:current.lesson.proposer_id==='admin'}};control={...control,set_version:1,lesson_count:1};return current.lesson as never;}
    if(method==='POST'&&(url.endsWith('/reject')||url.endsWith('/retire'))){current={...current,lesson:{...current.lesson,status:url.endsWith('/retire')?'retired':'rejected'}};return current.lesson as never;}
    if(url.startsWith('/api/lessons/history'))return {items:[{id:'audit',seq:1,actor_id:'admin',action:'approved',revision_id:lesson.id,previous_version:null,set_version:1,timestamp:'2026-10-25T12:00:00Z',payload:{actor:'Admin',self_approved:true}}],total:1,page:1,page_size:25} as never;
    if(url.startsWith('/api/lessons?'))return {items:[current.lesson],total:1,page:1,page_size:25} as never;
    return current as never;
  });
  render(<MemoryRouter initialEntries={[`/settings/lessons?lesson=${lesson.id}`]}><LessonsSettings/></MemoryRouter>);
  return request;
}

it('NFR-01 shows linked decision, filter and exact preview before approval without rendering HTML',async()=>{
  const request=setup();const dialog=await screen.findByRole('dialog',{name:'Lesson v1'});
  expect(within(dialog).getByRole('heading',{name:'Exact prompt preview'})).toBeVisible();
  expect(within(dialog).getByText('Passed deterministic filter · v1')).toBeVisible();
  expect(within(dialog).getByText('<script>raw decision reason</script>')).toBeVisible();expect(dialog.querySelector('script')).toBeNull();
  expect(within(dialog).getByRole('link',{name:'View source decision'})).toHaveAttribute('href',`/settings/review-history?decision_id=${lesson.decision_id}`);
  fireEvent.click(within(dialog).getByRole('button',{name:'Approve lesson'}));
  await waitFor(()=>expect(request).toHaveBeenCalledWith(`/api/lessons/${lesson.id}/approve`,'POST',{}));
  expect((await within(dialog).findAllByText('approved',{exact:true}))[0]).toBeVisible();
});

it('NFR-01 default four-eyes policy prevents self-approval in the UI',async()=>{
  const request=setup(controls,{...detail,lesson:{...lesson,proposer_id:'admin',proposer:'Admin'}});
  const dialog=await screen.findByRole('dialog',{name:'Lesson v1'});
  expect(within(dialog).getByText('A different named administrator must approve your proposal.')).toBeVisible();
  expect(within(dialog).getByRole('button',{name:'Approve lesson'})).toBeDisabled();
  expect(request.mock.calls.some(([url,method])=>method==='POST'&&url.endsWith('/approve'))).toBe(false);
});

it('NFR-01 self-approval repeats the filter and preview and requires a separate token-bound action',async()=>{
  const request=setup({...controls,require_second_approver:false},{...detail,lesson:{...lesson,proposer_id:'admin',proposer:'Admin'}});
  const dialog=await screen.findByRole('dialog',{name:'Lesson v1'});
  fireEvent.click(within(dialog).getByRole('button',{name:'Approve lesson'}));
  const confirm=await screen.findByRole('dialog',{name:'Confirm self-approval'});
  expect(within(confirm).getByText('Four-eyes review is off. You are approving your own lesson.')).toBeVisible();
  expect(within(confirm).getByText('Passed deterministic filter · v1')).toBeVisible();
  expect(within(confirm).getByLabelText('architect advisory block')).toHaveTextContent(lesson.text);
  expect(request.mock.calls.some(([url,method])=>method==='POST'&&url.endsWith('/approve'))).toBe(false);
  fireEvent.click(within(confirm).getByRole('button',{name:'Confirm self-approval'}));
  await waitFor(()=>expect(request).toHaveBeenCalledWith(`/api/lessons/${lesson.id}/approve`,'POST',{confirmation_token:'fixture-confirmation-token'}));
  expect(await within(dialog).findByText(/Approved by Admin.*self-approved/)).toBeVisible();
  expect(JSON.stringify({...localStorage,...sessionStorage})).not.toContain('fixture-confirmation-token');
});

it('NFR-01 server gate disables enabling while keeping immediate disable available',async()=>{
  const request=setup({...controls,server_enabled:false});await screen.findByRole('dialog',{name:'Lesson v1'});
  fireEvent.click(screen.getByRole('button',{name:'Close lesson'}));
  expect(screen.getByRole('checkbox',{name:'Use approved lessons'})).toBeDisabled();
  fireEvent.click(screen.getByRole('button',{name:'Disable lessons'}));
  await waitFor(()=>expect(request).toHaveBeenCalledWith('/api/lessons/control','PUT',{enabled:false}));
});

it('FR-UI-07 exposes history and a field diff, keeping immutable content out of edit actions for others',async()=>{
  setup(controls,{...detail,previous:{...lesson,text:'Previous preference.'}});
  const dialog=await screen.findByRole('dialog',{name:'Lesson v1'});
  expect(dialog.querySelector('del')).toHaveTextContent('Previous preference.');
  expect(within(dialog).getByRole('button',{name:'Propose new version'})).toBeDisabled();
  fireEvent.click(within(dialog).getByRole('button',{name:'Close lesson'}));
  fireEvent.click(screen.getByRole('button',{name:'History'}));
  expect(await screen.findByRole('cell',{name:'Admin'})).toBeVisible();
  expect(screen.getByText(/self-approved/)).toBeVisible();
});

it('NFR-01 reviewer Settings hide the admin Lessons route',()=>{
  setSessionStatus({authenticated:true,auth_required:true,mode:'account',user:{id:'reviewer',username:'Reviewer',role:'reviewer'}});
  const request=vi.spyOn(api,'request');render(<MemoryRouter><SettingsScreen/></MemoryRouter>);
  expect(screen.queryByRole('link',{name:'Lessons'})).toBeNull();expect(request).not.toHaveBeenCalled();
});

it.each(['reject','retire'] as const)('NFR-01 %s requires confirmation and cancellation leaves the lesson unchanged',async action=>{
  const request=setup(controls,{...detail,lesson:{...lesson,status:action==='retire'?'approved':'proposed'}});
  const inspector=await screen.findByRole('dialog',{name:'Lesson v1'});
  const label=action==='retire'?'Retire':'Reject';
  fireEvent.click(within(inspector).getByRole('button',{name:`${label} lesson`}));
  let confirm=await screen.findByRole('dialog',{name:`${label} this lesson?`});
  expect(within(confirm).getByText(lesson.text)).toBeVisible();
  fireEvent.click(within(confirm).getByRole('button',{name:'Cancel'}));
  expect(request.mock.calls.some(([url,method])=>method==='POST'&&url.endsWith(`/${action}`))).toBe(false);
  fireEvent.click(within(inspector).getByRole('button',{name:`${label} lesson`}));
  confirm=await screen.findByRole('dialog',{name:`${label} this lesson?`});
  fireEvent.click(within(confirm).getByRole('button',{name:`Confirm ${action}`}));
  await waitFor(()=>expect(request).toHaveBeenCalledWith(`/api/lessons/${lesson.id}/${action}`,'POST',{}));
  expect((await within(inspector).findAllByText(action==='retire'?'retired':'rejected',{exact:true}))[0]).toBeVisible();
});

it('FR-UI-07 an owner proposes an immutable successor from the existing structured content',async()=>{
  setup(controls,{...detail,lesson:{...lesson,status:'approved',proposer_id:'admin'}});
  const inspector=await screen.findByRole('dialog',{name:'Lesson v1'});
  fireEvent.click(within(inspector).getByRole('button',{name:'Propose new version'}));
  expect(within(inspector).getByLabelText('Lesson text',{exact:true})).toHaveValue(lesson.text);
  expect(within(inspector).getByLabelText('Lesson role',{exact:true})).toHaveValue(lesson.scope_role);
  expect(within(inspector).getAllByRole('button',{name:'Propose new version'})).toHaveLength(2);
});
