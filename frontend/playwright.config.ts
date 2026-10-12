import { defineConfig } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('..',import.meta.url));
const database=process.env.TEST_DATABASE_URL;
const owner=process.env.TEST_MIGRATION_DATABASE_URL;
if(!database||!owner) throw new Error('Export TEST_DATABASE_URL and TEST_MIGRATION_DATABASE_URL for the test database; E2E never loads dotenv.');
if(!database.includes('/infraarch_test')||!owner.includes('/infraarch_test')) throw new Error('E2E requires infraarch_test database URLs.');
const perf=process.argv.some((value,index)=>value==='--grep'&&process.argv[index+1]?.includes('@perf')||value.startsWith('--grep=')&&value.includes('@perf'));
export default defineConfig({
 testDir:'./e2e', timeout:180000, expect:{timeout:90000}, fullyParallel:false, workers:1, retries:0,
 reporter:'list', outputDir:'test-results', grepInvert:perf?undefined:/@perf/,
 globalSetup:'./e2e/support/prerequisites.ts',
 use:{baseURL:'http://127.0.0.1:5173',browserName:'chromium',viewport:{width:1440,height:900},reducedMotion:'reduce',trace:'retain-on-failure'},
 webServer:[
  {command:'make migrate-test && make run',cwd:root,url:'http://127.0.0.1:8000/api/health',timeout:120000,reuseExistingServer:false,
   env:{PYTHONPATH:[path.join(root,'backend/tests/bootstrap'),path.join(root,'backend')].join(path.delimiter),DATABASE_URL:database,MIGRATION_DATABASE_URL:owner,TEST_DATABASE_URL:database,TEST_MIGRATION_DATABASE_URL:owner,LLM_PROVIDER:'stub',LLM_MODEL:'',LLM_API_KEY:'',LLM_BASE_URL:'',LLM_REASONING_EFFORT:'',SECURITY_FIX_PROVIDER:'stub',SECURITY_FIX_MODEL:'',SECURITY_FIX_REASONING_EFFORT:'',PIPELINE_DEMO_SCENARIO:'review',API_KEY:'phase8-e2e-only'}},
  {command:'npm run dev',url:'http://127.0.0.1:5173',timeout:60000,reuseExistingServer:false},
 ],
});
