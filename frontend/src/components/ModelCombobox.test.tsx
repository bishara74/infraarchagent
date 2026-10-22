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
