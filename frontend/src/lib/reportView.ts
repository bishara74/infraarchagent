import type { PackageResult } from '../api/types';
export const record = (value: unknown): Record<string, unknown> => value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
export const records = (value: unknown) => Array.isArray(value) ? value.map(record) : [];
export const text = (value: unknown) => typeof value === 'string' ? value : '';
export const strings = (value: unknown) => Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
export function securityView(report: PackageResult['security_report']) {
  const root=record(report); const sessions=records(root.sessions);
  const first=sessions.find(item=>item.kind==='automated'); const scan=record(records(first?.iterations)[0]?.scan);
  const fixes: (Record<string,unknown> & {session:number;sessionKind:string;applied:boolean})[]=sessions.flatMap((session,index)=>records(session.iterations).flatMap(iteration=>records(iteration.fixes).map(fix=>({ ...fix, applied:fix.accepted===true&&fix.retained!==false, session:index+1, sessionKind:text(session.kind) }))));
  const initial=Array.isArray(scan.blocking) && (root.omitted_session_count===0 || root.omitted_session_count===undefined) ? scan.blocking.length : null;
  const final=record(root.final); const remaining=Array.isArray(final.remaining_blocking) ? records(final.remaining_blocking) : null;
  return { initial, remaining, fixes, applied:fixes.filter(fix=>fix.applied).length, outcome:text(final.outcome), omitted:Number(root.omitted_session_count)||0 };
}
export function fixSeverities(report:PackageResult['security_report'],fix:Record<string,unknown>) {
  const evidence=records(record(report).sessions).flatMap(session=>records(session.iterations).flatMap(iteration=>records(record(iteration.scan).blocking)));
  return [...new Set(evidence.filter(finding=>finding.file_path===fix.file&&strings(fix.rule_ids).includes(text(finding.rule_id))).map(finding=>text(finding.severity)).filter(Boolean))];
}
export function validationView(report: PackageResult['validation_report']) {
  const root=record(report); return { checks:records(root.checks), summary:record(root.summary), omitted:record(root.omitted_counts), abort:text(root.abort_reason) };
}
export function fileRules(item: PackageResult,path:string) {
  const view=securityView(item.security_report); return [...new Set(view.fixes.filter(fix=>fix.file===path).flatMap(fix=>strings(fix.rule_ids)))];
}
