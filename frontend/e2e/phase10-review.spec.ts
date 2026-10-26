import {mkdir} from 'node:fs/promises';
import {expect,test} from '@playwright/test';
import {pendingPackage,submit} from './support/flow';

test('FR-UI-06 FR-UI-07 UC-08 approval categories settle controls and restore download',async({page})=>{
  await page.setViewportSize({width:1280,height:800});
  const id=await submit(page);await pendingPackage(page,id);
  await page.getByLabel('Decision',{exact:true}).selectOption('approve');
  await expect(page.getByRole('option',{name:'accepted risk',exact:true})).toHaveCount(1);
  await expect(page.getByRole('option',{name:'too expensive',exact:true})).toHaveCount(0);
  await page.getByLabel('Reason category',{exact:true}).selectOption('accepted_risk');
  await page.getByLabel('Decision reason').fill('Synthetic defence fixture: accept the documented validation risk.');
  await page.getByRole('button',{name:'Approve',exact:true}).click();
  await expect(page.locator('.badge.engineer-approved')).toHaveText('engineer approved');
  await expect(page.locator('.badge.engineer-approved .codicon-person')).toHaveCount(1);
  for(const name of ['Approve','Retry with feedback','Reject'])await expect(page.getByRole('button',{name,exact:true})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Download ZIP',exact:true})).toBeEnabled();
  await expect(page.getByLabel('Recorded decision')).toContainText('accepted risk');
  await expect(page.getByRole('heading',{name:'Share a lesson',exact:true})).toBeVisible();
  await mkdir('../docs/evals/phase10-ui',{recursive:true});
  for(const colorScheme of ['light','dark'] as const){
    await page.emulateMedia({colorScheme});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await page.screenshot({path:`../docs/evals/phase10-ui/approved-${colorScheme}.png`,animations:'disabled'});
  }
});
