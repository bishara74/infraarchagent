import {expect,it} from 'vitest';
import type {Catalog,CatalogModel} from '../api/types';
import {compatibleModels,modelDetail} from './modelCatalogue';

const model=(id:string,extra:Partial<CatalogModel>={}):CatalogModel=>({id,name:id,context_length:32768,pricing:{prompt:'0.000001',completion:'0.000002'},structured_output:true,reasoning:null,thinking_modes:[],source:'provider',...extra});
export const catalogue:Catalog={provider:'openrouter',credential_id:'c',defaults:{},models:[
 model('zeta/last'),model('openai/gpt-oss-120b:nitro'),model('alpha/first'),model('alpha/free:free'),
 model('old/deprecated',{deprecated:true}),model('old/expired',{expiration_date:'2026-01-01'}),
 model('unknown',{structured_output:null}),model('incompatible',{structured_output:false}),
]};
it('FR-UI-01 versioned recommendations intersect provider metadata without inventing support',()=>{
 expect(compatibleModels(catalogue,false).map(m=>m.id)).toEqual(['openai/gpt-oss-120b:nitro']);
 expect(compatibleModels({...catalogue,provider:'custom'},false)).toEqual([]);
 expect(compatibleModels({...catalogue,models:[model('openai/gpt-oss-120b:nitro',{structured_output:null})]},false)).toEqual([]);
});
it('FR-UI-01 compatible models exclude free, deprecated, expired and unknown and sort by provider/name',()=>{
 expect(compatibleModels(catalogue,true,new Date('2026-10-23T00:00:00Z')).map(m=>m.id)).toEqual(['alpha/first','openai/gpt-oss-120b:nitro','zeta/last']);
});
it('FR-UI-01 model details use catalogue prices and context, preserving unknown values',()=>{
 expect(modelDetail(model('priced'))).toContain('input: $1 / million tokens · output: $2 / million tokens · context: 32,768 tokens');
 const detail=modelDetail(model('unknown',{pricing:{prompt:'not-a-number',completion:-1},context_length:null}));
 expect(detail).toContain('input: unavailable');expect(detail).toContain('output: unavailable');expect(detail).toContain('context: unknown');expect(detail).not.toContain('NaN');
});
