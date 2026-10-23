import {expect,type Page,type Locator} from '@playwright/test';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import type {ResultsResponse} from '../../src/api/types';
export const API_KEY='phase8-e2e-only';
export const USERNAME='committee';export const PASSWORD='phase9h-browser-password';
export const headers={'X-API-Key':API_KEY};
export const originHeaders={Origin:`http://127.0.0.1:${process.env.INFRAARCH_E2E_FRONTEND_PORT??5173}`};
export async function submit(page:Page){
 await page.goto('/');const status=await (await page.request.get('/api/auth/session')).json();if(!status.authenticated){await page.getByLabel('Username',{exact:true}).fill(USERNAME);await page.getByLabel('Password',{exact:true}).fill(PASSWORD);if(status.setup_required)await page.getByLabel('Confirm password',{exact:true}).fill(PASSWORD);await page.getByRole('button',{name:status.setup_required?'Create admin account':'Log in',exact:true}).click();}
 await expect(page.getByRole('heading',{name:'Generate infrastructure'})).toBeVisible();
 await page.request.post('/api/providers/environment',{headers:originHeaders});const preferences=await(await page.request.get('/api/me/preferences')).json();await page.request.put('/api/me/preferences',{headers:originHeaders,data:{revision:preferences.revision,data:{}}});await page.reload();
 await page.getByLabel('Infrastructure description').fill('Create an AWS web service with Terraform and secure access.');
 const request=page.waitForRequest(request=>request.url().endsWith('/api/pipeline/run')&&request.method()==='POST');await page.getByRole('button',{name:'Generate',exact:true}).click();const submitted=await request;expect(submitted.postDataJSON().config.provider).toBeUndefined();expect(submitted.headers()['x-api-key']).toBeUndefined();expect(await page.evaluate(()=>sessionStorage.getItem('infraarch.apiKey'))).toBeNull();await expect(page).toHaveURL(/\/runs\/[a-f0-9-]+$/);return page.url().split('/').at(-1)!;
}
export async function pendingPackage(page:Page,id:string){await expect(page.getByRole('link',{name:'View results'})).toBeVisible();await page.getByRole('link',{name:'View results'}).click();await expect(page.getByRole('heading',{name:'Select a variant'})).toBeVisible();await page.goto(`/runs/${id}/packages/security?tab=review`);await expect(page.getByRole('heading',{name:'Pending review',exact:true})).toBeVisible();}
export async function results(page:Page,id:string):Promise<ResultsResponse>{const response=await page.request.get(`/api/pipeline/${id}/results`);expect(response.ok()).toBe(true);return await response.json() as ResultsResponse;}
export async function downloadAndCheck(page:Page,id:string,readiness:string,origin:string){
 await expect(page.getByText('Label origin: '+origin,{exact:true})).toBeVisible();
 const data=await results(page,id);const item=data.packages.find(item=>item.variant==='security')!;expect(item.readiness_label).toBe(readiness);expect(item.retry_in_progress).toBe(false);
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download ZIP',exact:true}).click();const zip=await download;expect(await zip.failure()).toBeNull();const filename=await zip.path();expect(filename).toBeTruthy();
 const script=`import json,sys,zipfile\nexpected=json.loads(sys.argv[2])\nwith zipfile.ZipFile(sys.argv[1]) as z:\n names=set(z.namelist())\n assert set(expected).issubset(names)\n extra=names-set(expected)\n assert len(extra)==1 and next(iter(extra)).endswith('INFRAARCHAGENT_READINESS.md')\n for name,content in expected.items(): assert z.read(name).decode()==content\n assert '# '+sys.argv[3].replace('_',' ').upper() in z.read(next(iter(extra))).decode()\n assert 'Label origin: '+sys.argv[4] in z.read(next(iter(extra))).decode()\n`;
 await promisify(execFile)(new URL('../../../backend/.venv/bin/python',import.meta.url).pathname,['-c',script,filename!,JSON.stringify(item.files),readiness,origin]);
}
export async function tabTo(page:Page,target:Locator){for(let i=0;i<60;i++){if(await target.evaluate(element=>element===document.activeElement))return;await page.keyboard.press('Tab');}throw new Error('Keyboard target was not reachable.');}
