import type { AgentChoice, Catalog, ThinkingMode } from '../api/types';
import { defaultLabel } from '../lib/modelDefaults';
const roles = [['architect', 'Architect'], ['generators', 'Generators'], ['fixer', 'Fixer']] as const;
const advanced = [['generator_cost', 'Cost Generator'], ['generator_performance', 'Performance Generator'], ['generator_security', 'Security Generator']] as const;
export function ModelControls({ catalog, value, onChange, defaults = {} }: {
    catalog: Catalog | null;
    value: Record<string, AgentChoice>;
    onChange: (value: Record<string, AgentChoice>) => void;
    defaults?: Record<string, AgentChoice>;
}) {
    function field(role: string, label: string) {
        const choice = value[role];
        const model = catalog?.models.find(m => m.id === choice?.model);
        const limit = catalog?.output_token_limits?.[role.startsWith('generator') ? 'generators' : role];
        const price = Number(model?.pricing.prompt);
        const outputPrice = Number(model?.pricing.completion);
        const estimate = limit !== undefined && Number.isFinite(price) && Number.isFinite(outputPrice) ? ` Illustrative initial call: $${(1000 * price + limit * .25 * outputPrice).toFixed(4)}–$${(4000 * price + limit * outputPrice).toFixed(4)} (1k–4k input tokens, 25–100% of a ${limit.toLocaleString()}-token output allowance; retries extra).` : '';
        return <div className="model-choice" key={role}><label>{label} model<select aria-label={`${label} model`} value={choice?.model ?? ''} onChange={event => { const next = { ...value }; if (event.target.value)
            next[role] = { model: event.target.value };
        else
            delete next[role]; onChange(next); }}><option value="">Use default — {defaultLabel(role, catalog, defaults)}</option>{choice && !model && <option value={choice.model} disabled>Unavailable model — {choice.model}</option>}{catalog?.models.map(m => <option key={m.id} value={m.id} disabled={role !== 'architect' && m.structured_output !== true}>{m.name} ({m.id}){role !== 'architect' && m.structured_output !== true ? ' — unsuitable: structured output unknown or unsupported' : ''}</option>)}</select></label>{model?.reasoning === true && <label>{label} thinking<select aria-label={`${label} thinking`} value={choice?.thinking_mode ?? ''} onChange={event => onChange({ ...value, [role]: { model: model.id, thinking_mode: (event.target.value || null) as ThinkingMode | null } })}><option value="">Use configured default</option>{model.thinking_modes.map(mode => <option key={mode} value={mode}>{mode}</option>)}</select></label>}{model && <p className="muted">Context: {model.context_length?.toLocaleString() ?? 'unknown'} tokens. {Object.keys(model.pricing).length ? Object.entries(model.pricing).map(([kind, rate]) => `${kind}: $${(Number(rate) * 1e6).toLocaleString()} / million tokens`).join(' · ') : 'Pricing unavailable.'}{model.reasoning === false ? ' No reasoning support.' : ''}{estimate}</p>}</div>;
    }
    return <>{roles.map(([role, label]) => field(role, label))}<details><summary>Advanced: per-generator overrides</summary>{advanced.map(([role, label]) => field(role, label))}</details><button type="button" onClick={() => onChange({})}>Use defaults</button></>;
}
