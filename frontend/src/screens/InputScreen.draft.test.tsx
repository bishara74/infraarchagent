import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router';
import {beforeEach,expect,it,vi} from 'vitest';
import {api} from '../api/client';
import {hydratePreferences,getPreferences} from '../lib/preferences';
import {InputScreen} from './InputScreen';

vi.mock('../hooks/useRunStream',()=>({useRunStream:()=>({results:null})}));
const text='Deploy a saved AWS web service with Terraform.';
beforeEach(async()=>{
 sessionStorage.clear();
 vi.spyOn(api,'request').mockImplementation(async(url,method,body)=>{
  if(url.startsWith('/api/models'))return {provider:'stub',credential_id:null,models:[],defaults:{}} as never;
  if(url.endsWith('recent-runs'))return [] as never;
  if(method==='PUT')return {...body as object,updated_at:'2026-10-23T10:00:00Z'} as never;
  return {revision:1,data:{prompt_draft:text,draft_config:{max_iterations:3}},updated_at:'2026-10-23T09:00:00Z'} as never;
 });
 await hydratePreferences('draft-tests',true);
});
function show(){return render(<MemoryRouter><InputScreen/></MemoryRouter>);}
it('FR-UI-01 saved drafts stay out of the editor until Restore is clicked',async()=>{
 show();expect(screen.getByLabelText('Infrastructure description')).toHaveValue('');
 expect(screen.getByText(/You have an unsent draft from/)).toBeVisible();
 fireEvent.click(screen.getByRole('button',{name:'Restore'}));
 expect(screen.getByLabelText('Infrastructure description')).toHaveValue(text);expect(screen.getByLabelText('Infrastructure description')).toHaveFocus();
 expect(getPreferences().data.draft_config.max_iterations).toBe(3);
});
it('FR-UI-01 Dismiss preserves the server draft and the next mount offers it again',()=>{
 const root=show();fireEvent.click(screen.getByRole('button',{name:'Dismiss draft hint'}));
 expect(screen.queryByText(/You have an unsent draft/)).toBeNull();expect(getPreferences().data.prompt_draft).toBe(text);
 root.unmount();show();expect(screen.getByRole('button',{name:'Restore'})).toBeVisible();expect(screen.getByLabelText('Infrastructure description')).toHaveValue('');
});
it('FR-UI-01 Discard clears the server draft without changing saved configuration',async()=>{
 show();fireEvent.click(screen.getByRole('button',{name:'Discard'}));
 await waitFor(()=>expect(screen.queryByText(/You have an unsent draft/)).toBeNull());
 const writes=vi.mocked(api.request).mock.calls.filter(([,method])=>method==='PUT');
 expect(writes.length).toBeGreaterThan(0);expect((writes.at(-1)![2] as {data:{prompt_draft:string}}).data.prompt_draft).toBe('');
 expect(getPreferences().data.draft_config.max_iterations).toBe(3);expect(screen.getByLabelText('Infrastructure description')).toHaveValue('');
});
it('FR-UI-01 failed Discard keeps recovery actions and can retry',async()=>{
 const previous=vi.mocked(api.request).getMockImplementation()!;let fail=true;
 vi.mocked(api.request).mockImplementation((url,method,body,signal)=>method==='PUT'&&fail?Promise.reject(new Error('offline')):previous(url,method,body,signal));
 show();fireEvent.click(screen.getByRole('button',{name:'Discard'}));
 expect(await screen.findByText(/saved draft could not be discarded/)).toBeVisible();expect(screen.getByRole('button',{name:'Restore'})).toBeEnabled();
 fail=false;fireEvent.click(screen.getByRole('button',{name:'Retry discard'}));await waitFor(()=>expect(screen.queryByText(/You have an unsent draft/)).toBeNull());
});
it('FR-UI-01 examples populate only on click and fresh typing replaces the draft',()=>{
 show();fireEvent.change(screen.getByLabelText('Infrastructure description'),{target:{value:'A different AWS infrastructure request'}});
 expect(getPreferences().data.prompt_draft).toBe('A different AWS infrastructure request');expect(screen.queryByText(/You have an unsent draft/)).toBeNull();
 fireEvent.click(screen.getByRole('button',{name:'Static site + CloudFront + S3'}));expect(screen.getByLabelText('Infrastructure description')).not.toHaveValue('A different AWS infrastructure request');
});
