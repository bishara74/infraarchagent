import {fireEvent,render,screen} from '@testing-library/react';
import {expect,it,vi} from 'vitest';
import type {Catalog,CatalogModel} from '../api/types';
import {ModelControls} from './ModelControls';
const model=(id:string,structured_output:boolean|null=true):CatalogModel=>({id,name:id,structured_output,pricing:{prompt:0.000001,completion:0.000002},context_length:65536,reasoning:false,thinking_modes:[],source:'provider'});
it('FR-UI-01 every role defaults to tested recommendations and toggle reveals only compatible models',()=>{
 const catalog:Catalog={provider:'openrouter',credential_id:'c',defaults:{},models:[model('openai/gpt-oss-120b:nitro'),model('other/compatible'),model('other/free:free'),model('bad',false),model('unknown',null)]};
 render(<ModelControls catalog={catalog} value={{}} onChange={vi.fn()}/>);
 for(const role of ['Architect','Generators','Fixer']){
  const input=screen.getByRole('combobox',{name:`${role} model`});fireEvent.click(input);
  expect(screen.getByRole('option',{name:/openai\/gpt-oss-120b:nitro/})).toHaveTextContent('tested');
  expect(screen.queryByRole('option',{name:/other\/compatible/})).toBeNull();
  expect(screen.getByRole('option',{name:/openai\/gpt-oss-120b:nitro/})).toHaveTextContent('65,536');fireEvent.keyDown(input,{key:'Escape'});
 }
 fireEvent.click(screen.getByRole('checkbox',{name:'Show all compatible models'}));
 fireEvent.click(screen.getByRole('combobox',{name:'Architect model'}));
 expect(screen.getByRole('option',{name:/other\/compatible/})).toBeVisible();
 expect(screen.queryByRole('option',{name:/other\/free|unknown|bad/})).toBeNull();
});

it('FR-UI-01 routing default uses base metadata and effective server effort',()=>{
 const catalog:Catalog={provider:'openrouter',credential_id:null,defaults:{},environment_defaults:Object.fromEntries(['architect','generator_cost','generator_performance','generator_security','fixer'].map(role=>[role,{provider:'openai' as const,model:'openai/gpt-oss-120b:nitro',thinking_mode:'low' as const}])),models:[{...model('openai/gpt-oss-120b'),reasoning:true,thinking_modes:['low','high']}]};
 render(<ModelControls catalog={catalog} value={{}} onChange={vi.fn()}/>);
 expect(screen.getByLabelText('Architect thinking')).toHaveDisplayValue('low (server default)');
 expect(screen.queryByText(/We couldn't load details/)).toBeNull();
 fireEvent.click(screen.getByRole('combobox',{name:'Architect model'}));expect(screen.getByRole('option',{name:/gpt-oss-120b:nitro.*tested/})).toHaveTextContent('65,536');
});
it('FR-UI-01 missing details only show after loading and retry is actionable',()=>{
 const retry=vi.fn();const props={catalog:null,value:{},onChange:vi.fn(),retry};
 const view=render(<ModelControls {...props} loaded={false}/>);expect(screen.queryByText(/We couldn't load details/)).toBeNull();
 view.rerender(<ModelControls {...props} loaded/>);expect(screen.getAllByText("We couldn't load details for this model. It will still run with the server's settings.")).toHaveLength(6);
 fireEvent.click(screen.getAllByRole('button',{name:'Retry'})[0]!);expect(retry).toHaveBeenCalledOnce();
});
