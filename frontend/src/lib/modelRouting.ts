import type {Catalog} from '../api/types';
const routing=new Set(['nitro','floor','exacto','online']);
export function catalogueId(provider:string,id:string){
 if(provider!=='openrouter')return id;
 const [slug,...suffixes]=id.split(':');return [slug,...suffixes.filter(s=>!routing.has(s))].join(':');
}
export function catalogueModel(catalog:Catalog|null,id:string|undefined){
 if(!catalog||!id)return undefined;
 const resolved=catalogueId(catalog.provider,id);
 return catalog.models.find(item=>item.id===resolved)??catalog.models.find(item=>item.id===id);
}
export function movingAlias(id:string){const slug=id.split(':')[0]!;return slug.startsWith('~')||slug.endsWith('-latest');}
