import {expect as baseExpect,test,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {mkdir} from 'node:fs/promises';
const pending=JSON.parse(readFileSync(new URL('../src/test/fixtures/pending-results.json',import.meta.url),'utf8'));
const expect=baseExpect.configure({timeout:10000});
test.describe.configure({timeout:60000});
test.use({viewport:{width:1280,height:800}});
import {controls,detail} from '../src/test/fixtures/lessons';

async function mockApp(page:Page,{server=true,own=false,filtered=false,status='proposed'}={}){
 await page.route('**/api/**',route=>new URL(route.request().url()).pathname.startsWith('/api/')?route.fulfill({json:route.request().url().includes('/events')?{events:[],has_more:false}:{}}):route.fallback());
 const account={id:own?'reviewer':'phase9m-admin',username:'phase9m-admin',role:'admin'};
 await page.route('**/api/auth/session',route=>route.fulfill({json:{auth_required:true,authenticated:true,mode:'account',user:account}}));
 await page.route('**/api/me/preferences',route=>route.fulfill({json:{revision:1,data:{}}}));
 await page.route('**/api/me/recent-runs',route=>route.fulfill({json:[]}));
 await page.route('**/api/models/defaults',route=>route.fulfill({json:{defaults:{},static_models:[]}}));
 await page.route('**/api/models',route=>route.fulfill({json:{provider:'stub',credential_id:null,models:[],defaults:{}}}));
 await page.route('**/api/pipeline/**/results',route=>route.fulfill({json:pending}));
 await page.route('**/api/pipeline/**/stream',route=>route.fulfill({contentType:'text/event-stream',body:''}));
 await page.route('**/api/lessons/control',route=>route.fulfill({json:{...controls,server_enabled:server}}));
 await page.route('**/api/lessons?*',route=>route.fulfill({json:{items:[{...detail.lesson,status}],total:1,page:1,page_size:25}}));
 await page.route(`**/api/lessons/${detail.lesson.id}`,route=>route.fulfill({json:{...detail,lesson:{...detail.lesson,status},preview:{...detail.preview,filter_result:{version:'2',passed:!filtered,reasons:filtered?[{id:'code',message:'Remove code syntax.'}]:[]}}}}));
 await page.route(`**/api/lessons/${detail.lesson.lesson_id}/versions*`,route=>route.fulfill({json:{items:[detail.lesson],total:1,page:1,page_size:25}}));
}

async function checkGate(page:Page,name:string,selector='button'){
 const control=selector==='button'?page.getByRole('button',{name,exact:true}):page.getByLabel(name,{exact:true}).first();
 await expect(control).toBeDisabled();
 const gate=control.locator('xpath=ancestor::*[contains(concat(" ",normalize-space(@class)," ")," action-gate ")][1]');
 await expect(gate).toHaveAttribute('aria-describedby',/.+/);
 const help=gate.locator(':scope > .action-gate-help');
 await gate.hover();await expect(help).toBeVisible();expect((await help.innerText()).length).toBeGreaterThan(30);const bounds=await help.boundingBox();expect(bounds!.y).toBeGreaterThanOrEqual(0);expect(bounds!.y+bounds!.height).toBeLessThanOrEqual(await page.evaluate(()=>innerHeight));
 await gate.focus();await expect(gate).toBeFocused();await expect(help).toBeVisible();
 await gate.press('Escape');await gate.click({position:{x:2,y:2}});await expect(help).toBeVisible();
 await expect(gate.getByRole('status')).not.toBeEmpty();
}

test('FR-UI-03/06 unavailable downloads and proposal expose reasons and review links',async({page})=>{
 await mockApp(page);const mutations:string[]=[];page.on('request',r=>{if(r.method()!=='GET'&&!r.url().includes('/api/me/'))mutations.push(r.url());});
 await page.route('**/api/pipeline/**/results',route=>route.fulfill({json:{...pending,run:{...pending.run,status:'running'}}}));
 await page.addInitScript(()=>sessionStorage.setItem('infraarch.activeRun','run'));
 await page.goto('/');await checkGate(page,'Generate');
 await page.goto('/runs/run');await checkGate(page,'View results');
 await page.route('**/api/pipeline/**/results',route=>route.fulfill({json:pending}));
 await page.goto('/runs/run/compare');await checkGate(page,'Download all three');
 const security=page.getByRole('article',{name:'security variant'});await expect(security.getByRole('button',{name:'Download this variant'})).toBeDisabled();
 const download=security.getByRole('button',{name:'Download this variant'});await download.locator('..').focus();await expect(download.locator('..').locator('.action-gate-help')).toBeVisible();
 await expect(page.getByRole('link',{name:'Review security',exact:true})).toHaveAttribute('href','/runs/run/packages/security?tab=review');
 await mkdir('../docs/evals/phase9m-verification',{recursive:true});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../docs/evals/phase9m-verification/ui-download-reasons.png',animations:'disabled'});
 await page.getByRole('link',{name:'Review security',exact:true}).click();await checkGate(page,'Download ZIP');await checkGate(page,'Propose a lesson');expect(mutations).toEqual([]);
});

for(const state of [{name:'server gate',server:false,own:false,filtered:false,status:'proposed'},{name:'four eyes',server:true,own:true,filtered:false,status:'proposed'},{name:'filter',server:true,own:false,filtered:true,status:'proposed'},{name:'retired',server:true,own:false,filtered:false,status:'retired'}]){
 test(`FR-UI-07 lesson ${state.name} gates explain their unchanged conditions`,async({page})=>{
  await mockApp(page,state);const mutations:string[]=[];page.on('request',r=>{if(r.method()!=='GET'&&!r.url().includes('/api/me/'))mutations.push(r.url());});
  await page.goto(`/settings/lessons?lesson=${detail.lesson.id}`);
  const dialog=page.getByRole('dialog',{name:'Lesson v1',exact:true});await expect(dialog).toBeVisible();
  if(state.own||state.filtered||state.status==='retired')await checkGate(page,'Approve lesson');
  if(!state.own)await checkGate(page,'Propose new version');
  if(state.status==='retired')await checkGate(page,'Reject lesson');
  await checkGate(page,'Retire lesson');await checkGate(page,'Previous versions');await checkGate(page,'Next versions');
  await dialog.getByRole('button',{name:'Close lesson'}).click();
  if(!state.server)await checkGate(page,'Use approved lessons','input');
  await checkGate(page,'Previous');await checkGate(page,'Next');expect(mutations).toEqual([]);
 });
}

test('FR-UI-01 provider/model unavailable controls remain explained without mutation',async({page})=>{
 await mockApp(page);await page.route('**/api/providers',route=>route.fulfill({json:{storage_enabled:false,default_credential_id:'revoked',credentials:[{id:'revoked',provider:'openai',label:'Revoked synthetic key',last4:'test',revoked:true,base_url:''}]}}));
 const mutations:string[]=[];page.on('request',r=>{if(r.method()!=='GET'&&!r.url().includes('/api/me/'))mutations.push(r.url());});
 await page.goto('/settings/provider');await checkGate(page,'Save and use provider');
 const tests=page.getByRole('button',{name:'Test',exact:true});await expect(tests).toHaveCount(2);
 for(const control of await tests.all()){await expect(control).toBeDisabled();await control.locator('..').focus();await expect(control.locator('..').locator('.action-gate-help')).toBeVisible();}
 await checkGate(page,'Use');await checkGate(page,'Revoke');
 await page.goto('/settings/models');await checkGate(page,'Architect thinking','select');await checkGate(page,'Generators thinking','select');await checkGate(page,'Fixer thinking','select');expect(mutations).toEqual([]);
});

async function checkVisibleGates(page:Page){
 const dialog=page.getByRole('dialog');const root=await dialog.count()?dialog.last():page.locator('main');
 const gates=root.locator('.action-gate');const count=await gates.count();expect(count).toBeGreaterThan(0);
 for(let i=0;i<count;i++){
  const gate=gates.nth(i);if(!await gate.isVisible())continue;
  const hint=gate.locator(':scope > .action-gate-help');await gate.hover();await expect(hint).toBeVisible();
  await gate.focus();await expect(gate).toBeFocused();await gate.click({position:{x:2,y:2}});await expect(hint).toBeVisible();
  expect((await hint.innerText()).length).toBeGreaterThan(30);
 }
}

for(const kind of ['login','account','users','review','runtime','export'] as const){
 test(`FR-UI-01/07 ${kind} busy controls remain disabled and explain recovery`,async({page})=>{
  await mockApp(page);let held:import('@playwright/test').Route|undefined;
  const hold=async(pattern:string,verb:string)=>page.route(pattern,route=>{if(route.request().method()===verb){held=route;}else void route.fallback();});
  if(kind==='login'){
   await page.route('**/api/auth/session',route=>route.fulfill({json:{auth_required:true,authenticated:false,mode:'account'}}));
   await hold('**/api/auth/login','POST');await page.goto('/login');await page.getByLabel('Username',{exact:true}).fill('synthetic-user');await page.getByLabel('Password',{exact:true}).fill('synthetic-password-only');await page.getByRole('button',{name:'Log in',exact:true}).click();
  }else if(kind==='account'){
   await hold('**/api/auth/password','POST');await page.goto('/settings/account');await page.getByLabel('Current password',{exact:true}).fill('synthetic-current');await page.getByLabel('New password',{exact:true}).fill('synthetic-new-password');await page.getByLabel('Confirm password',{exact:true}).fill('synthetic-new-password');await page.getByRole('button',{name:'Change password',exact:true}).click();
  }else if(kind==='users'){
   await page.route('**/api/auth/users',route=>route.request().method()==='POST'?(held=route,undefined):route.fulfill({json:[{id:'reviewer',username:'Synthetic reviewer',role:'reviewer',disabled:false,created_at:'2026-10-26T00:00:00Z',last_login_at:null}]}));
   await page.goto('/settings/users');const form=page.locator('.create-reviewer');await form.getByLabel('Username',{exact:true}).fill('new-reviewer');await form.getByLabel('New password',{exact:true}).fill('synthetic-password');await form.getByLabel('Confirm password',{exact:true}).fill('synthetic-password');await form.getByRole('button',{name:'Create reviewer'}).click();
  }else if(kind==='review'){
   const fixture=structuredClone(pending);const item=fixture.packages.find((item:{variant:string})=>item.variant==='security');item.retry_targets=[];item.files=Object.fromEntries(['main','a','b','c','d','e'].map(name=>[`terraform/${name}.tf`,'# synthetic']));
   await page.route('**/api/pipeline/**/results',route=>route.fulfill({json:fixture}));
   await hold('**/api/pipeline/**/review','POST');await page.goto('/runs/run/packages/security?tab=review');await page.getByRole('button',{name:'Retry with feedback',exact:true}).click();
   for(const name of ['main','a','b','c','d'])await page.getByRole('checkbox',{name:`terraform/${name}.tf`,exact:true}).check();
   await checkGate(page,'terraform/e.tf','input');await page.getByRole('button',{name:'Submit retry',exact:true}).click();
  }else if(kind==='runtime'){
   await hold('**/api/lessons/control','PUT');await page.goto('/settings/lessons');await page.getByRole('checkbox',{name:'Use approved lessons',exact:true}).click();
  }else{
   await page.route('**/api/reviews/history?*',route=>route.fulfill({json:{items:[],total:0,page:1,page_size:25,filters:{}}}));await hold('**/api/reviews/history/export?*','GET');await page.goto('/settings/review-history');await page.getByRole('button',{name:'Export CSV'}).click();
  }
  await expect.poll(()=>!!held).toBe(true);const requests:string[]=[];page.on('request',request=>{if(request.method()!=='GET'&&!request.url().includes('/api/me/'))requests.push(request.url());});
  await checkVisibleGates(page);expect(requests).toEqual([]);await held!.abort();
 });
}
