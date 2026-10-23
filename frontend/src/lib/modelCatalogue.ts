import recommended from '../config/recommended-models.v1.json';
import type {Catalog,CatalogModel} from '../api/types';

export function isRecommended(provider:string,model:CatalogModel) {
 return recommended.models.some(entry=>entry.provider===provider&&entry.id===model.id);
}
export function compatibleModels(catalog:Catalog|null,all:boolean,now=new Date()):CatalogModel[] {
 if(!catalog)return [];
 return catalog.models.filter(model=>{
  if(model.structured_output!==true||model.id.toLowerCase().endsWith(':free')||model.deprecated===true)return false;
  if(model.expiration_date&&Date.parse(model.expiration_date)<=now.getTime())return false;
  return all||isRecommended(catalog.provider,model)||(catalog.provider==='stub'&&model.source==='builtin');
 }).sort((a,b)=>{
  const vendor=(item:CatalogModel)=>catalog.provider==='openrouter'?item.id.split('/')[0]!:catalog.provider;
  return vendor(a).localeCompare(vendor(b),'en',{sensitivity:'base'})||a.name.localeCompare(b.name,'en',{sensitivity:'base',numeric:true})||a.id.localeCompare(b.id);
 });
}
export function modelDetail(model:CatalogModel) {
 const price=(key:string)=>{const raw=model.pricing[key];const rate=raw===undefined?NaN:Number(raw);return Number.isFinite(rate)&&rate>=0?`$${(rate*1e6).toLocaleString()} / million tokens`:'unavailable';};
 return `structured output · ${model.reasoning===true?'reasoning':model.reasoning===false?'no reasoning':'reasoning unknown'} · input: ${price('prompt')} · output: ${price('completion')} · context: ${model.context_length?.toLocaleString()??'unknown'} tokens`;
}
