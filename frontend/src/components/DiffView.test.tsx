import {fireEvent,render,screen} from '@testing-library/react';
import {expect,it} from 'vitest';
import fixture from '../test/fixtures/repaired-results.json';
import type {PackageResult} from '../api/types';
import {DiffView} from './DiffView';
import {getPreferences,retrySave,hydratePreferences} from '../lib/preferences';
it('FR-UI-04 multi-hunk diffs retain headers line numbers and plus/minus markers',()=>{
 const original=Array.from({length:30},(_,index)=>`line ${index}`).join('\n')+'\n';const current=original.replace('line 1\n','changed one\n').replace('line 28\n','changed last\n');
 const item={...fixture.packages[0],files:{'main.tf':current},original_files:{'main.tf':original}} as PackageResult;
 const {container}=render(<DiffView item={item} path="main.tf"/>);
 expect(container.querySelectorAll('.diff-row.hunk')).toHaveLength(2);expect(container.querySelector('.remove .marker')).toHaveTextContent('-');expect(container.querySelector('.add .marker')).toHaveTextContent('+');expect(screen.getByText('changed one')).toBeVisible();expect(container.querySelectorAll('.line-number').length).toBeGreaterThan(0);
});

it('FR-UI-04 whitespace toggle and counts persist through account cache without changing package text',async()=>{
 const item={...fixture.packages[0],files:{'main.tf':'  a = 1\n'},original_files:{'main.tf':'a=1\n'}} as PackageResult;
 const original=JSON.stringify(item);const root=render(<DiffView item={item} path="main.tf"/>);
 expect(screen.getByRole('checkbox',{name:'Hide whitespace-only changes'})).toBeChecked();
 expect(screen.getByText('Formatting only (terraform fmt)')).toBeVisible();expect(screen.getByRole('status')).toHaveTextContent('0 changed lines · 1 formatting-only lines hidden');
 fireEvent.click(screen.getByRole('checkbox'));expect(screen.getByRole('status')).toHaveTextContent('2 changed lines · 0 formatting-only lines hidden');
 expect(document.querySelector('.diff-row.add')).not.toBeNull();await retrySave();root.unmount();await hydratePreferences(null);
 render(<DiffView item={item} path="main.tf"/>);expect(screen.getByRole('checkbox')).not.toBeChecked();expect(getPreferences().data.ui.hide_whitespace_only_changes).toBe(false);expect(JSON.stringify(item)).toBe(original);
});
