import type { AgentState, ResultsResponse, RunEvent, RunStatus, Variant } from '../api/types';

export interface StageItem {
  status: AgentState; seq: number; message: string | null;
  started: string | null; ended: string | null;
}
export interface RunModel {
  runStatus: RunStatus; plan: unknown; stages: Record<string, StageItem>;
  packageStatuses: Partial<Record<Variant, string>>; paths: Partial<Record<Variant, string[]>>;
  events: RunEvent[];
}
export const blankStage = (): StageItem => ({ status: 'pending', seq: 0, message: null, started: null, ended: null });
export const initialModel = (): RunModel => ({ runStatus: 'created', plan: null, stages: {}, packageStatuses: {}, paths: {}, events: [] });
export function reduceEvent(model: RunModel, event: RunEvent): RunModel {
  if (event.seq <= (model.events.at(-1)?.seq ?? 0)) return model;
  const next = { ...model, events: [...model.events, event] };
  if (event.kind === 'run_status') next.runStatus = event.status as RunStatus;
  if (event.kind === 'plan_created') next.plan = event.payload.plan;
  if (event.kind === 'package_status' && event.variant) next.packageStatuses = { ...model.packageStatuses, [event.variant]: event.status };
  if (event.kind === 'package_generated' && event.variant) next.paths = { ...model.paths, [event.variant]: Array.isArray(event.payload.paths) ? event.payload.paths as string[] : [] };
  if (event.kind === 'agent_state' || event.kind === 'stage_notice') {
    const key = event.agent + (event.variant ? `:${event.variant}` : '');
    const previous = model.stages[key] ?? blankStage();
    const status = event.kind === 'agent_state' ? event.status as AgentState : previous.status;
    next.stages = { ...model.stages, [key]: {
      ...previous, status, seq: event.seq, message: event.message,
      started: status === 'running' && previous.status !== 'running' ? event.timestamp : previous.started,
      ended: status === 'completed' || status === 'failed' ? event.timestamp : null,
    } };
  }
  return next;
}
export function stageFor(model: RunModel, agent: string): StageItem {
  const keys = agent === 'security' || agent === 'validator'
    ? Object.keys(model.packageStatuses).filter(variant => model.packageStatuses[variant as Variant] !== 'failed').map(variant => `${agent}:${variant}`)
    : agent === 'generators' ? ['generator_cost:cost', 'generator_performance:performance', 'generator_security:security'] : [];
  const items = keys.length ? keys.map(key => model.stages[key] ?? blankStage())
    : Object.entries(model.stages).filter(([key]) => key === agent || key.startsWith(`${agent}:`)).map(([, item]) => item);
  if (!items.length) return blankStage();
  const latest = items.reduce((a, b) => a.seq > b.seq ? a : b);
  const status = items.some(item => item.status === 'running') ? 'running'
    : items.some(item => item.status === 'failed') ? 'failed'
    : items.every(item => item.status === 'completed') ? 'completed' : 'pending';
  const starts = items.flatMap(item => item.started ? [item.started] : []).sort();
  const ends = items.flatMap(item => item.ended ? [item.ended] : []).sort();
  return { ...latest, status, started: starts[0] ?? null, ended: status === 'running' ? null : ends.at(-1) ?? null };
}
export function applySnapshot(model: RunModel, results: ResultsResponse): RunModel {
  return { ...model, runStatus: results.run.status, plan: results.plan,
    packageStatuses: Object.fromEntries(results.packages.map(item => [item.variant, item.status])) };
}
