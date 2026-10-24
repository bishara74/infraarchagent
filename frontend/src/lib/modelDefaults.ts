import {catalogueModel} from './modelRouting';
import type {AgentChoice,Catalog,RunConfig} from '../api/types';

export const generatorRoles = ['generator_cost', 'generator_performance', 'generator_security'] as const;
export type ChoiceTier = 'run'|'personal'|'admin';
export type ChoiceSource = ChoiceTier|'environment';
export type ModelLayers = Partial<Record<ChoiceTier,Record<string,AgentChoice>>>;
export interface ResolvedChoice {choice:AgentChoice;source:ChoiceSource}
export const sourceLabel = (source:ChoiceSource) => ({run:'from this run',personal:'from your defaults',admin:'from administrator defaults',environment:'server default'})[source];

/** Match backend tier order; generator specificity applies inside each tier. */
export function resolveModel(role:string,catalog:Catalog|null,layers:ModelLayers={},config:RunConfig={}):ResolvedChoice|undefined {
  for(const source of ['run','personal','admin'] as const) {
    const tier=layers[source];
    const chosen=tier?.[role]??(role.startsWith('generator_')?tier?.generators:undefined);
    if(chosen)return {choice:{...chosen,thinking_mode:chosen.thinking_mode??null},source};
  }
  const context=catalog?.resolution_context;
  if(!context) {
    const choice=catalog?.environment_defaults?.[role];
    return choice?{choice,source:'environment'}:undefined;
  }
  const provider=catalog?.credential_id?(catalog.provider==='anthropic'?'anthropic':'openai'):config.provider??context.provider;
  let model=provider==='stub'?'stub':config.model??context.model;
  let thinking=context.thinking_mode;
  if(role==='fixer'&&provider!=='stub'&&provider===context.provider) {
    model=context.fixer_model??model;
    thinking=context.fixer_thinking_mode??thinking;
  }
  if(!model)return undefined;
  const effectiveProvider=role==='fixer'&&provider!=='stub'&&provider===context.provider?context.fixer_provider??provider:provider;
  return {choice:{model,thinking_mode:catalog?.credential_id?thinking:effectiveProvider==='anthropic'?null:thinking},source:'environment'};
}

export function modelDefault(role:string,catalog:Catalog|null,layers:ModelLayers={},config:RunConfig={}):AgentChoice|undefined {
  return resolveModel(role,catalog,layers,config)?.choice;
}

/** Missing metadata is evidence of absence only after a successful catalogue load. */
export function modelProblem(role:string,catalog:Catalog|null,layers:ModelLayers,config:RunConfig) {
  if(!catalog||['setup_required','invalid','unavailable'].includes(catalog.status??'')||(catalog.status==='no_credit'&&!catalog.models.length))return undefined;
  for(const key of role==='generators'?generatorRoles:[role]) {
    const effective=resolveModel(key,catalog,layers,config);
    if(!effective)return `No default is configured for ${key.replaceAll('_',' ')}. Choose a model or configure its default in Settings.`;
    const {choice,source}=effective;
    const saved=source!=='environment';
    const metadata=catalogueModel(catalog,choice.model);
    if(!metadata&&saved)return `This saved model (${choice.model}) is unavailable. Select Use default or a listed model; update the saved default if inherited.`;
    if(metadata?.structured_output===false)return `This model (${metadata.id}) can't return the structured JSON the pipeline needs. Choose a structured-output model or update its saved default.`;
    if(saved&&metadata?.structured_output===null)return `Structured-output support for ${metadata.id} is unknown. Retry the catalogue or choose a confirmed structured-output model.`;
  }
  return undefined;
}

export function choiceLabel(choice:AgentChoice|undefined) {
  return choice?`${choice.model} · ${choice.thinking_mode??'provider default'}`:'unavailable';
}

export function resolvedLabel(value:ResolvedChoice|undefined) {
  return value?`${choiceLabel(value.choice)} (${sourceLabel(value.source)})`:'unavailable';
}

export function defaultLabel(role:string,catalog:Catalog|null,layers:ModelLayers={},config:RunConfig={}) {
  if(role!=='generators')return resolvedLabel(resolveModel(role,catalog,layers,config));
  const labels=generatorRoles.map(key=>resolvedLabel(resolveModel(key,catalog,layers,config)));
  return labels.every(label=>label===labels[0])?labels[0]!:labels.map((label,index)=>`${generatorRoles[index]!.slice(10)}: ${label}`).join('; ');
}
