import {expect,it} from 'vitest';
import type {Catalog} from '../api/types';
import {choiceLabel,defaultLabel,modelDefault} from './modelDefaults';
const environment={model:'openai/gpt-oss-120b:nitro',thinking_mode:'low' as const,provider:'openai' as const};
const catalog:Catalog={provider:'openrouter',credential_id:null,defaults:{},models:[],environment_defaults:{architect:environment,generator_cost:environment,generator_performance:environment,generator_security:environment,fixer:environment}};
it('FR-P-04 saved personal Gemini default and explicit draft precede environment without inheriting thinking',()=>{
 const personal={architect:{model:'google/gemini-3.8-flash:batch',thinking_mode:null}};
 expect(defaultLabel('architect',catalog,personal)).toBe('google/gemini-3.8-flash:batch · provider default');
 expect(modelDefault('architect',catalog,personal,{architect:{model:'openai/gpt-oss-120b'}})?.model).toBe('openai/gpt-oss-120b');
 expect(defaultLabel('architect',catalog,{})).toBe('openai/gpt-oss-120b:nitro · low');
});
it('FR-P-04 generators resolve role overrides before group and environment defaults',()=>{
 expect(defaultLabel('generators',catalog,{})).toBe('openai/gpt-oss-120b:nitro · low');
 const defaults={generators:{model:'group',thinking_mode:null},generator_cost:{model:'cost',thinking_mode:'off' as const}};
 expect(modelDefault('generator_cost',catalog,defaults)).toEqual(defaults.generator_cost);
 expect(modelDefault('generator_security',catalog,defaults)).toEqual(defaults.generators);
 expect(defaultLabel('generators',catalog,defaults)).toContain('cost: cost · off');
 expect(choiceLabel(undefined)).toBe('unavailable');
});
