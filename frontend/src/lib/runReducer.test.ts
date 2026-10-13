import { expect, it } from 'vitest';
import recorded from '../test/fixtures/run.sse?raw';
import pending from '../test/fixtures/pending-results.json';
import { createSseParser, eventFromFrame } from '../api/sse';
import { applySnapshot, initialModel, reduceEvent, stageFor } from './runReducer';
import type { ResultsResponse, RunEvent } from '../api/types';
it('FR-P-04 every recorded event kind and deduplication',()=>{const events:RunEvent[]=[]; createSseParser(frame=>events.push(eventFromFrame(frame))).feed(recorded); expect(new Set(events.map(event=>event.kind)).size).toBe(6); let model=initialModel(); for(const event of events) model=reduceEvent(model,event); expect(model.events).toEqual(events); expect(model.runStatus).toBe('partial_success'); expect(model.packageStatuses.security).toBe('pending_review'); expect(model.paths.cost).toContain('terraform/main.tf'); expect(stageFor(model,'architect').status).toBe('completed'); expect(model.plan).toBeTruthy(); expect(reduceEvent(model,events[0]!)).toBe(model);});
it('restores snapshot and isolates fresh runs',()=>{expect(applySnapshot(initialModel(),pending as ResultsResponse).packageStatuses.security).toBe('pending_review'); expect(initialModel().events).toEqual([]);});
it('Security/Validator aggregation waits for every generated variant',()=>{const model=applySnapshot(initialModel(),pending as ResultsResponse);model.stages['security:cost']={status:'completed',seq:10,message:'Done',started:'2026-10-12T12:00:00Z',ended:'2026-10-12T12:00:01Z'};expect(stageFor(model,'security').status).toBe('pending');model.stages['security:security']={...model.stages['security:cost'],status:'running',seq:11,ended:null};expect(stageFor(model,'security').status).toBe('running');expect(stageFor(model,'security').seq).toBe(11);});

it('FR-UI-02 counts the union of real active intervals across variants and retries', async()=>{
 const {stageElapsed}=await import('./runReducer');
 const at=(seconds:number)=>new Date(Date.parse('2026-10-12T12:00:00Z')+seconds*1000).toISOString();
 let model=initialModel();
 model.packageStatuses={cost:'production_ready',security:'pending_review'};
 const frames:[number,'cost'|'security','running'|'completed'][]=[[0,'cost','running'],[2,'security','running'],[4,'cost','completed'],[6,'security','completed'],[20,'security','running']];
 for(const [index,[seconds,variant,status]] of frames.entries()) model=reduceEvent(model,{seq:index+1,kind:'agent_state',agent:'security',variant,status,previous_status:null,message:null,timestamp:at(seconds),payload:{}});
 expect(stageElapsed(stageFor(model,'security'),Date.parse(at(23)))).toBe('9s');
 model=reduceEvent(model,{seq:6,kind:'agent_state',agent:'security',variant:'security',status:'completed',previous_status:'running',message:null,timestamp:at(24),payload:{}});
 model=reduceEvent(model,{seq:7,kind:'stage_notice',agent:'security',variant:'security',status:'completed',previous_status:null,message:'Report retained',timestamp:at(30),payload:{}});
 expect(stageElapsed(stageFor(model,'security'),Date.parse(at(50)))).toBe('10s');
});
it('FR-UI-02 elapsed time uses timestamps and distinguishes queued from zero duration', async()=>{
 const {stageElapsed,blankStage}=await import('./runReducer');
 expect(stageElapsed(blankStage(),1000)).toBe('—');
 const start='2026-10-12T12:00:00Z';
 expect(stageElapsed({status:'running',seq:1,message:null,started:start,ended:null},Date.parse(start)+1999)).toBe('1s');
});

it.each([
 ['validator',['invalid','valid','valid'],'2 valid · 1 invalid'],
 ['validator',['validation_error','invalid','valid'],'1 valid · 1 invalid · 1 error'],
 ['security',['scan_exhausted','scan_clean','scan_clean'],'2 clean · 1 exhausted'],
 ['security',['scan_error','scan_exhausted','scan_clean'],'1 clean · 1 exhausted · 1 error'],
] as const)('FR-UI-02 %s summary retains mixed outcomes when the last variant succeeds', (agent,outcomes,summary)=>{
 let model=initialModel();let seq=0;
 for(const [index,variant] of (['security','cost','performance'] as const).entries()){
  const event={seq:++seq,kind:'agent_state' as const,agent,variant,status:'running',previous_status:null,message:'Started',timestamp:'2026-10-13T12:00:00Z',payload:{}};
  model=reduceEvent(model,event);
  model=reduceEvent(model,{...event,seq:++seq,kind:'package_status',agent:'orchestrator',status:outcomes[index]!,message:'Outcome'});
  model=reduceEvent(model,{...event,seq:++seq,status:outcomes[index]!.includes('error')?'failed':'completed',message:'Last variant finished'});
 }
 expect(stageFor(model,agent).message).toBe(summary);
 if(agent==='validator'){
  const event={seq:++seq,kind:'agent_state' as const,agent,variant:'security' as const,status:'running',previous_status:'completed',message:'Retry',timestamp:'2026-10-13T12:00:01Z',payload:{}};
  model=reduceEvent(model,event);
  expect(stageFor(model,agent).message).toBe(summary.startsWith('2')?'2 valid':'1 valid · 1 invalid');
  model=reduceEvent(model,{...event,seq:++seq,kind:'package_status',status:'valid'});
  model=reduceEvent(model,{...event,seq:seq+1,status:'completed'});
  expect(stageFor(model,agent).message).toBe(summary.startsWith('2')?'3 valid':'2 valid · 1 invalid');
 }
});
