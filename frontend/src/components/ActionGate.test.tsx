import {act,fireEvent,render,screen,within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {expect,it,vi} from 'vitest';
import {MemoryRouter} from 'react-router';
import {ActionButton,ActionGate} from './ActionGate';
import {DownloadAllButton} from './DownloadAllButton';
import {DownloadButton} from './DownloadButton';
import {ReviewPanel} from './ReviewPanel';
import {LessonProposalAction} from './LessonProposalAction';
import {LessonForm} from './LessonForm';
import {LessonVersions} from './LessonVersions';
import pending from '../test/fixtures/pending-results.json';
import type {PackageResult} from '../api/types';
import {api} from '../api/client';

async function explained(control:HTMLElement){
 const gate=control.closest<HTMLElement>('.action-gate');expect(gate).not.toBeNull();
 const help=gate!.querySelector<HTMLElement>('.action-gate-help')!;
 expect(gate).toHaveAttribute('aria-describedby');expect(help.textContent?.length).toBeGreaterThan(30);
 fireEvent.mouseEnter(gate!);expect(help).toBeVisible();fireEvent.mouseLeave(gate!);
 act(()=>gate!.focus());expect(help).toBeVisible();expect(gate).toHaveFocus();
 fireEvent.keyDown(gate!,{key:'Escape'});fireEvent.click(gate!);expect(help).toBeVisible();
 expect(within(gate!).getByRole('status')).not.toBeEmptyDOMElement();
}

it.each(['button','select','checkbox','textarea','fieldset'])('FR-UI-01/06/07 %s gate explains hover focus click without activation',async kind=>{
 const action=vi.fn();
 render(kind==='button'?<ActionButton disabled onClick={action} unavailableReason="An engineer review is required." nextStep="Open the review before downloading.">Download</ActionButton>:<ActionGate disabled label={kind} reason="A request is in progress." nextStep="Wait for it to finish.">{kind==='select'?<select disabled aria-label={kind} onChange={action}><option>One</option></select>:kind==='checkbox'?<input disabled type="checkbox" aria-label={kind} onChange={action}/>:kind==='textarea'?<textarea disabled aria-label={kind} onChange={action}/>:<fieldset disabled aria-label={kind}><input onChange={action}/></fieldset>}</ActionGate>);
 const element=document.querySelector<HTMLElement>(':disabled')!;
 await explained(element);expect(action).not.toHaveBeenCalled();
});

it('FR-UI-06 enabled actions retain native focus and exactly one request',async()=>{
 const action=vi.fn();render(<ActionButton onClick={action}>Download</ActionButton>);
 const button=screen.getByRole('button',{name:'Download'});await userEvent.tab();expect(button).toHaveFocus();await userEvent.keyboard('{Enter}');expect(action).toHaveBeenCalledTimes(1);
 expect(document.querySelector('.action-gate')).toBeNull();
});

it('FR-UI-06 bundle names outstanding variants and links to their reviews',async()=>{
 const action=vi.spyOn(api,'downloadAll');render(<MemoryRouter><DownloadAllButton runId="run" available={false} blocked={[{variant:'cost',review:true},{variant:'performance',review:true}]}/></MemoryRouter>);
 const button=screen.getByRole('button',{name:'Download all three'});expect(button).toBeDisabled();await explained(button);
 expect(screen.getByRole('link',{name:'Review cost'})).toHaveAttribute('href','/runs/run/packages/cost?tab=review');expect(screen.getByRole('link',{name:'Review performance'})).toHaveAttribute('href','/runs/run/packages/performance?tab=review');
 expect(action).not.toHaveBeenCalled();
});

it.each(['Approve','Retry with feedback','Reject','Download ZIP'])('FR-UI-07 retained retry lock explains unavailable %s',async name=>{
 const item=structuredClone(pending.packages[2]) as PackageResult;item.retry_in_progress=true;
 const request=vi.spyOn(api,'review');render(<MemoryRouter><ReviewPanel item={item} runId="run" onRetry={vi.fn()} onRefresh={vi.fn()}/></MemoryRouter>);
 const button=screen.getByRole('button',{name});expect(button).toBeDisabled();await explained(button);expect(request).not.toHaveBeenCalled();
});

it.each(['Download this variant','Propose a lesson'])('FR-UI-06/07 explains unavailable %s without a request',async name=>{
 const item=structuredClone(pending.packages[2]) as PackageResult;
 render(name==='Download this variant'?<DownloadButton runId="run" variant="security" available={false} label={name}/>:<LessonProposalAction item={item}/>);
 const button=screen.getByRole('button',{name});expect(button).toBeDisabled();await explained(button);
});

it('FR-UI-07 lesson busy fields and proposal/cancel actions are explained',async()=>{
 vi.spyOn(api,'request').mockImplementation(async url=>url.endsWith('/filter')?{filter_result:{version:'2',passed:true,reasons:[]}} as never:new Promise(()=>undefined));
 render(<LessonForm initialRole="generator_security" initialCategory="other" decisionId="decision" onCancel={vi.fn()} onProposed={vi.fn()}/>);
 fireEvent.change(screen.getByLabelText('Lesson text'),{target:{value:'Prefer explicit retention.'}});
 fireEvent.submit(document.querySelector('form')!);
 await vi.waitFor(()=>expect(screen.getByRole('button',{name:/Submit lesson proposal/})).toBeDisabled());
 for(const control of document.querySelectorAll<HTMLElement>(':disabled'))await explained(control);
});

it('FR-UI-07 lesson version pagination explains both boundaries',async()=>{
 vi.spyOn(api,'request').mockResolvedValue({items:[],total:0});render(<LessonVersions lessonId="lesson" onSelect={vi.fn()}/>);
 await screen.findByText('Page 1 of 1');for(const name of ['Previous versions','Next versions'])await explained(screen.getByRole('button',{name}));
});
