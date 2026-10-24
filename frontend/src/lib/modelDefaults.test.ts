import {expect,it} from 'vitest';
import type {Catalog} from '../api/types';
import {choiceLabel,defaultLabel,modelDefault} from './modelDefaults';
const environment={model:'openai/gpt-oss-120b:nitro',thinking_mode:'low' as const,provider:'openai' as const};
const catalog:Catalog={provider:'openrouter',credential_id:null,defaults:{},models:[],environment_defaults:{architect:environment,generator_cost:environment,generator_performance:environment,generator_security:environment,fixer:environment}};
it('FR-P-04 saved personal Gemini default and explicit draft precede environment without inheriting thinking',()=>{
 const personal={architect:{model:'google/gemini-3.8-flash:batch',thinking_mode:null}};
 expect(defaultLabel('architect',catalog,{personal})).toBe('google/gemini-3.8-flash:batch · provider default (from your defaults)');
 expect(modelDefault('architect',catalog,{personal,run:{architect:{model:'openai/gpt-oss-120b'}}})?.model).toBe('openai/gpt-oss-120b');
 expect(defaultLabel('architect',catalog,{})).toBe('openai/gpt-oss-120b:nitro · low (server default)');
});
it('FR-P-04 generators resolve role overrides before group and environment defaults',()=>{
 expect(defaultLabel('generators',catalog,{})).toBe('openai/gpt-oss-120b:nitro · low (server default)');
 const defaults={generators:{model:'group',thinking_mode:null},generator_cost:{model:'cost',thinking_mode:'off' as const}};
 expect(modelDefault('generator_cost',catalog,{admin:defaults})).toEqual(defaults.generator_cost);
 expect(modelDefault('generator_security',catalog,{admin:defaults})).toEqual(defaults.generators);
 expect(defaultLabel('generators',catalog,{admin:defaults})).toContain('cost: cost · off');
 expect(choiceLabel(undefined)).toBe('unavailable');
});

import parity from '../test/fixtures/model-defaults.json';
it.each(parity)('FR-P-04 shared backend resolution fixture: $name',testCase=>{
 const settings=testCase.settings;
 const fixtureCatalog={...catalog,credential_id:testCase.credential_id,resolution_context:{provider:settings.llm_provider,model:settings.llm_model,thinking_mode:settings.llm_reasoning_effort,fixer_provider:null,fixer_model:settings.security_fix_model??null,fixer_thinking_mode:settings.security_fix_reasoning_effort??null}} as Catalog;
 for(const [role,expected] of Object.entries(testCase.expected))expect(modelDefault(role,fixtureCatalog,{admin:testCase.saved,personal:testCase.personal,run:testCase.config.agent_models} as never,testCase.config as never)).toEqual(expected);
});

import matrix from '../test/fixtures/model-tiers.json';
import {generatorRoles,resolveModel,sourceLabel,type ModelLayers} from './modelDefaults';
it.each(matrix.flatMap(testCase=>generatorRoles.map(role=>({...testCase,role}))))('FR-UI-01 FR-P-04 tier/group matrix $name $role',testCase=>{
 const fixtureCatalog={...catalog,resolution_context:{provider:'openai',model:'environment',thinking_mode:'low',fixer_provider:null,fixer_model:null,fixer_thinking_mode:null}} as Catalog;
 const result=resolveModel(testCase.role,fixtureCatalog,testCase.layers as ModelLayers);
 expect(result).toEqual({choice:testCase.expected[testCase.role],source:testCase.source});
 expect(defaultLabel(testCase.role,fixtureCatalog,testCase.layers as ModelLayers)).toContain(sourceLabel(result!.source));
});

it.each([null,'saved-credential'])('FR-P-04 Architect override never changes other roles with credential %s',credential_id=>{
 const fixtureCatalog={...catalog,credential_id,resolution_context:{provider:'openai',model:environment.model,thinking_mode:'low',fixer_provider:null,fixer_model:'separate-fixer',fixer_thinking_mode:'high'}} as Catalog;
 const run={architect:{model:'anthropic/claude-opus-4.5',thinking_mode:null}};
 for(const role of [...generatorRoles,'fixer'])expect(resolveModel(role,fixtureCatalog,{run})).toEqual(resolveModel(role,fixtureCatalog));
 expect(resolveModel('architect',fixtureCatalog,{run})).toEqual({choice:run.architect,source:'run'});
});

it('FR-UI-01 a missing role default stays unavailable despite an Architect selection',()=>{
 const fixtureCatalog={...catalog,credential_id:'saved',resolution_context:{provider:'stub',model:null,thinking_mode:null,fixer_provider:null,fixer_model:null,fixer_thinking_mode:null}} as Catalog;
 expect(resolveModel('generator_cost',fixtureCatalog,{run:{architect:{model:'chosen'}}})).toBeUndefined();
 expect(defaultLabel('generators',fixtureCatalog,{run:{architect:{model:'chosen'}}})).toBe('unavailable');
});
