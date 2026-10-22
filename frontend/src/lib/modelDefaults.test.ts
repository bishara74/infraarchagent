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

import parity from '../test/fixtures/model-defaults.json';
it.each(parity)('FR-P-04 shared backend resolution fixture: $name',testCase=>{
 const settings=testCase.settings;
 const fixtureCatalog={...catalog,credential_id:testCase.credential_id,resolution_context:{provider:settings.llm_provider,model:settings.llm_model,thinking_mode:settings.llm_reasoning_effort,fixer_provider:null,fixer_model:settings.security_fix_model??null,fixer_thinking_mode:settings.security_fix_reasoning_effort??null}} as Catalog;
 for(const [role,expected] of Object.entries(testCase.expected))expect(modelDefault(role,fixtureCatalog,{...testCase.saved,...testCase.personal} as never,testCase.config.agent_models as never,testCase.config as never)).toEqual(expected);
});
