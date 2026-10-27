export const variants = ['cost', 'performance', 'security'] as const;
export type Variant = typeof variants[number];
export type Provider = 'stub' | 'openai' | 'anthropic';
export type RunStatus = 'created' | 'running' | 'success' | 'partial_success' | 'failed';
export type PackageStatus = 'generating' | 'generated' | 'failed' | 'scanning' | 'remediating' | 'scan_clean' | 'scan_exhausted' | 'scan_error' | 'validating' | 'valid' | 'invalid' | 'validation_error' | 'pending_review' | 'checks_passed' | 'engineer_approved' | 'rejected';
export type AgentName = 'orchestrator' | 'architect' | 'generator_cost' | 'generator_performance' | 'generator_security' | 'security' | 'validator';
export type AgentState = 'pending' | 'running' | 'completed' | 'failed';
export type EventKind = 'run_status' | 'agent_state' | 'plan_created' | 'package_status' | 'package_generated' | 'stage_notice';
export type ReviewReason = 'unresolved_security_findings' | 'validation_failed' | 'validation_error' | 'retry_aborted';

export interface DeploymentPlan {
  cloud_provider: 'aws';
  services: { name: string; aws_service: string; purpose: string }[];
  dependencies: { source: string; target: string; description: string }[];
  network: { public_services: string[]; private_services: string[]; ingress: string[]; notes: string };
  storage: { name: string; kind: 'relational_db' | 'nosql_db' | 'object_storage' | 'block_volume' | 'cache' | 'other'; aws_service: string; attached_to: string[] }[];
  file_types: ('terraform' | 'kubernetes' | 'helm' | 'nginx' | 'jenkins' | 'ansible' | 'prometheus' | 'grafana' | 'dockerfile')[];
  ambiguities: { topic: string; detail: string; assumption: string }[];
}
export interface ProfileAssessment {checks_passed:boolean;remaining_blocking:number;excepted:{rule_id:string;resource:string;file_path:string;entry_id:string;classification:string;justification:string}[]}
export interface RunResult {
  lessons?:LessonManifest|null;
  agent_models?: Record<string,AgentSelection>|null;
  policy_profile?: 'strict'|'contextual-v1';
  id: string; status: RunStatus; input_text: string; start_time: string;
  end_time: string | null; provider: Provider; model: string | null;
  max_iterations: number; error_message: string | null;
}
export interface PackageResult {
  variant: Variant; status: PackageStatus; iteration_count: number;
  error: string | null; files: Record<string, string>;
  original_files: Record<string, string> | null;
  security_report: Record<string, unknown> | null;
  validation_report: Record<string, unknown> | null;
  profile_assessments?: Record<'strict'|'contextual-v1',ProfileAssessment> & Partial<Record<'contextual-v2',ProfileAssessment>>;
  review_decision?: {decision_id?:string;user_id?:string|null;remaining_blocking_rules?:string[]|null;action:string;reviewer_name:string|null;category?:ReviewCategory|null;reason:string|null;decided_at:string|null;identity_basis:string} | null;
  review_feedback: string | null;
  readiness_label: 'checks_passed' | 'engineer_approved' | 'rejected' | 'pending_review' | null;
  downloadable: boolean; review_available: boolean;
  review_actions?: Array<'approve'|'retry'|'reject'>; retry_in_progress: boolean;
  review_reasons: ReviewReason[]; retry_targets: string[];
}
export interface ResultsResponse {
  run: RunResult; plan: DeploymentPlan | null; packages: PackageResult[];
  missing_variants: { variant: Variant; error: string }[];
}
export type ThinkingMode = "off"|"low"|"medium"|"high";
export interface AgentChoice {model:string;thinking_mode?:ThinkingMode|null}
export interface AgentSelection extends AgentChoice {provider:Provider;configured_thinking?:ThinkingMode|null;request_style?:string}
export interface CatalogModel {deprecated?:boolean|null;expiration_date?:string|null;id:string;name:string;context_length:number|null;pricing:Record<string,string|number>;structured_output:boolean|null;reasoning:boolean|null;thinking_modes:ThinkingMode[];source:string}
export interface ResolutionContext {provider:Provider;model:string|null;thinking_mode:ThinkingMode|null;fixer_provider:Provider|null;fixer_model:string|null;fixer_thinking_mode:ThinkingMode|null}
export interface Catalog {server_default_max_iterations?:number;resolution_context?:ResolutionContext;output_token_limits?:Record<string,number>;environment_defaults?:Record<string,AgentSelection>;provider:string;credential_id:string|null;models:CatalogModel[];defaults:Record<string,AgentChoice>;status?:string;error_code?:string}
export interface RunConfig { agent_models?:Record<string,AgentChoice>; policy_profile?:'strict'|'contextual-v1'; provider?: Provider; model?: string; max_iterations?: number }
export interface SubmitResponse { run_id: string; status: 'created'; stream_url: string }
export interface ReviewRequest { action: 'approve' | 'retry' | 'reject'; reviewer_name?:string;reason?:string;category?:ReviewCategory; feedback?: string; target_files?: string[] }
export interface ReviewResponse { run_id: string; variant: Variant; status: PackageStatus }
export interface RetryResponse extends ReviewResponse { stream_url: string }
export interface ErrorResponse { error: string; message: string }
export interface RunEvent {
  seq: number; kind: EventKind; agent: AgentName; status: string;
  previous_status: string | null; message: string | null; variant: Variant | null;
  timestamp: string; payload: Record<string, unknown>;
}

