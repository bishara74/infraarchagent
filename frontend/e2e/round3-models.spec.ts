import {expect,test} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
import {USERNAME,PASSWORD,originHeaders} from './support/flow';
import type {Catalog} from '../src/api/types';

test('FR-UI-01 FR-P-04 routing metadata, inherited effort, aliases, compact options and retry',async({page})=>{
 await page.setViewportSize({width:1280,height:800});await page.goto('/login');await page.getByLabel('Username',{exact:true}).fill(USERNAME);await page.getByLabel('Password',{exact:true}).fill(PASSWORD);await page.getByRole('button',{name:'Log in',exact:true}).click();await expect(page).toHaveURL(/\/$/);
 const created=await(await page.request.post('/api/providers',{headers:originHeaders,data:{provider:'openrouter',label:'Round3 mock',api_key:'phase9j-round3-synthetic-key'}})).json();expect((await page.request.post(`/api/providers/${created.id}/default`,{headers:originHeaders})).ok()).toBe(true);
 const actual=await(await page.request.get('/api/models')).json() as Catalog;
 const base=actual.models.find(m=>m.id==='openai/gpt-oss-120b:nitro')!;expect(base).toBeTruthy();
 const catalog={...actual,resolution_context:{provider:'openai',model:base.id,thinking_mode:'low',fixer_provider:null,fixer_model:null,fixer_thinking_mode:null},models:[{...base,id:'openai/gpt-oss-120b'}, {...base,id:'~moving-latest',name:'Moving fixture'}]};
 let missing=false;await page.route('**/api/models*',route=>route.fulfill({json:missing&&!route.request().url().includes('refresh=true')?{...catalog,status:'unavailable',models:[]}:catalog}));
 const prefs=await(await page.request.get('/api/me/preferences')).json();await page.request.put('/api/me/preferences',{headers:originHeaders,data:{revision:prefs.revision,data:{}}});await page.goto('/');await page.locator('details.config>summary').click();
 await expect(page.getByLabel('Architect thinking',{exact:true})).toHaveValue('low');await expect(page.getByLabel('Architect thinking',{exact:true})).toContainText('low (server default)');
 const combo=page.getByRole('combobox',{name:'Architect model',exact:true});await combo.click();const recommended=page.getByRole('option',{name:/gpt-oss-120b:nitro.*tested/});await expect(recommended).toBeVisible();await expect(recommended).toContainText('32,768');expect((await recommended.boundingBox())!.height).toBe(80);await expect(page.getByRole('option',{name:/Moving fixture/})).toHaveCount(0);
 await mkdir('../docs/evals/phase9j-ui/round3',{recursive:true});await page.screenshot({path:'../docs/evals/phase9j-ui/round3/model-routing.png'});await recommended.click();
 await page.getByRole('checkbox',{name:'Show all compatible models'}).check();await combo.click();await expect(page.getByRole('option',{name:/Moving fixture/})).toContainText('alias — changes over time');await combo.press('Escape');
 await page.getByLabel('Infrastructure description').fill('Create an AWS web service using Terraform.');const request=page.waitForRequest(r=>r.url().endsWith('/api/pipeline/run')&&r.method()==='POST');await page.getByRole('button',{name:'Generate',exact:true}).click();expect((await request).postDataJSON().config.agent_models.architect.model).toBe('openai/gpt-oss-120b:nitro');await expect(page).toHaveURL(/\/runs\//);
 missing=true;await page.goto('/settings/models');await expect(page.getByText("We couldn't load details for this model. It will still run with the server's settings.").first()).toBeVisible();await page.screenshot({path:'../docs/evals/phase9j-ui/round3/model-retry.png'});await page.getByRole('button',{name:'Retry',exact:true}).first().click();await expect(page.getByText("We couldn't load details for this model. It will still run with the server's settings.")).toHaveCount(0);
});
