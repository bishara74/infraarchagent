import {expect,type Page,type Locator} from '@playwright/test';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import type {ResultsResponse} from '../../src/api/types';
export const API_KEY='phase8-e2e-only';
export const headers={'X-API-Key':API_KEY};
export async function submit(page:Page){
 await page.goto('/');await page.getByText('Configuration options',{exact:true}).click();await page.getByLabel('LLM provider').selectOption('stub');await page.getByLabel('API key',{exact:true}).fill(API_KEY);await page.getByLabel('Infrastructure description').fill('Create an AWS web service with Terraform and secure access.');
 const request=page.waitForRequest(request=>request.url().endsWith('/api/pipeline/run')&&request.method()==='POST');await page.getByRole('button',{name:'Generate',exact:true}).click();expect((await request).postDataJSON().config.provider).toBe('stub');await expect(page).toHaveURL(/\/runs\/[a-f0-9-]+$/);return page.url().split('/').at(-1)!;
}
export async function pendingPackage(page:Page,id:string){await expect(page.getByRole('link',{name:'View results'})).toBeVisible();await page.getByRole('link',{name:'View results'}).click();await expect(page.getByRole('heading',{name:'Select a variant'})).toBeVisible();await page.goto(`/runs/${id}/packages/security`);await expect(page.getByRole('heading',{name:'Pending review',exact:true})).toBeVisible();}
export async function results(page:Page,id:string):Promise<ResultsResponse>{const response=await page.request.get(`/api/pipeline/${id}/results`,{headers});expect(response.ok()).toBe(true);return await response.json() as ResultsResponse;}
export async function downloadAndCheck(page:Page,id:string,readiness:string,origin:string){
 await expect(page.getByText('Label origin: '+origin,{exact:true})).toBeVisible();
 const data=await results(page,id);const item=data.packages.find(item=>item.variant==='security')!;expect(item.readiness_label).toBe(readiness);expect(item.retry_in_progress).toBe(false);
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download ZIP',exact:true}).click();const zip=await download;expect(await zip.failure()).toBeNull();const filename=await zip.path();expect(filename).toBeTruthy();
 const script=`import json,sys,zipfile\nexpected=json.loads(sys.argv[2])\nwith zipfile.ZipFile(sys.argv[1]) as z:\n names=set(z.namelist())\n assert set(expected).issubset(names)\n extra=names-set(expected)\n assert len(extra)==1 and next(iter(extra)).endswith('INFRAARCHAGENT_READINESS.md')\n for name,content in expected.items(): assert z.read(name).decode()==content\n assert '# '+sys.argv[3].replace('_',' ').upper() in z.read(next(iter(extra))).decode()\n assert 'Label origin: '+sys.argv[4] in z.read(next(iter(extra))).decode()\n`;
 await promisify(execFile)(new URL('../../../backend/.venv/bin/python',import.meta.url).pathname,['-c',script,filename!,JSON.stringify(item.files),readiness,origin]);
}
export async function tabTo(page:Page,target:Locator){for(let i=0;i<60;i++){if(await target.evaluate(element=>element===document.activeElement))return;await page.keyboard.press('Tab');}throw new Error('Keyboard target was not reachable.');}
