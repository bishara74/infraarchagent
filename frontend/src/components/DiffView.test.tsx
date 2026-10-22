import {render,screen} from '@testing-library/react';
import {expect,it} from 'vitest';
import fixture from '../test/fixtures/repaired-results.json';
import type {PackageResult} from '../api/types';
import {DiffView} from './DiffView';
it('FR-UI-04 multi-hunk diffs retain headers line numbers and plus/minus markers',()=>{
 const original=Array.from({length:30},(_,index)=>`line ${index}`).join('\n')+'\n';const current=original.replace('line 1\n','changed one\n').replace('line 28\n','changed last\n');
 const item={...fixture.packages[0],files:{'main.tf':current},original_files:{'main.tf':original}} as PackageResult;
 const {container}=render(<DiffView item={item} path="main.tf"/>);
 expect(container.querySelectorAll('.diff-row.hunk')).toHaveLength(2);expect(container.querySelector('.remove .marker')).toHaveTextContent('-');expect(container.querySelector('.add .marker')).toHaveTextContent('+');expect(screen.getByText('changed one')).toBeVisible();expect(container.querySelectorAll('.line-number').length).toBeGreaterThan(0);
});
