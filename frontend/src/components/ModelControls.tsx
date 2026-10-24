import {catalogueModel} from '../lib/modelRouting';
import {useState} from 'react';
import {compatibleModels,isRecommended,modelDetail} from '../lib/modelCatalogue';
import type {AgentChoice,Catalog,RunConfig,ThinkingMode} from '../api/types';
import {choiceLabel,defaultLabel,modelDefault,modelProblem} from '../lib/modelDefaults';
import {ModelCombobox,type ModelOption} from './ModelCombobox';
export const structuredExplanation="Every pipeline role needs structured JSON. Choose a confirmed structured-output model or use the environment default.";
const roles=[['architect','Architect'],['generators','Generators'],['fixer','Fixer']] as const;
const advanced=[['generator_cost','Cost Generator'],['generator_performance','Performance Generator'],['generator_security','Security Generator']] as const;
export function ModelControls({catalog,value,onChange,defaults={},config={},showReset=true,retry,loaded=!!catalog}:{catalog:Catalog|null;value:Record<string,AgentChoice>;onChange:(value:Record<string,AgentChoice>)=>void;defaults?:Record<string,AgentChoice>;config?:RunConfig;showReset?:boolean;retry?:()=>void;loaded?:boolean}) {
 const [showAll,setShowAll]=useState(false);
 const listed=compatibleModels(catalog,showAll);
 function field(role:string,label:string){
  const without={...value};delete without[role];
  const fallback=defaultLabel(role,catalog,defaults,without,config);
  const effective=role==='generators'?modelDefault('generator_cost',catalog,defaults,value,config):modelDefault(role,catalog,defaults,value,config);
  const choice=value[role];const model=catalogueModel(catalog,choice?.model??effective?.model);
  const fieldError=modelProblem(role,catalog,defaults,value,config);
  const defaultError=modelProblem(role,catalog,defaults,without,config);
  const options:ModelOption[]=[{value:'',label:`Use default — ${fallback}`,detail:'Inherits personal, administrator, then environment settings.',disabled:!!defaultError,explanation:defaultError},...listed.map(item=>({value:item.id,label:`${item.name} (${item.id})`,detail:modelDetail(item),tested:isRecommended(catalog!.provider,item)}))];
  const limit=catalog?.output_token_limits?.[role.startsWith('generator')?'generators':role];const price=Number(model?.pricing.prompt),completion=Number(model?.pricing.completion);
  const estimate=limit&&Number.isFinite(price)&&Number.isFinite(completion)?`Illustrative initial call: $${(1000*price+limit*.25*completion).toFixed(4)}–$${(4000*price+limit*completion).toFixed(4)} (1k–4k input tokens, 25–100% of a ${limit.toLocaleString()}-token output allowance; retries extra).`:'';
  return <div className="model-choice" key={role}><ModelCombobox selectedLabel={choice?`${model?.name??'Saved model'} (${choice.model})`:undefined} error={fieldError} label={`${label} model`} value={choice?.model??''} options={options} onChange={selected=>{const next={...value};if(selected)next[role]={model:selected};else delete next[role];onChange(next);}}/>
   {model?.reasoning!==false&&<label>{label} thinking<select aria-label={`${label} thinking`} value={choice?.thinking_mode??(choice? '':effective?.thinking_mode??'')} disabled={!model||!effective||(role==='generators'&&fallback.includes(';'))} onChange={event=>{if(effective)onChange({...value,[role]:{model:choice?.model??effective.model,thinking_mode:(event.target.value||null) as ThinkingMode|null}});}}><option value="">{!choice&&!effective?.thinking_mode?'Provider default (inherited)':'Provider default'}</option>{[...new Set([...(model?.thinking_modes??[]),...(!choice&&effective?.thinking_mode?[effective.thinking_mode]:[])])].map(mode=><option key={mode} value={mode}>{mode}{!choice&&mode===effective?.thinking_mode?(defaults[role]||without[role]||((role.startsWith('generator')||role==='generators')&&(defaults.generators||without.generators))?' (inherited default)':' (server default)'):''}</option>)}</select></label>}
   {model?.reasoning===false&&<p className="muted">No thinking control: this model has no reasoning support.</p>}
   {loaded&&!model&&(choice?.model||effective?.model)&&<div className="muted"><p>We couldn't load details for this model. It will still run with the server's settings.</p>{retry&&<button type="button" onClick={retry}>Retry</button>}</div>}
   {role==='generators'&&fallback.includes(';')&&<p className="muted">Per-variant defaults differ. Set thinking in Advanced for each variant.</p>}
   <p className="muted model-detail">{choice?`Selected: ${choiceLabel(choice)}. `:''}{model?`Context: ${model.context_length?.toLocaleString()??'unknown'} tokens. `:''}{estimate}</p>
  </div>;
 }
 return <><div className="model-filter"><strong>{showAll?'All compatible models':'Recommended'}</strong><label className="checkbox"><input type="checkbox" checked={showAll} onChange={event=>setShowAll(event.target.checked)}/>Show all compatible models</label>{catalog&&!listed.length&&<p className="muted">{showAll?'No confirmed structured-output models are available. Retry the catalogue or check provider access.':'No recommended models available for this provider. Use the environment default or enable Show all compatible models.'}</p>}</div>{roles.map(([role,label])=>field(role,label))}<details className="model-advanced"><summary>Advanced: per-generator overrides</summary><div className="model-grid">{advanced.map(([role,label])=>field(role,label))}</div></details>{showReset&&<div className="form-actions model-reset"><button type="button" onClick={()=>onChange({})}>Use defaults</button></div>}</>;
}
