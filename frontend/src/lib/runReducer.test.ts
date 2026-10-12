import { expect, it } from 'vitest';
import recorded from '../test/fixtures/run.sse?raw';
import pending from '../test/fixtures/pending-results.json';
import { createSseParser, eventFromFrame } from '../api/sse';
import { applySnapshot, initialModel, reduceEvent, stageFor } from './runReducer';
import type { ResultsResponse, RunEvent } from '../api/types';
it('FR-P-04 every recorded event kind and deduplication',()=>{const events:RunEvent[]=[]; createSseParser(frame=>events.push(eventFromFrame(frame))).feed(recorded); expect(new Set(events.map(event=>event.kind)).size).toBe(6); let model=initialModel(); for(const event of events) model=reduceEvent(model,event); expect(model.events).toEqual(events); expect(model.runStatus).toBe('partial_success'); expect(model.packageStatuses.security).toBe('pending_review'); expect(model.paths.cost).toContain('terraform/main.tf'); expect(stageFor(model,'architect').status).toBe('completed'); expect(model.plan).toBeTruthy(); expect(reduceEvent(model,events[0]!)).toBe(model);});
it('restores snapshot and isolates fresh runs',()=>{expect(applySnapshot(initialModel(),pending as ResultsResponse).packageStatuses.security).toBe('pending_review'); expect(initialModel().events).toEqual([]);});
