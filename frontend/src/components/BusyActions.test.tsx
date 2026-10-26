import {act,fireEvent,render,screen} from '@testing-library/react';
import {expect,it,vi} from 'vitest';
import {MemoryRouter} from 'react-router';
import {Authentication} from './Authentication';
import {AccountMenu} from './AccountMenu';
import {AccountSettings} from '../screens/AccountSettings';
import {UsersSettings} from '../screens/UsersSettings';
import {ProviderPage} from '../screens/SettingsScreen';
import {ReviewHistorySettings} from '../screens/ReviewHistorySettings';
import {api} from '../api/client';

async function checkAll(){
 const disabled=[...document.querySelectorAll<HTMLElement>('button:disabled')].filter(control=>!control.closest('dialog:not([open])'));expect(disabled.length).toBeGreaterThan(0);
 for(const control of disabled){
  const gate=control.closest<HTMLElement>('.action-gate')!;expect(gate).not.toBeNull();
  const help=gate.querySelector('.action-gate-help')!;fireEvent.mouseEnter(gate);expect(help).toBeVisible();
  act(()=>gate.focus());expect(gate).toHaveFocus();expect(help).toBeVisible();fireEvent.click(gate);expect(help.textContent).toMatch(/Wait|wait|finish|Enter|Add|configure|Use|Choose/);
 }
}

it.each([false,true])('FR-UI-01 authentication busy actions are explained (setup=%s)',async setup=>{
 const request=vi.spyOn(api,'login').mockImplementation(()=>new Promise(()=>undefined));render(<Authentication setup={setup} onSaved={vi.fn()}/>);
 fireEvent.submit(document.querySelector('form')!);await checkAll();expect(request).toHaveBeenCalledTimes(1);
});

it('FR-UI-01 account password and logout busy actions are explained',async()=>{
 const request=vi.spyOn(api,'request').mockImplementation(()=>new Promise(()=>undefined));const root=render(<AccountSettings/>);
 fireEvent.submit(document.querySelector('form')!);await checkAll();expect(request).toHaveBeenCalledTimes(1);root.unmount();
 const logout=vi.spyOn(api,'logout').mockImplementation(()=>new Promise(()=>undefined));render(<MemoryRouter><AccountMenu username="Reviewer"/></MemoryRouter>);
 fireEvent.click(screen.getByRole('button',{name:'Reviewer'}));fireEvent.click(screen.getByRole('menuitem',{name:'Log out'}));await checkAll();expect(logout).toHaveBeenCalledTimes(1);
});

it('FR-UI-01 users create/reset/enable/disable busy actions are explained',async()=>{
 const users=[{id:'one',username:'Enabled reviewer',role:'reviewer',disabled:false,created_at:'2026-10-26T00:00:00Z',last_login_at:null},{id:'two',username:'Disabled reviewer',role:'reviewer',disabled:true,created_at:'2026-10-26T00:00:00Z',last_login_at:null}];
 const request=vi.spyOn(api,'request').mockImplementation(async(_url,method)=>method==='POST'?new Promise(()=>undefined):users as never);
 render(<UsersSettings/>);await screen.findByRole('table');fireEvent.submit(document.querySelector('.create-reviewer')!);await checkAll();
 expect(request.mock.calls.filter(([,method])=>method==='POST')).toHaveLength(1);
});

it('FR-UI-01 provider save/test/use/revoke busy actions are explained',async()=>{
 const saved={storage_enabled:true,default_credential_id:null,credentials:[{id:'one',provider:'openrouter',label:'Synthetic',last4:'only',revoked:false,base_url:''}]};
 const request=vi.spyOn(api,'request').mockImplementation(async(_url,method)=>method==='POST'?new Promise(()=>undefined):saved as never);
 render(<MemoryRouter><ProviderPage/></MemoryRouter>);await screen.findByText('Synthetic');fireEvent.submit(document.querySelector('form')!);await checkAll();
 expect(request.mock.calls.filter(([,method])=>method==='POST')).toHaveLength(1);
});

it('FR-UI-07 review-history export and page boundaries are explained',async()=>{
 vi.spyOn(api,'request').mockResolvedValue({items:[],total:0,page:1,page_size:25,filters:{}});
 render(<MemoryRouter><ReviewHistorySettings/></MemoryRouter>);await screen.findByText('Page 1 of 1');await checkAll();
});
