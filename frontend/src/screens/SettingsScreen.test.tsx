import {beforeEach,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,within,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter,Route,Routes} from 'react-router';
import {api} from '../api/client';
import {setSessionStatus} from '../lib/sessionState';
import {SettingsScreen,ProviderPage,ModelsPage} from './SettingsScreen';
import {UsersSettings} from './UsersSettings';
import {AccountSettings} from './AccountSettings';
beforeEach(()=>{
 setSessionStatus({auth_required:true,authenticated:true,mode:'account',user:{id:'admin',username:'admin',role:'admin',created_at:'2026-10-01T10:00:00Z',last_login_at:null}});
 HTMLDialogElement.prototype.showModal=function(){this.open=true;};HTMLDialogElement.prototype.close=function(){this.open=false;this.dispatchEvent(new Event('close'));};
});
it('NFR-01 users table reset confirmation and enable actions preserve passwords in memory only',async()=>{
 const users=[{id:'r',username:'reviewer',role:'reviewer',disabled:true,created_at:'2026-10-01T10:00:00Z',last_login_at:null}];
 const request=vi.spyOn(api,'request').mockImplementation(async(_url,method)=>(method==='POST'?{updated:true}:users) as never);
 render(<UsersSettings/>);expect(await screen.findByRole('table')).toBeVisible();expect(screen.getByRole('columnheader',{name:'Last login'})).toBeVisible();expect(screen.getByText('Never')).toBeVisible();
 await userEvent.click(screen.getByRole('button',{name:'Enable reviewer'}));await waitFor(()=>expect(request).toHaveBeenCalledWith('/api/auth/users/r/enable','POST'));
 const reset=screen.getByRole('button',{name:'Reset password for reviewer'});await userEvent.click(reset);
 const dialog=screen.getByRole('dialog',{name:'Reset password for reviewer'});expect(within(dialog).getByLabelText('New password',{exact:true})).toHaveFocus();
 expect(within(dialog).getByLabelText('Username for password reset')).toHaveValue('reviewer');
 fireEvent.change(within(dialog).getByLabelText('New password',{exact:true}),{target:{value:'synthetic-new-password'}});fireEvent.change(within(dialog).getByLabelText('Confirm password',{exact:true}),{target:{value:'different-password'}});
 fireEvent.submit(dialog.querySelector('form')!);expect(within(dialog).getByText('Passwords must match.')).toBeVisible();
 fireEvent.change(within(dialog).getByLabelText('Confirm password',{exact:true}),{target:{value:'synthetic-new-password'}});fireEvent.submit(dialog.querySelector('form')!);
 await waitFor(()=>expect(request).toHaveBeenCalledWith('/api/auth/users/r/password','POST',{password:'synthetic-new-password'}));await waitFor(()=>expect(dialog).not.toHaveAttribute('open'));await waitFor(()=>expect(reset).toHaveFocus());expect(JSON.stringify({...localStorage,...sessionStorage})).not.toContain('synthetic-new-password');
});
it('NFR-01 create reviewer requires confirmation before submitting',async()=>{
 const request=vi.spyOn(api,'request').mockResolvedValue([]);render(<UsersSettings/>);await screen.findByRole('table');
 const form=screen.getByRole('heading',{name:'Create reviewer'}).closest('form')!;
 fireEvent.change(within(form).getByLabelText('Username'),{target:{value:'new-reviewer'}});fireEvent.change(within(form).getByLabelText('New password',{exact:true}),{target:{value:'synthetic-password'}});
 fireEvent.submit(form);expect(within(form).getByText('Passwords must match.')).toBeVisible();expect(request.mock.calls.some(([,method])=>method==='POST')).toBe(false);
 fireEvent.change(within(form).getByLabelText('Confirm password',{exact:true}),{target:{value:'synthetic-password'}});fireEvent.submit(form);await waitFor(()=>expect(request).toHaveBeenCalledWith('/api/auth/users','POST',{username:'new-reviewer',password:'synthetic-password'}));
});
it('NFR-01 account metadata preferences and confirmed password change use existing API',async()=>{
 const request=vi.spyOn(api,'request').mockResolvedValue({updated:true});const logout=vi.spyOn(api,'logout').mockResolvedValue(undefined);
 render(<AccountSettings/>);expect(screen.getByRole('heading',{name:'admin'})).toBeVisible();expect(screen.getByText('Never')).toBeVisible();expect(screen.getByRole('checkbox',{name:'Auto-scroll live log'})).toBeChecked();
 expect(screen.getByLabelText('Account username')).toHaveValue('admin');
 expect(screen.getByRole('checkbox',{name:'Hide whitespace-only changes'})).toBeChecked();
 fireEvent.change(screen.getByLabelText('Current password',{exact:true}),{target:{value:'synthetic-current'}});fireEvent.change(screen.getByLabelText('New password',{exact:true}),{target:{value:'synthetic-new-password'}});fireEvent.change(screen.getByLabelText('Confirm password',{exact:true}),{target:{value:'synthetic-new-password'}});
 fireEvent.submit(screen.getByRole('button',{name:'Change password'}).closest('form')!);await waitFor(()=>expect(logout).toHaveBeenCalledOnce());expect(request).toHaveBeenCalledWith('/api/auth/password','POST',{current_password:'synthetic-current',password:'synthetic-new-password'});
});
it('FR-UI-01 provider permits saving no-credit keys and confirms revocation',async()=>{
 const saved={storage_enabled:true,default_credential_id:'saved',credentials:[{id:'saved',label:'Demo key',provider:'openrouter',last4:'only',revoked:false,base_url:'https://example.invalid'}]};
 const request=vi.spyOn(api,'request').mockImplementation(async(url,method)=>(url.endsWith('/probe')?{status:'no_credit',models:[]}:method==='POST'?{id:'saved'}:saved) as never);
 render(<MemoryRouter><ProviderPage/></MemoryRouter>);await screen.findByText('Demo key');
 const revoke=screen.getByRole('button',{name:'Revoke'});await userEvent.click(revoke);expect(request.mock.calls.some(([url])=>url.endsWith('/revoke'))).toBe(false);await userEvent.click(screen.getByRole('button',{name:'Cancel'}));expect(revoke).toHaveFocus();
 await userEvent.click(revoke);await userEvent.click(screen.getByRole('button',{name:'Confirm revoke'}));await waitFor(()=>expect(request).toHaveBeenCalledWith('/api/providers/saved/revoke','POST'));await waitFor(()=>expect(revoke).toHaveFocus());
 fireEvent.paste(screen.getByLabelText('Provider API key'));fireEvent.change(screen.getByLabelText('Provider API key'),{target:{value:'synthetic-no-credit-key'}});
 await screen.findByText(/This key can be saved without credit/);expect(screen.getByRole('button',{name:'Save and use provider'})).toBeEnabled();await userEvent.click(screen.getByRole('button',{name:'Save and use provider'}));await waitFor(()=>expect(request.mock.calls.some(([url,method])=>url==='/api/providers'&&method==='POST')).toBe(true));
});
it.each(['custom','openrouter'])('FR-UI-01 model capability declarations are scoped to custom providers: %s',async provider=>{
 vi.spyOn(api,'request').mockImplementation(async url=>(url.endsWith('/defaults')?{defaults:{},static_models:[]}:{provider,credential_id:null,defaults:{},models:[]}) as never);
 render(<MemoryRouter><ModelsPage/></MemoryRouter>);await screen.findByRole('heading',{name:'Administrator defaults'});
 await waitFor(()=>expect(screen.queryByText('Loading model settings…')).toBeNull());
 if(provider==='custom'){const declaration=screen.getByText('Declare model capabilities',{selector:'summary'});expect(declaration.closest('details')).not.toHaveAttribute('open');}else expect(screen.queryByText('Declare model capabilities')).toBeNull();
 expect(screen.getByText(/Explicit request choices override personal defaults/)).toBeVisible();
});
it('NFR-01 reviewer settings navigation hides user/provider management and denies deep links',()=>{
 setSessionStatus({auth_required:true,authenticated:true,mode:'account',user:{id:'r',username:'reviewer',role:'reviewer'}});
 render(<MemoryRouter initialEntries={['/settings/users']}><Routes><Route path="/settings/:section" element={<SettingsScreen/>}/></Routes></MemoryRouter>);
 expect(screen.queryByRole('link',{name:'Users'})).toBeNull();expect(screen.queryByRole('link',{name:'Provider'})).toBeNull();expect(screen.getByText('Ask an administrator to manage this setting.')).toBeVisible();
});
