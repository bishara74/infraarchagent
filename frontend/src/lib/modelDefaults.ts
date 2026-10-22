import type { AgentChoice, Catalog } from '../api/types';

export const generatorRoles = ['generator_cost', 'generator_performance', 'generator_security'] as const;

/** Keep role-before-group precedence from ModelSelectionService.resolve. */
export function modelDefault(role: string, catalog: Catalog | null, defaults: Record<string, AgentChoice>, overrides: Record<string, AgentChoice> = {}): AgentChoice | undefined {
  const choices = { ...defaults, ...overrides };
  const chosen = choices[role] ?? (role.startsWith('generator_') ? choices.generators : undefined);
  if (chosen) return chosen;
  return catalog?.environment_defaults?.[role];
}

export function choiceLabel(choice: AgentChoice | undefined) {
  return choice ? `${choice.model} · ${choice.thinking_mode ?? 'provider default'}` : 'unavailable';
}

export function defaultLabel(role: string, catalog: Catalog | null, defaults: Record<string, AgentChoice>, overrides: Record<string, AgentChoice> = {}) {
  if (role !== 'generators') return choiceLabel(modelDefault(role, catalog, defaults, overrides));
  const labels = generatorRoles.map(key => choiceLabel(modelDefault(key, catalog, defaults, overrides)));
  return labels.every(label => label === labels[0]) ? labels[0] : labels.map((label, index) => `${generatorRoles[index]!.slice(10)}: ${label}`).join('; ');
}
