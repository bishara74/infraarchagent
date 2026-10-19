import {render,screen,fireEvent,waitFor,act} from '@testing-library/react';
import {MemoryRouter} from 'react-router';
import {afterEach,expect,it,vi} from 'vitest';
import {ModelControls} from './ModelControls';
import {ProviderPage} from '../screens/SettingsScreen';
import {api} from '../api/client';
import type {Catalog} from '../api/types';
afterEach(()=>vi.restoreAllMocks());
const catalog:Catalog={provider:'custom',credential_id:null,defaults:{},models:[{id:'reasoning',name:'Reasoning model',context_length:8192,pricing:{prompt:'0.000001',completion:'0.000002'},structured_output:true,reasoning:true,thinking_modes:['low'],source:'admin'},{id:'unknown',name:'Unknown model',context_length:null,pricing:{},structured_output:null,reasoning:false,thinking_modes:[],source:'unknown'}]};
it('FR-UI-01 only supported modes can be selected and unsuitable models are disabled',()=>{
 render(<ModelControls catalog={catalog} value={{generators:{model:'reasoning'}}} onChange={vi.fn()}/>);
 const thinking=screen.getByLabelText('Generators thinking');expect(thinking).toHaveTextContent('low');expect(thinking).not.toHaveTextContent('high');expect(screen.getAllByRole('option',{name:/Unknown model/})[1]).toBeDisabled();expect(screen.getByText(/8,192/)).toBeVisible();
});
it('NFR-01 entering a key automatically probes and loads catalog without persistence',async()=>{
 const calls=vi.spyOn(api,'request').mockImplementation(async url=>url.endsWith('/probe')?{status:'ok',models:catalog.models}: {storage_enabled:true,default_credential_id:null,credentials:[]} as never);
 render(<MemoryRouter><ProviderPage/></MemoryRouter>);fireEvent.change(screen.getByLabelText('Provider API key'),{target:{value:'synthetic-provider-key'}});
 await waitFor(()=>expect(screen.getByRole('status')).toHaveTextContent('2 models loaded'),{timeout:3000});expect(calls.mock.calls.some(([url])=>url==='/api/providers/probe')).toBe(true);expect(JSON.stringify({...localStorage,...sessionStorage})).not.toContain('synthetic-provider-key');
});

it('FR-UI-01 obsolete probe responses cannot replace the current catalog', async () => {
 const probes: Array<{signal?: AbortSignal; resolve: (value: unknown) => void}> = [];
 vi.spyOn(api, 'request').mockImplementation((url, _method, _body, signal) => {
  if (!url.endsWith('/probe')) return Promise.resolve({storage_enabled:true,default_credential_id:null,credentials:[]}) as never;
  return new Promise(resolve => probes.push({signal, resolve})) as never;
 });
 render(<MemoryRouter><ProviderPage/></MemoryRouter>);
 const input = screen.getByLabelText('Provider API key');
 fireEvent.paste(input);fireEvent.change(input,{target:{value:'first-synthetic-key'}});
 await waitFor(()=>expect(probes).toHaveLength(1));
 fireEvent.change(input,{target:{value:'second-synthetic-key'}});
 await waitFor(()=>expect(probes).toHaveLength(2));
 const [first, second] = probes;
 if (!first || !second) throw new Error('Expected two probe requests');
 expect(first.signal?.aborted).toBe(true);
 await act(async()=>second.resolve({status:'ok',models:catalog.models}));
 expect(screen.getByRole('status')).toHaveTextContent('2 models loaded');
 // The mock deliberately ignores abort: the UI must discard its stale result.
 await act(async()=>first.resolve({status:'invalid',models:[]}));
 expect(screen.getByRole('status')).toHaveTextContent('Provider test: ok. 2 models loaded');
});
