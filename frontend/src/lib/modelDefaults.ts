import type { AgentChoice, Catalog, RunConfig } from '../api/types';

export const generatorRoles = ['generator_cost', 'generator_performance', 'generator_security'] as const;

/** Missing metadata is evidence of absence only after a successful catalogue load. */
export function modelProblem(role:string,catalog:Catalog|null,defaults:Record<string,AgentChoice>,overrides:Record<string,AgentChoice>,config:RunConfig) {
 if(!catalog||['setup_required','invalid','unavailable'].includes(catalog.status??'')||(catalog.status==='no_credit'&&!catalog.models.length))return undefined;
 const merged={...defaults,...overrides};
 for(const key of role==='generators'?generatorRoles:[role]) {
  const saved=merged[key]??(key.startsWith('generator_')?merged.generators:undefined);
  const effective=modelDefault(key,catalog,defaults,overrides,config);
  const metadata=catalog.models.find(item=>item.id===effective?.model);
  if(!metadata&&saved)return `This saved model (${saved.model}) is unavailable. Select Use default or a listed model; update the saved default if inherited.`;
  if(metadata?.structured_output===false)return `This model (${metadata.id}) can't return the structured JSON the pipeline needs. Choose a structured-output model or update its saved default.`;
  if(saved&&metadata?.structured_output===null)return `Structured-output support for ${metadata.id} is unknown. Retry the catalogue or choose a confirmed structured-output model.`;
 }
 return undefined;
}

/** Keep role-before-group precedence from ModelSelectionService.resolve. */
export function modelDefault(role: string, catalog: Catalog | null, defaults: Record<string, AgentChoice>, overrides: Record<string, AgentChoice> = {}, config: RunConfig = {}): AgentChoice | undefined {
  const choices = { ...defaults, ...overrides };
  const chosen = choices[role] ?? (role.startsWith('generator_') ? choices.generators : undefined);
  if (chosen) return {...chosen,thinking_mode:chosen.thinking_mode??null};
  const context = catalog?.resolution_context;
  if (!context) return catalog?.environment_defaults?.[role];
  let provider = config.provider ?? context.provider;
  let model = provider === 'stub' ? 'stub' : config.model ?? context.model;
  let thinking = context.thinking_mode;
  if (catalog?.credential_id) {
    provider = catalog.provider === 'anthropic' ? 'anthropic' : 'openai';
    model = choices.architect?.model ?? config.model ?? context.model;
  }
  if (role === 'fixer' && provider !== 'stub' && provider === context.provider) {
    provider = context.fixer_provider ?? provider;
    model = context.fixer_model ?? model;
    thinking = context.fixer_thinking_mode ?? thinking;
  }
  if (!model) return undefined;
  return { model, thinking_mode: catalog?.credential_id ? thinking : provider === 'anthropic' ? null : thinking };
}

export function choiceLabel(choice: AgentChoice | undefined) {
  return choice ? `${choice.model} · ${choice.thinking_mode ?? 'provider default'}` : 'unavailable';
}

export function defaultLabel(role: string, catalog: Catalog | null, defaults: Record<string, AgentChoice>, overrides: Record<string, AgentChoice> = {}, config: RunConfig = {}) {
  if (role !== 'generators') return choiceLabel(modelDefault(role, catalog, defaults, overrides, config));
  const labels = generatorRoles.map(key => choiceLabel(modelDefault(key, catalog, defaults, overrides, config)));
  return labels.every(label => label === labels[0]) ? labels[0]! : labels.map((label, index) => `${generatorRoles[index]!.slice(10)}: ${label}`).join('; ');
}
