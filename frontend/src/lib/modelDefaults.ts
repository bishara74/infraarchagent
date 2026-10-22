import type { AgentChoice, Catalog, RunConfig } from '../api/types';

export const generatorRoles = ['generator_cost', 'generator_performance', 'generator_security'] as const;

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
