import {render,screen,fireEvent,waitFor,act} from '@testing-library/react';
import {MemoryRouter} from 'react-router';
import {afterEach,expect,it,vi} from 'vitest';
import {ModelControls} from './ModelControls';
import {ProviderPage} from '../screens/SettingsScreen';
import {api} from '../api/client';
import type {Catalog} from '../api/types';
afterEach(()=>vi.restoreAllMocks());
const catalog:Catalog={provider:'custom',credential_id:null,defaults:{},models:[{id:'reasoning',name:'Reasoning model',context_length:8192,pricing:{prompt:'0.000001',completion:'0.000002'},structured_output:true,reasoning:true,thinking_modes:['low'],source:'admin'},{id:'unknown',name:'Unknown model',context_length:null,pricing:{},structured_output:null,reasoning:false,thinking_modes:[],source:'unknown'}]};
it('FR-UI-01 only supported modes can be selected and incompatible models are absent',()=>{
 render(<ModelControls catalog={catalog} value={{generators:{model:'reasoning'}}} onChange={vi.fn()}/>);
 const thinking=screen.getByLabelText('Generators thinking');expect(thinking).toHaveTextContent('low');expect(thinking).not.toHaveTextContent('high');fireEvent.click(screen.getByRole('checkbox',{name:'Show all compatible models'}));fireEvent.click(screen.getByRole('combobox',{name:'Generators model'}));expect(screen.queryByRole('option',{name:/Unknown model/})).toBeNull();expect(screen.getAllByText(/8,192/).length).toBeGreaterThan(0);
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
 expect(screen.getByRole('status')).toHaveTextContent('Provider test: ok — valid. 2 models loaded');
});

it('FR-UI-01 changing provider during a probe clears loading and ignores its completion', async () => {
 let finish!:(value:unknown)=>void;
 vi.spyOn(api,'request').mockImplementation(url=>url.endsWith('/probe')?new Promise(resolve=>{finish=resolve;}) as never:Promise.resolve({storage_enabled:true,credentials:[],default_credential_id:null}) as never);
 render(<MemoryRouter><ProviderPage/></MemoryRouter>);
 fireEvent.paste(screen.getByLabelText('Provider API key'));
 fireEvent.change(screen.getByLabelText('Provider API key'),{target:{value:'synthetic-pending-key'}});
 await waitFor(()=>expect(screen.getByRole('status')).toHaveTextContent('Testing or saving…'));
 fireEvent.change(screen.getByRole('combobox'),{target:{value:'openai'}});
 expect(screen.getByRole('status')).toHaveTextContent('Enter a key to test it');
 expect(screen.getByRole('button',{name:'Save and use provider'})).toBeDisabled();
 await act(async()=>finish({status:'ok',models:catalog.models}));
 expect(screen.getByRole('status')).not.toHaveTextContent('valid');
 expect(screen.getByLabelText('Provider API key')).toHaveValue('');
});

import {useState} from 'react';
import type {AgentChoice} from '../api/types';
const roleCatalog:Catalog={...catalog,provider:'openrouter',credential_id:'saved',defaults:{},resolution_context:{provider:'openai',model:'openai/gpt-oss-120b:nitro',thinking_mode:'low',fixer_provider:null,fixer_model:null,fixer_thinking_mode:null},models:[...['openai/gpt-oss-120b','anthropic/claude-opus-4.5'].map(id=>({...catalog.models[0]!,id,name:id,thinking_modes:['low','high'] as ['low','high']}))]};
it('FR-UI-01 FR-P-04 changing Architect leaves Generator/Fixer defaults and edits independent',()=>{
 const changed=vi.fn();
 function Harness(){const [value,setValue]=useState<Record<string,AgentChoice>>({});return <ModelControls catalog={roleCatalog} value={value} onChange={next=>{changed(next);setValue(next);}}/>;}
 render(<Harness/>);
 const generators=screen.getByRole('combobox',{name:'Generators model'});
 const fixer=screen.getByRole('combobox',{name:'Fixer model'});
 const before=[(generators as HTMLInputElement).value,(fixer as HTMLInputElement).value];
 fireEvent.click(screen.getByRole('checkbox',{name:'Show all compatible models'}));
 const architect=screen.getByRole('combobox',{name:'Architect model'});fireEvent.click(architect);fireEvent.click(screen.getByRole('option',{name:/anthropic\/claude-opus-4.5/}));
 expect(changed).toHaveBeenLastCalledWith({architect:{model:'anthropic/claude-opus-4.5'}});
 expect(generators).toHaveValue(before[0]);expect(fixer).toHaveValue(before[1]);
 expect(screen.getByLabelText('Generators thinking')).toHaveDisplayValue('low (server default)');
 expect(screen.getByText('Architect: from this run')).toBeVisible();
 fireEvent.change(screen.getByLabelText('Generators thinking'),{target:{value:'high'}});
 expect(changed).toHaveBeenLastCalledWith({architect:{model:'anthropic/claude-opus-4.5'},generators:{model:'openai/gpt-oss-120b:nitro',thinking_mode:'high'}});
 fireEvent.click(architect);fireEvent.click(screen.getByRole('option',{name:/Use default/}));
 expect(changed).toHaveBeenLastCalledWith({generators:{model:'openai/gpt-oss-120b:nitro',thinking_mode:'high'}});
 expect(screen.getByText('Architect: server default')).toBeVisible();
});

it('FR-UI-01 per-variant provenance distinguishes identical values from different tiers',()=>{
 const choice={model:'openai/gpt-oss-120b:nitro',thinking_mode:'low' as const};
 render(<ModelControls catalog={roleCatalog} value={{architect:choice}} personalDefaults={{generator_cost:choice}} defaults={{generators:choice}} onChange={vi.fn()}/>);
 expect(screen.getByText('Architect: from this run')).toBeVisible();
 expect(screen.getByText('Fixer: server default')).toBeVisible();
 expect((screen.getByRole('combobox',{name:'Generators model'}) as HTMLInputElement).value).toContain('cost: openai/gpt-oss-120b:nitro · low (from your defaults)');
 expect((screen.getByRole('combobox',{name:'Generators model'}) as HTMLInputElement).value).toContain('performance: openai/gpt-oss-120b:nitro · low (from administrator defaults)');
 expect(screen.getByLabelText('Generators thinking')).toBeEnabled();
});

it.each(['personal','admin'] as const)('FR-UI-01 Settings %s preview reports the editing tier',tier=>{
 render(<ModelControls catalog={roleCatalog} tier={tier} value={{generators:{model:'anthropic/claude-opus-4.5',thinking_mode:null}}} defaults={{generator_cost:{model:'openai/gpt-oss-120b:nitro',thinking_mode:'low'}}} onChange={vi.fn()}/>);
 expect(screen.getByText(`Generators: from ${tier==='personal'?'your':'administrator'} defaults`)).toBeVisible();
 const source=tier==='personal'?'your':'administrator';
 expect(screen.getByRole('combobox',{name:'Cost Generator model',hidden:true})).toHaveValue(`Use default — anthropic/claude-opus-4.5 · provider default (from ${source} defaults)`);
});
