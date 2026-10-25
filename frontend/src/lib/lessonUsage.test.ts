import {expect,it} from 'vitest';
import type {RunEvent} from '../api/types';
import {manifest,lesson} from '../test/fixtures/lessons';
import {lessonUsage} from './lessonUsage';

function event(payload:RunEvent['payload']){return {seq:1,kind:'stage_notice',agent:'orchestrator',status:'running',previous_status:null,message:null,variant:null,timestamp:'2026-10-25T12:00:00Z',payload} as RunEvent;}
it('FR-P-04 combines backend and live authorized use without double counting',()=>{
  const use={enabled:true,set_version:1,set_hash:manifest.set_hash,lesson_ids:[lesson.id],self_approved:false};
  const result=lessonUsage(manifest,[event({notice:'lesson use',lessons:use})]);
  expect(result.count).toBe(1);expect(result.version).toBe(1);
});
it('FR-P-04 displays live use before a results refresh and preserves sticky disabling',()=>{
  const result=lessonUsage(undefined,[event({notice:'lesson use',lessons:{enabled:true,set_version:3,set_hash:manifest.set_hash,lesson_ids:[lesson.id],self_approved:true}}),event({notice:'runtime telemetry',telemetry:[{lesson_usage:{enabled:false,lesson_ids:[],reason:'disabled_during_run'}}]})]);
  expect(result).toMatchObject({count:1,version:3,selfApproved:true,disabled:true});
});
it('NFR-01 ignores malformed/unrelated stream data',()=>{
  expect(lessonUsage(undefined,[event({notice:'lesson use',lessons:'invalid'}),event({notice:'lesson use',lessons:{enabled:true,lesson_ids:'bad'}})])).toMatchObject({count:0,selfApproved:false});
});
