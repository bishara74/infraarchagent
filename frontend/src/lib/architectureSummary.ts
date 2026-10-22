import type {DeploymentPlan} from '../api/types';
/** Structured plan facts only; the plan is shared, not proof of variant deployment. */
export function architectureSummary(plan:DeploymentPlan|null):string {
 if(!plan)return '';
 const properties=[];
 if(plan.network.private_services.length)properties.push('Private services planned');
 if(plan.network.public_services.length)properties.push('Public services planned');
 if(plan.storage.some(storage=>storage.kind==='relational_db'))properties.push('Relational storage planned');
 else if(plan.storage.some(storage=>storage.kind==='object_storage'))properties.push('Object storage planned');
 return properties.join(' · ');
}
