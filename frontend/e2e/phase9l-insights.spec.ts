import {mkdir} from 'node:fs/promises';
import {expect,test} from '@playwright/test';
import {pendingPackage,results,submit} from './support/flow';

test('FR-UI-07 NFR-01 deterministic feedback insights link to retained decisions',async({page})=>{
  await page.setViewportSize({width:1280,height:800});
  const run=await submit(page);
  await pendingPackage(page,run);
  await page.getByLabel('Reason category',{exact:true}).selectOption('security_concern');
  await page.getByLabel('Decision reason').fill('Browser fixture: retain the remaining blocking evidence.');
  await page.getByRole('button',{name:'Reject',exact:true}).click();
  await page.getByRole('button',{name:'Confirm reject',exact:true}).click();
  await expect(page.getByText('Category: security concern',{exact:true})).toBeVisible();
  const item=(await results(page,run)).packages.find(item=>item.variant==='security')!;
  expect(item.review_decision?.decision_id).toBeTruthy();
  await page.goto(`/settings/review-history?view=insights&decision_id=${item.review_decision!.decision_id}`);
  await expect(page.getByRole('heading',{name:'Feedback insights',exact:true})).toBeVisible();
  await expect(page.getByText('1 of 1 rejected decision has recorded blocking-rule snapshots. 0 unavailable.')).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await mkdir('../docs/evals/phase9l-ui',{recursive:true});
  await page.screenshot({path:'../docs/evals/phase9l-ui/feedback-insights.png',animations:'disabled'});
  await page.getByRole('link',{name:'View 1 decisions: security concern',exact:true}).click();
  await expect(page.getByRole('cell',{name:'Browser fixture: retain the remaining blocking evidence.',exact:true})).toBeVisible();
  await page.screenshot({path:'../docs/evals/phase9l-ui/insight-decision.png',animations:'disabled'});
});
