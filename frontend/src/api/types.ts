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
  review_decision?: {action:string;reviewer_name:string|null;reason:string|null;decided_at:string|null;identity_basis:string} | null;
  review_feedback: string | null;
  readiness_label: 'checks_passed' | 'engineer_approved' | 'rejected' | 'pending_review' | null;
  downloadable: boolean; review_available: boolean; retry_in_progress: boolean;
  review_reasons: ReviewReason[]; retry_targets: string[];
}
export interface ResultsResponse {
  run: RunResult; plan: DeploymentPlan | null; packages: PackageResult[];
  missing_variants: { variant: Variant; error: string }[];
}
export type ThinkingMode = "off"|"low"|"medium"|"high";
export interface AgentChoice {model:string;thinking_mode?:ThinkingMode|null}
export interface AgentSelection extends AgentChoice {provider:Provider;configured_thinking?:ThinkingMode|null;request_style?:string}
export interface CatalogModel {id:string;name:string;context_length:number|null;pricing:Record<string,string|number>;structured_output:boolean|null;reasoning:boolean|null;thinking_modes:ThinkingMode[];source:string}
export interface Catalog {output_token_limits?:Record<string,number>;environment_defaults?:Record<string,AgentSelection>;provider:string;credential_id:string|null;models:CatalogModel[];defaults:Record<string,AgentChoice>;status?:string}
export interface RunConfig { agent_models?:Record<string,AgentChoice>; policy_profile?:'strict'|'contextual-v1'; provider?: Provider; model?: string; max_iterations?: number }
export interface SubmitResponse { run_id: string; status: 'created'; stream_url: string }
export interface ReviewRequest { action: 'approve' | 'retry' | 'reject'; reviewer_name?:string;reason?:string; feedback?: string; target_files?: string[] }
export interface ReviewResponse { run_id: string; variant: Variant; status: PackageStatus }
export interface RetryResponse extends ReviewResponse { stream_url: string }
export interface ErrorResponse { error: string; message: string }
export interface RunEvent {
  seq: number; kind: EventKind; agent: AgentName; status: string;
  previous_status: string | null; message: string | null; variant: Variant | null;
  timestamp: string; payload: Record<string, unknown>;
}
