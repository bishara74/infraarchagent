import {act,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router';
import {expect,it,vi} from 'vitest';
import {api} from '../api/client';
import {CatalogNotice} from '../components/CatalogNotice';
import {useModelCatalog} from './useModelCatalog';
import {setSessionStatus} from '../lib/sessionState';

function View(){const state=useModelCatalog();return <MemoryRouter><CatalogNotice {...state}/><span>{state.catalog?.provider}</span></MemoryRouter>;}
it.each([
 ['setup_required',undefined,'No provider selected'],
 ['invalid',undefined,'credential is invalid'],
 ['no_credit',undefined,'has no credit'],
 ['unavailable','network_error','Network error'],
 ['unavailable',undefined,'catalogue is unavailable'],
 ['ok',undefined,'returned no models'],
])('FR-UI-01 catalogue %s explains recovery and retries past the cache',async(status,error_code,message)=>{
 const request=vi.spyOn(api,'request').mockResolvedValue({status,error_code,models:[],provider:'custom',defaults:{},credential_id:'c'});
 render(<View/>);expect(screen.getByText('Loading model catalogue…')).toBeVisible();
 await screen.findByText(new RegExp(message));fireEvent.click(screen.getByRole('button',{name:'Retry'}));
 await waitFor(()=>expect(request.mock.calls.some(([url])=>url==='/api/models?refresh=true')).toBe(true));
});
it('FR-UI-01 obsolete account results are ignored',async()=>{
 const pending:Array<(value:unknown)=>void>=[];
 vi.spyOn(api,'request').mockImplementation(()=>new Promise(resolve=>pending.push(resolve)) as never);
 setSessionStatus({authenticated:true,auth_required:true,mode:'account',user:{id:'one',username:'one',role:'reviewer'}});
 render(<View/>);
 act(()=>setSessionStatus({authenticated:true,auth_required:true,mode:'account',user:{id:'two',username:'two',role:'reviewer'}}));
 await act(async()=>pending[1]!({provider:'current',models:[],defaults:{},credential_id:null}));
 await act(async()=>pending[0]!({provider:'stale',models:[],defaults:{},credential_id:null}));
 expect(screen.getByText('current')).toBeVisible();expect(screen.queryByText('stale')).toBeNull();
});
it('FR-UI-01 rejected catalogue requests expose a safe retry and recover',async()=>{
 const request=vi.spyOn(api,'request').mockRejectedValueOnce(new Error('not-public-provider-details'));
 render(<View/>);await screen.findByText(/Unable to load model catalogue/);
 expect(screen.queryByText(/not-public-provider-details/)).toBeNull();
 request.mockResolvedValue({provider:'stub',models:[{id:'stub'}],defaults:{},credential_id:null});
 fireEvent.click(screen.getByRole('button',{name:'Retry'}));await screen.findByText('stub');
 expect(screen.queryByRole('button',{name:'Retry'})).toBeNull();
});
