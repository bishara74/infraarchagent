import { request } from '@playwright/test';
export default async function prerequisites(){
 const context=await request.newContext();try{
 const response=await context.get(`http://127.0.0.1:${process.env.INFRAARCH_E2E_BACKEND_PORT??8000}/api/health`);const value=await response.json() as {status:string;llm_configured:boolean;scanners:Record<string,{available:boolean}>;validators:Record<string,{available:boolean}>;provider_mirror_present:boolean};
 if(value.status!=='ok'||value.llm_configured||!['checkov','trivy','terraform'].every(tool=>value.scanners[tool]?.available)||!value.validators.terraform?.available||!value.provider_mirror_present)throw new Error('E2E requires the test database, stub-only settings, installed Checkov/Trivy/Terraform and the offline Terraform provider mirror.');
 }finally{await context.dispose();}
}
