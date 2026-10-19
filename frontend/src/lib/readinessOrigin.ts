import type { PackageResult, RunEvent } from '../api/types';

/** Match archive provenance using recorded transitions, never package heuristics. */
export function readinessOrigin(events: RunEvent[], item: Pick<PackageResult, 'variant' | 'readiness_label'>): string | null {
  if (!item.readiness_label || item.readiness_label==='pending_review') return null;
  const label = events.findLast(event => event.kind === 'package_status' && event.variant === item.variant && event.status === item.readiness_label);
  if (!label) return 'unavailable (transition event not recorded)';
  const decision=label.payload.review_decision;
  if(decision&&typeof decision==='object'&&'identity_basis' in decision&&decision.identity_basis==='synthetic benchmark fixture')return 'synthetic benchmark fixture (no engineer decision or executed checks)';
  if (['approve', 'reject'].includes(String(label.payload.review_action))) return 'engineer decision';
  const retried = events.some(event => event.seq < label.seq && event.kind === 'package_status' && event.variant === item.variant && event.payload.review_action === 'retry');
  return retried ? 'automatic after an engineer-requested retry (clean scan and valid validation)' : 'automatic (clean scan and valid validation)';
}
