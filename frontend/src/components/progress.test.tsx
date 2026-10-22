import {fireEvent,render,screen} from '@testing-library/react';
import {expect,it} from 'vitest';
import {StageCard} from './StageCard';
import {LiveLog} from './LiveLog';
import {WindowedRows} from './WindowedRows';
import {blankStage} from '../lib/runReducer';
import type {RunEvent} from '../api/types';
it('FR-UI-02 stage cards keep timing event sequence and expandable variants',()=>{
 const {container}=render(<StageCard id="generators" name="GeneratorAgents" stage={{...blankStage(),status:'completed',seq:12,started:'2026-10-22T10:00:00Z',ended:'2026-10-22T10:00:03Z'}}>Cost variant</StageCard>);
 expect(screen.getByTestId('stage-generators')).toHaveAttribute('data-seq','12');expect(screen.getByText('3s')).toBeVisible();expect(container.querySelector('.codicon-check')).not.toBeNull();
 fireEvent.click(screen.getByText('Generator variants'));expect(screen.getByText('Cost variant')).not.toBeVisible();
});
it('FR-UI-02 live log escapes messages and uses a text-flow cursor only while live',()=>{
 const event:RunEvent={seq:1,kind:'agent_state',agent:'architect',status:'failed',previous_status:null,message:'<script>failure</script>',variant:null,timestamp:'2026-10-22T10:00:00Z',payload:{}};
 const {container,rerender}=render(<LiveLog events={[event]}/>);expect(screen.getByText('[ERROR]')).toBeVisible();expect(container.querySelector('script')).toBeNull();expect(container.querySelector('.log-cursor')).toHaveTextContent('█');
 rerender(<LiveLog events={[event]} live={false}/>);expect(container.querySelector('.log-cursor')).toBeNull();
});
it('PR-02 auto-follow pauses above the bottom and resumes when pinned',()=>{
 const row=(index:number)=><div key={index}>Row {index}</div>;
 const {rerender}=render(<WindowedRows count={100} follow label="Log" row={row}/>);const region=screen.getByRole('region',{name:'Log'});
 Object.defineProperty(region,'scrollHeight',{value:2400,configurable:true});Object.defineProperty(region,'clientHeight',{value:240,configurable:true});
 fireEvent.scroll(region,{target:{scrollTop:120}});rerender(<WindowedRows count={101} follow label="Log" row={row}/>);expect(region.scrollTop).toBe(120);
 fireEvent.scroll(region,{target:{scrollTop:2160}});rerender(<WindowedRows count={102} follow label="Log" row={row}/>);expect(region.scrollTop).toBe(2400);
});
