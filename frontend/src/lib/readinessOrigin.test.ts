import { expect, it } from 'vitest';
import run from '../test/fixtures/run.sse?raw';
import retry from '../test/fixtures/retry.sse?raw';
import { createSseParser, eventFromFrame } from '../api/sse';
import type { RunEvent } from '../api/types';
import { readinessOrigin } from './readinessOrigin';

const events: RunEvent[] = [];
createSseParser(frame => events.push(eventFromFrame(frame))).feed(run + retry);
const ready = { variant: 'security', readiness_label: 'production_ready' } as const;
it('FR-UI-06/07 recorded automatic and retry origins agree with archive copy', () => {
  expect(readinessOrigin(events, { ...ready, variant: 'cost' })).toBe('automatic (clean scan and valid validation)');
  expect(readinessOrigin(events, ready)).toBe('automatic after an engineer-requested retry (clean scan and valid validation)');
  expect(readinessOrigin(events.filter(event => event.payload.review_action !== 'retry'), ready)).toBe('automatic (clean scan and valid validation)');
});
it.each(['approve', 'reject'])('FR-UI-07 %s decision takes precedence over prior retries', action => {
  const label = events.at(-1)!;
  expect(readinessOrigin([...events.slice(0, -1), { ...label, payload: { ...label.payload, review_action: action } }], ready)).toBe('engineer decision');
});
it('missing transition is unavailable; other variants and later retries cannot change origin', () => {
  expect(readinessOrigin([], ready)).toBe('unavailable (transition event not recorded)');
  expect(readinessOrigin(events, { ...ready, readiness_label: null })).toBeNull();
  const label = events.at(-1)!;
  const start = events.find(event => event.payload.review_action === 'retry')!;
  expect(readinessOrigin([{ ...start, variant: 'cost' }, label, { ...start, seq: label.seq + 1 }], ready)).toBe('automatic (clean scan and valid validation)');
});
