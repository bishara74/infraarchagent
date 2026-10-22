import type {AgentChoice,Catalog,RunConfig,ThinkingMode} from '../api/types';
import {choiceLabel,defaultLabel,modelDefault} from '../lib/modelDefaults';
import {ModelCombobox,type ModelOption} from './ModelCombobox';
export const structuredExplanation="This model can't return the structured JSON the Generators and Fixer need. Pick a model marked 'structured output', or select Use default.";
const roles=[['architect','Architect'],['generators','Generators'],['fixer','Fixer']] as const;
const advanced=[['generator_cost','Cost Generator'],['generator_performance','Performance Generator'],['generator_security','Security Generator']] as const;
export function ModelControls({catalog,value,onChange,defaults={},config={},showReset=true}:{catalog:Catalog|null;value:Record<string,AgentChoice>;onChange:(value:Record<string,AgentChoice>)=>void;defaults?:Record<string,AgentChoice>;config?:RunConfig;showReset?:boolean}) {
 function field(role:string,label:string){
  const without={...value};delete without[role];
  const fallback=defaultLabel(role,catalog,defaults,without,config);
  const effective=role==='generators'?modelDefault('generator_cost',catalog,defaults,value,config):modelDefault(role,catalog,defaults,value,config);
  const choice=value[role];const model=catalog?.models.find(item=>item.id===(choice?.model??effective?.model));
  const options:ModelOption[]=[{value:'',label:`Use default — ${fallback}`,detail:'Inherits personal, administrator, then environment settings.'},...(catalog?.models.map(item=>({value:item.id,label:`${item.name} (${item.id})`,detail:`${item.structured_output===true?'structured output':'structured output unknown or unsupported'} · ${item.reasoning===true?'reasoning':item.reasoning===false?'no reasoning':'reasoning unknown'} · ${Object.keys(item.pricing).length?Object.entries(item.pricing).map(([kind,rate])=>`${kind}: $${(Number(rate)*1e6).toLocaleString()} / million tokens`).join(' · '):'Pricing unavailable'}`,disabled:role!=='architect'&&item.structured_output!==true,explanation:structuredExplanation}))??[])];
  if(choice&&!catalog?.models.some(item=>item.id===choice.model))options.push({value:choice.model,label:`Unavailable model — ${choice.model}`,detail:'Refresh the catalogue or choose another model.',disabled:true,explanation:'This saved model is unavailable. Select Use default or another available model.'});
  const limit=catalog?.output_token_limits?.[role.startsWith('generator')?'generators':role];const price=Number(model?.pricing.prompt),completion=Number(model?.pricing.completion);
  const estimate=limit&&Number.isFinite(price)&&Number.isFinite(completion)?`Illustrative initial call: $${(1000*price+limit*.25*completion).toFixed(4)}–$${(4000*price+limit*completion).toFixed(4)} (1k–4k input tokens, 25–100% of a ${limit.toLocaleString()}-token output allowance; retries extra).`:'';
  return <div className="model-choice" key={role}><ModelCombobox label={`${label} model`} value={choice?.model??''} options={options} onChange={selected=>{const next={...value};if(selected)next[role]={model:selected};else delete next[role];onChange(next);}}/>
   {model?.reasoning!==false&&<label>{label} thinking<select aria-label={`${label} thinking`} value={choice?.thinking_mode??(choice? '':effective?.thinking_mode??'')} disabled={!model||!effective||(role==='generators'&&fallback.includes(';'))} onChange={event=>{if(effective)onChange({...value,[role]:{model:choice?.model??effective.model,thinking_mode:(event.target.value||null) as ThinkingMode|null}});}}><option value="">Provider default</option>{model?.thinking_modes.map(mode=><option key={mode} value={mode}>{mode}</option>)}</select></label>}
   {model?.reasoning===false&&<p className="muted">No thinking control: this model has no reasoning support.</p>}
   {!model&&<p className="muted">Model capabilities unavailable. Refresh the catalogue or choose a model.</p>}
   {role==='generators'&&fallback.includes(';')&&<p className="muted">Per-variant defaults differ. Set thinking in Advanced for each variant.</p>}
   <p className="muted model-detail">{choice?`Selected: ${choiceLabel(choice)}. `:''}{model?`Context: ${model.context_length?.toLocaleString()??'unknown'} tokens. `:''}{estimate}</p>
  </div>;
 }
 return <>{roles.map(([role,label])=>field(role,label))}<details className="model-advanced"><summary>Advanced: per-generator overrides</summary><div className="model-grid">{advanced.map(([role,label])=>field(role,label))}</div></details>{showReset&&<div className="form-actions model-reset"><button type="button" onClick={()=>onChange({})}>Use defaults</button></div>}</>;
}
