import {render,screen} from '@testing-library/react';
import {expect,it} from 'vitest';
import pending from '../test/fixtures/pending-results.json';
import type {PackageResult,PlanConflict} from '../api/types';
import {PlanConformanceNotice} from './PlanConformanceNotice';
const conflict:PlanConflict={service:'edge',resource:'aws_lb.edge',property:'exposure',expected:'public',assessment:'regression',rule_id:'AWS-0053',file_path:'terraform/main.tf'};
it('FR-S-07 FR-UI-05 explains current public, private and unknown conflicts without inventing legacy evidence',()=>{
 const item={...pending.packages[0],plan_conflicts:[conflict]} as PackageResult;
 const view=render(<PlanConformanceNotice item={item}/>);
 expect(screen.getByText("Kept open: required by the plan's internet exposure.")).toBeVisible();
 view.rerender(<PlanConformanceNotice item={{...item,plan_conflicts:[{...conflict,expected:'private'}]}}/>);
 expect(screen.getByText("Kept open: required by the plan's private exposure.")).toBeVisible();
 view.rerender(<PlanConformanceNotice item={{...item,plan_conflicts:[{...conflict,assessment:'unknown'}]}}/>);
 expect(screen.getByText(/could not be verified/)).toBeVisible();
 view.rerender(<PlanConformanceNotice item={{...item,plan_conflicts:undefined}}/>);expect(view.container).toBeEmptyDOMElement();
});
it('FR-UI-05 only annotates the exact finding linked by the backend',()=>{
 const item={...pending.packages[0],plan_conflicts:[conflict]} as PackageResult;
 const view=render(<PlanConformanceNotice item={item} finding={{...conflict,rule_id:'OTHER'}}/>);expect(view.container).toBeEmptyDOMElement();
 view.rerender(<PlanConformanceNotice item={item} finding={{...conflict}}/>);expect(screen.getByText(/Kept open/)).toBeVisible();
});
