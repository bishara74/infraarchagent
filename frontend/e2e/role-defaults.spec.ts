import {expect,test,type Page} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
import {USERNAME,PASSWORD,originHeaders} from './support/flow';

const environment='openai/gpt-oss-120b:nitro';
const architect='anthropic/claude-opus-4.5';
const evidence='../docs/evals/phase9j-ui/role-defaults';
async function prepare(page:Page){
 await mkdir(evidence,{recursive:true});
 await page.goto('/login');await page.getByLabel('Username',{exact:true}).fill(USERNAME);await page.getByLabel('Password',{exact:true}).fill(PASSWORD);await page.getByRole('button',{name:'Log in',exact:true}).click();await expect(page).toHaveURL(/\/$/);
 const created=await(await page.request.post('/api/providers',{headers:originHeaders,data:{provider:'openrouter',label:'Role defaults mock',api_key:'role-defaults-synthetic-provider-key'}})).json();
 expect((await page.request.post(`/api/providers/${created.id}/default`,{headers:originHeaders})).ok()).toBe(true);
 expect((await page.request.put('/api/models/defaults',{headers:originHeaders,data:{defaults:{},static_models:[]}})).ok()).toBe(true);
 const prefs=await(await page.request.get('/api/me/preferences')).json();
 expect((await page.request.put('/api/me/preferences',{headers:originHeaders,data:{revision:prefs.revision,data:{}}})).ok()).toBe(true);
 await page.goto('/');await page.locator('details.config>summary').click();
}

test('FR-UI-01 FR-P-04 Architect-only choice keeps defaults, sparse submission and actual resolved roles independent',async({page})=>{
 await page.setViewportSize({width:1280,height:800});const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 await prepare(page);
 const generators=page.getByRole('combobox',{name:'Generators model',exact:true});const fixer=page.getByRole('combobox',{name:'Fixer model',exact:true});
 await expect(generators).toHaveValue(`Use default — ${environment} · low (server default)`);
 await expect(fixer).toHaveValue(`Use default — ${environment} · low (server default)`);
 await page.getByRole('checkbox',{name:'Show all compatible models'}).check();
 const combo=page.getByRole('combobox',{name:'Architect model',exact:true});await combo.fill(architect);await combo.press('ArrowDown');await combo.press('Enter');await expect(combo).toHaveValue(/Claude Opus/);await expect(combo).toBeFocused();
 await expect(page.getByText('Architect: from this run',{exact:true})).toBeVisible();
 await expect(generators).toHaveValue(`Use default — ${environment} · low (server default)`);await expect(fixer).toHaveValue(`Use default — ${environment} · low (server default)`);
 await expect(page.getByLabel('Generators thinking',{exact:true})).toHaveValue('low');
 await mkdir(evidence,{recursive:true});await page.locator('.model-choice').first().evaluate(element=>element.scrollIntoView({block:'start'}));await page.screenshot({path:`${evidence}/architect-only.png`});
 await combo.click();await combo.press('Home');await combo.press('Enter');await expect(page.getByText('Architect: server default',{exact:true})).toBeVisible();
 await combo.fill(architect);await combo.press('ArrowDown');await combo.press('Enter');
 await page.getByLabel('Infrastructure description').fill('Create an AWS web service using Terraform.');
 const submitted=page.waitForRequest(request=>request.url().endsWith('/api/pipeline/run')&&request.method()==='POST');
 await page.getByRole('button',{name:'Generate',exact:true}).click();
 expect((await submitted).postDataJSON().config.agent_models).toEqual({architect:{model:architect}});
 await expect(page).toHaveURL(/\/runs\/[a-f0-9-]+$/);const id=page.url().split('/').at(-1)!;
 const result=await(await page.request.get(`/api/pipeline/${id}/results`)).json();
 expect(result.run.agent_models.architect.model).toBe(architect);
 for(const role of ['generator_cost','generator_performance','generator_security','fixer'])expect(result.run.agent_models[role].model).toBe(environment);
 await expect(page.getByRole('link',{name:'View results'})).toBeVisible();
 expect(errors).toEqual([]);
});

test('FR-UI-01 FR-P-04 personal group beats administrator specificity and Settings identify their tier',async({page})=>{
 await page.setViewportSize({width:1280,height:800});await prepare(page);
 expect((await page.request.put('/api/models/defaults',{headers:originHeaders,data:{defaults:{generator_cost:{model:architect,thinking_mode:null}},static_models:[]}})).ok()).toBe(true);
 const prefs=await(await page.request.get('/api/me/preferences')).json();
 expect((await page.request.put('/api/me/preferences',{headers:originHeaders,data:{revision:prefs.revision,data:{role_defaults:{generators:{model:environment,thinking_mode:'low'}},draft_config:{agent_models:{generator_security:{model:architect,thinking_mode:null}}}}}})).ok()).toBe(true);
 await page.goto('/');await page.locator('details.config>summary').click();
 const group=page.getByRole('combobox',{name:'Generators model',exact:true});
 await expect(group).toHaveValue(/cost: .*from your defaults.*performance: .*from your defaults.*security: .*from this run/);
 await page.locator('details.model-advanced>summary').click();
 await expect(page.getByText('Cost Generator: from your defaults',{exact:true})).toBeVisible();await expect(page.getByText('Security Generator: from this run',{exact:true})).toBeVisible();
 await page.getByText('Security Generator: from this run',{exact:true}).scrollIntoViewIfNeeded();await page.screenshot({path:`${evidence}/per-variant-sources.png`,fullPage:false});
 await page.goto('/settings/models');
 const mine=page.getByRole('heading',{name:'My defaults',exact:true}).locator('..');
 await expect(mine.getByText('Generators: from your defaults',{exact:true})).toBeVisible();
 await mine.evaluate(element=>element.scrollIntoView({block:'start'}));await page.screenshot({path:`${evidence}/personal-settings-sources.png`});
 const admin=page.getByRole('heading',{name:'Administrator defaults',exact:true}).locator('..');
 await admin.locator('details.model-advanced>summary').click();
 await expect(admin.getByText('Cost Generator: from administrator defaults',{exact:true})).toBeVisible();
 await admin.getByText('Cost Generator: from administrator defaults',{exact:true}).scrollIntoViewIfNeeded();await page.screenshot({path:`${evidence}/settings-sources.png`});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 // Leave no configuration that changes later browser scenarios.
 expect((await page.request.put('/api/models/defaults',{headers:originHeaders,data:{defaults:{},static_models:[]}})).ok()).toBe(true);
 const latest=await(await page.request.get('/api/me/preferences')).json();await page.request.put('/api/me/preferences',{headers:originHeaders,data:{revision:latest.revision,data:{}}});
});