export type ReviewCategory='requirements_not_met'|'too_expensive'|'organisational_policy'|'security_concern'|'operability'|'too_complex'|'other'|'meets_requirements'|'accepted_risk'|'approved_with_follow_ups'|'organisational_exception';

export interface InsightGroup {value:string;count:number;filters:Record<string,string>}
export interface FeedbackInsightsData {
  total:number;filters:Record<string,string>;
  by_category:InsightGroup[];by_variant:InsightGroup[];by_decision:InsightGroup[];
  blocking_rules:{rule_id:string;count:number;filters:Record<string,string>}[];
  accepted_risk_total?:number;accepted_risk_rules?:{rule_id:string;count:number;filters:Record<string,string>}[];
  rejected_total:number;blocking_snapshot_available:number;blocking_snapshot_unavailable:number;
}

export type LessonRole='fixer'|'architect'|'generator_cost'|'generator_performance'|'generator_security'|'all_generators';
export type LessonTag='load_balancer'|'database'|'storage'|'network'|'kubernetes'|'cost'|'logging';
export interface LessonFilterResult {version:string;passed:boolean;reasons:{id:string;message:string}[]}
export interface LessonInput {scope_role:LessonRole;applies_to:LessonTag[];category:ReviewCategory;text:string}
export interface LessonEntry extends LessonInput {approval?:string|null;approval_actor?:{user_id:string;username:string}|null;id:string;lesson_id:string;revision:number;self_approved:boolean;filter_version:string}
export interface LessonRevision extends LessonEntry {
  status:'proposed'|'approved'|'retired'|'rejected';previous_id:string|null;decision_id:string;
  proposer_id:string;proposer:string|null;approved_by:string|null;approver:string|null;
  approved_at:string|null;created_at:string;filter_result:LessonFilterResult;
  proposal_filter_result:LessonFilterResult;approval_filter_result:LessonFilterResult|null;
  source_decision?:{id:string;run_id:string;variant:string|null;timestamp:string;action:string|null;reviewer_name:string|null;user_id:string|null;reason:string|null;category:ReviewCategory|null;decided_at:string|null;identity_basis:string|null}|null;
}
export interface LessonPreview {filter_result:LessonFilterResult;roles:Record<string,{block:string;selected_ids:string[];included:boolean}>}
export interface LessonDetail {lesson:LessonRevision;previous:LessonRevision|null;preview:LessonPreview}
export interface LessonControls {admin_direct_activation?:boolean;server_enabled:boolean;runtime_enabled:boolean;enabled:boolean;require_second_approver:boolean;disable_generation:number;set_version:number;set_hash:string;lesson_count:number}
export interface LessonPage {items:LessonRevision[];total:number;page:number;page_size:number}
export interface LessonAuditRow {id:string;seq:number;actor_id:string;action:string;revision_id:string|null;previous_version:string|null;set_version:number|null;timestamp:string;payload:Record<string,unknown>}
export interface LessonHistoryPage {items:LessonAuditRow[];total:number;page:number;page_size:number}
export interface LessonConfirmation {confirmation_token:string;expires_at:string;lesson:LessonEntry;preview:LessonPreview;set_version:number;require_second_approver:boolean;warning:string}
export interface LessonUsage {enabled:boolean;set_version:number;set_hash:string;lesson_ids:string[];block_hash:string|null;self_approved:boolean;reason:string}
export interface LessonManifest {
  schema_version:number;recorded:boolean;lessons_enabled:boolean;set_version:number;set_hash:string;
  entries:LessonEntry[];disable_generation:number|null;self_approved:boolean;eligible_self_approved:boolean;
  reason:string;calls:(LessonUsage&{call_id:string|null;role:string|null;outcome:string|null})[];
  used_lesson_ids:string[];used_count:number;disabled_during_run:boolean;
}
