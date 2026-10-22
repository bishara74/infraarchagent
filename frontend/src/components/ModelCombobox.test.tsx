import {fireEvent,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {expect,it,vi} from 'vitest';
import {ModelCombobox} from './ModelCombobox';
import {ModelControls} from './ModelControls';
import type {Catalog} from '../api/types';
const options=[{value:'',label:'Use default — effective · low',detail:'Inherited'},{value:'alpha/id',label:'Alpha Name',detail:'structured output · reasoning · $1'},{value:'bad',label:'Invalid JSON model',detail:'unknown',disabled:true,explanation:'Choose a structured output model.'},{value:'beta/id',label:'Beta Name',detail:'structured output · no reasoning'}];
it('FR-UI-01 combobox filters by ID/name ignoring case and explains disabled choices',async()=>{
 const changed=vi.fn();render(<ModelCombobox label="Architect model" value="" options={options} onChange={changed}/>);
 const input=screen.getByRole('combobox');await userEvent.click(input);await userEvent.type(input,'ALPHA');expect(screen.getByRole('option',{name:/Alpha Name/})).toBeVisible();expect(screen.queryByRole('option',{name:/Beta/})).toBeNull();
 fireEvent.change(input,{target:{value:'beta/ID'}});expect(screen.getByRole('option',{name:/Beta/})).toBeVisible();
 fireEvent.change(input,{target:{value:''}});const invalid=screen.getByRole('option',{name:/Invalid/});expect(invalid).toHaveAttribute('aria-disabled','true');await userEvent.click(invalid);expect(changed).not.toHaveBeenCalled();
 fireEvent.change(input,{target:{value:'missing'}});expect(screen.getByText(/No matching models/)).toBeVisible();
});
it('FR-UI-01 combobox supports arrows Enter Escape and skips disabled options',()=>{
 const changed=vi.fn();render(<ModelCombobox label="Model" value="" options={options} onChange={changed}/>);const input=screen.getByRole('combobox');
 fireEvent.keyDown(input,{key:'ArrowDown'});fireEvent.keyDown(input,{key:'ArrowDown'});fireEvent.keyDown(input,{key:'ArrowDown'});fireEvent.keyDown(input,{key:'Enter'});expect(changed).toHaveBeenCalledWith('beta/id');
 fireEvent.keyDown(input,{key:'ArrowUp'});expect(input).toHaveAttribute('aria-expanded','true');fireEvent.keyDown(input,{key:'Escape'});expect(input).toHaveAttribute('aria-expanded','false');
});
it('FR-UI-01 default reasoning remains editable and materialises the effective model',()=>{
 const onChange=vi.fn();const catalog:Catalog={provider:'custom',credential_id:null,defaults:{architect:{model:'alpha',thinking_mode:'low'}},models:[{id:'alpha',name:'Alpha',context_length:8000,structured_output:true,reasoning:true,thinking_modes:['low','high'],pricing:{},source:'admin'}]};
 render(<ModelControls catalog={catalog} defaults={catalog.defaults} value={{}} onChange={onChange}/>);
 expect(screen.getByRole('combobox',{name:'Architect model'})).toHaveValue('Use default — alpha · low');
 fireEvent.change(screen.getByLabelText('Architect thinking'),{target:{value:'high'}});expect(onChange).toHaveBeenCalledWith({architect:{model:'alpha',thinking_mode:'high'}});
});

it('FR-UI-01 large catalogues stay bounded while keyboard End and ID search reach every model',()=>{
 const changed=vi.fn();const many=Array.from({length:300},(_,index)=>({value:`model/${index}`,label:`Model ${index}`,detail:'structured output · reasoning · $1 / million tokens'}));
 render(<ModelCombobox label="Large model catalogue" value="model/0" options={many} onChange={changed}/>);const input=screen.getByRole('combobox');fireEvent.focus(input);
 expect(screen.getAllByRole('option').length).toBeLessThanOrEqual(16);fireEvent.keyDown(input,{key:'End'});expect(screen.getByRole('option',{name:/Model 299/})).toHaveAttribute('aria-posinset','300');fireEvent.keyDown(input,{key:'Enter'});expect(changed).toHaveBeenCalledWith('model/299');
 fireEvent.change(input,{target:{value:'model/155'}});expect(screen.getAllByRole('option')).toHaveLength(1);expect(screen.getByRole('option',{name:/Model 155/})).toBeVisible();
});

it('FR-UI-01 invalid inherited structured-output defaults explain the affected fields',()=>{
 const catalog:Catalog={provider:'custom',credential_id:null,defaults:{generators:{model:'bad'},fixer:{model:'bad'}},models:[{id:'bad',name:'Unsupported',context_length:null,pricing:{},structured_output:false,reasoning:false,thinking_modes:[],source:'admin'}]};
 render(<ModelControls catalog={catalog} defaults={catalog.defaults} value={{}} onChange={vi.fn()}/>);
 expect(screen.getByRole('combobox',{name:'Generators model'})).toHaveAttribute('aria-invalid','true');expect(screen.getByRole('combobox',{name:'Fixer model'})).toHaveAttribute('aria-invalid','true');expect(screen.getAllByText(/This model can't return the structured JSON/).length).toBeGreaterThanOrEqual(2);fireEvent.click(screen.getByRole('combobox',{name:'Generators model'}));expect(screen.getByRole('option',{name:/Use default/})).toHaveAttribute('aria-disabled','true');
});
