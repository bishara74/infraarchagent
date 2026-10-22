import {expect,it} from 'vitest';
import type {DeploymentPlan} from '../api/types';
import fixture from '../test/fixtures/pending-results.json';
import {architectureSummary} from './architectureSummary';
it('FR-UI-03 subtitles report only available structured plan facts',()=>{
 expect(architectureSummary(null)).toBe('');
 const plan=structuredClone(fixture.plan) as DeploymentPlan;plan.network.private_services=['db'];plan.network.public_services=[];plan.storage=[];
 expect(architectureSummary(plan)).toBe('Private services planned');
 plan.network.private_services=[];expect(architectureSummary(plan)).toBe('');
});
