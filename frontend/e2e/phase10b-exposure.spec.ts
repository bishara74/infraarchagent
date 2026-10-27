import {expect,test} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
import {submit,pendingPackage,results} from './support/flow';

test('FR-S-07 FR-UI-03 FR-UI-05 FR-UI-07 retained plan-conflicting finding is visible in overview, Findings and Review',async({page})=>{
 const id=await submit(page);await pendingPackage(page,id);const snapshot=await results(page,id);
 const item=snapshot.packages.find(row=>row.variant==='security')!;
 item.plan_conflicts=[{service:'edge',resource:'aws_lb.edge',property:'exposure',expected:'public',assessment:'regression',rule_id:'AWS-0053',file_path:'terraform/main.tf'}];
 item.review_reasons.push('plan_conformance_conflict');
 item.security_report={sessions:[],final:{outcome:'exhausted',remaining_blocking:[{rule_id:'AWS-0053',resource:'aws_lb.edge',file_path:'terraform/main.tf',severity:'HIGH',message:'Load balancer is exposed to the internet'}]}};
 await page.route(`**/api/pipeline/${id}/results`,route=>route.fulfill({json:snapshot}));
 const explanation="Kept open: required by the plan's internet exposure.";
 await page.goto(`/runs/${id}/compare`);await expect(page.getByRole('article',{name:'security variant'}).getByText(explanation,{exact:true})).toBeVisible();
 await page.goto(`/runs/${id}/packages/security?tab=findings`);await expect(page.getByText(explanation,{exact:true})).toBeVisible();
 await page.getByRole('tab',{name:'Review',exact:true}).click();await expect(page.getByText(explanation,{exact:true})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Pending review',exact:true})).toBeVisible();
 await page.setViewportSize({width:1280,height:800});
 await expect(page.getByRole('button',{name:'Approve',exact:true})).toBeInViewport();
 await mkdir('../docs/evals/phase10b-verification/ui',{recursive:true});
 await page.screenshot({path:'../docs/evals/phase10b-verification/ui/plan-conflict-review.png',animations:'disabled'});
});
