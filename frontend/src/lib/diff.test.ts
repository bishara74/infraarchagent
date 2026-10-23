import {expect,it} from 'vitest';
import {presentedDiff,unifiedDiff} from './diff';

it('FR-UI-04 formatting-only hunks become labelled context with both line numbers',()=>{
 const view=presentedDiff('a=1\nb = 2\n','a = 1\n  b = 2\n',true);
 expect(view.changedLines).toBe(0);expect(view.formattingHidden).toBe(2);
 expect(view.rows[0]?.content).toBe('Formatting only (terraform fmt)');
 expect(view.rows.filter(row=>row.kind==='add'||row.kind==='remove')).toHaveLength(0);
 expect(view.rows.find(row=>row.content==='a = 1')).toMatchObject({kind:'context',oldLine:1,newLine:1});
});
it('FR-UI-04 mixed hunks keep substantive additions/removals and count formatting separately',()=>{
 const view=presentedDiff('a=1\nb=2\n',' a = 1 \nb=3\n',true);
 expect(view.changedLines).toBe(2);expect(view.formattingHidden).toBe(1);
 expect(view.rows.some(row=>row.kind==='hunk')).toBe(true);
 expect(view.rows.find(row=>row.kind==='remove')?.content).toBe('b=2');expect(view.rows.find(row=>row.kind==='add')?.content).toBe('b=3');
});
it('FR-UI-04 disabling whitespace hiding restores the exact raw diff',()=>{
 const before='a=1\n',after=' a = 1 \n';const view=presentedDiff(before,after,false);
 expect(view.rows).toEqual(unifiedDiff(before,after).rows);expect(view.changedLines).toBe(2);expect(view.formattingHidden).toBe(0);
});
it.each([
 ['x=1\r\n','x=1\n',1],['x=1','x=1\n',1],['x=1\n','\n x = 1\n',2],
])('FR-UI-04 CRLF EOF and blank-line formatting is visible as counted neutral context', (before,after,count)=>{
 const view=presentedDiff(before,after,true);expect(view.changedLines).toBe(0);expect(view.formattingHidden).toBe(count);
});
it('FR-UI-04 absent baselines and unchanged files retain their honest presentation',()=>{
 expect(presentedDiff(undefined,'a=1\n',true)).toMatchObject({baseline:false,changedLines:0,formattingHidden:0});
 expect(presentedDiff('a=1\n','a=1\n',true)).toMatchObject({baseline:true,changed:false,changedLines:0,formattingHidden:0});
});
it('FR-UI-04 separate formatting and substantive hunks preserve their own labels',()=>{
 const before=Array.from({length:30},(_,i)=>`line ${i}`).join('\n')+'\n';const after=before.replace('line 1','line    1').replace('line 28','changed 28');
 const view=presentedDiff(before,after,true);expect(view.rows.filter(row=>row.kind==='formatting')).toHaveLength(1);expect(view.rows.filter(row=>row.kind==='hunk')).toHaveLength(1);expect(view.changedLines).toBe(2);expect(view.formattingHidden).toBe(1);
});
