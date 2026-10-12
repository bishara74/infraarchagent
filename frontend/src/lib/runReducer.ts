import type { AgentState, ResultsResponse, RunEvent, RunStatus, Variant } from '../api/types';

export interface StageItem {
  status: AgentState; seq: number; message: string | null;
  started: string | null; ended: string | null;
  periods?: { started: string; ended: string | null }[];
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
    let periods = previous.periods ?? [];
    if (event.kind === 'agent_state') {
      if (status === 'running' && previous.status !== 'running') periods = [...periods, { started: event.timestamp, ended: null }];
      else if ((status === 'completed' || status === 'failed') && periods.at(-1)?.ended === null) periods = periods.map((period, index) => index === periods.length - 1 ? { ...period, ended: event.timestamp } : period);
    }
    next.stages = { ...model.stages, [key]: {
      ...previous, status, seq: event.seq, message: event.message, periods,
      started: status === 'running' && previous.status !== 'running' ? event.timestamp : previous.started,
      ended: event.kind === 'stage_notice' ? previous.ended : status === 'completed' || status === 'failed' ? event.timestamp : null,
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
  return { ...latest, status, started: starts[0] ?? null, ended: status === 'running' ? null : ends.at(-1) ?? null,
    periods: items.flatMap(item => item.periods ?? (item.started ? [{ started: item.started, ended: item.ended }] : [])) };
}
/** Time when at least one variant was active; review gaps and overlaps do not add time. */
export function stageElapsed(stage: StageItem, now: number): string {
  if (!stage.started) return '—';
  const periods = (stage.periods ?? [{ started: stage.started, ended: stage.ended }])
    .map(period => [Date.parse(period.started), period.ended ? Date.parse(period.ended) : now] as const)
    .sort((a, b) => a[0] - b[0]);
  let total = 0; let end = -Infinity;
  for (const [start, stop] of periods) {
    total += Math.max(0, stop - Math.max(start, end));
    end = Math.max(end, stop);
  }
  return `${Math.floor(total / 1000)}s`;
}
export function applySnapshot(model: RunModel, results: ResultsResponse): RunModel {
  return { ...model, runStatus: results.run.status, plan: results.plan,
    packageStatuses: Object.fromEntries(results.packages.map(item => [item.variant, item.status])) };
}
