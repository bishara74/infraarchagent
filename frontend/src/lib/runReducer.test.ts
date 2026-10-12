import { expect, it } from 'vitest';
import recorded from '../test/fixtures/run.sse?raw';
import pending from '../test/fixtures/pending-results.json';
import { createSseParser, eventFromFrame } from '../api/sse';
import { applySnapshot, initialModel, reduceEvent, stageFor } from './runReducer';
import type { ResultsResponse, RunEvent } from '../api/types';
it('FR-P-04 every recorded event kind and deduplication',()=>{const events:RunEvent[]=[]; createSseParser(frame=>events.push(eventFromFrame(frame))).feed(recorded); expect(new Set(events.map(event=>event.kind)).size).toBe(6); let model=initialModel(); for(const event of events) model=reduceEvent(model,event); expect(model.events).toEqual(events); expect(model.runStatus).toBe('partial_success'); expect(model.packageStatuses.security).toBe('pending_review'); expect(model.paths.cost).toContain('terraform/main.tf'); expect(stageFor(model,'architect').status).toBe('completed'); expect(model.plan).toBeTruthy(); expect(reduceEvent(model,events[0]!)).toBe(model);});
it('restores snapshot and isolates fresh runs',()=>{expect(applySnapshot(initialModel(),pending as ResultsResponse).packageStatuses.security).toBe('pending_review'); expect(initialModel().events).toEqual([]);});
it('Security/Validator aggregation waits for every generated variant',()=>{const model=applySnapshot(initialModel(),pending as ResultsResponse);model.stages['security:cost']={status:'completed',seq:10,message:'Done',started:'2026-10-12T12:00:00Z',ended:'2026-10-12T12:00:01Z'};expect(stageFor(model,'security').status).toBe('pending');model.stages['security:security']={...model.stages['security:cost'],status:'running',seq:11,ended:null};expect(stageFor(model,'security').status).toBe('running');expect(stageFor(model,'security').seq).toBe(11);});
