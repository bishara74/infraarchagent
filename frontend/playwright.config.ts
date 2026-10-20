import { defineConfig } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { assertTestDatabases } from './e2e/support/testDatabase';
const root=fileURLToPath(new URL('..',import.meta.url));
const [database,owner]=assertTestDatabases(process.env.TEST_DATABASE_URL,process.env.TEST_MIGRATION_DATABASE_URL);
const perf=process.argv.some((value,index)=>value==='--grep'&&process.argv[index+1]?.includes('@perf')||value.startsWith('--grep=')&&value.includes('@perf'));
export default defineConfig({
 testDir:'./e2e', timeout:180000, expect:{timeout:90000}, fullyParallel:false, workers:1, retries:0,
 reporter:'list', outputDir:process.env.INFRAARCH_PHASE9_OUTPUT_DIR?path.join(process.env.INFRAARCH_PHASE9_OUTPUT_DIR,'playwright-artifacts'):'test-results', grepInvert:perf?undefined:/@perf/,
 globalSetup:'./e2e/support/prerequisites.ts',
 use:{baseURL:'http://127.0.0.1:5173',browserName:'chromium',viewport:{width:1440,height:900},reducedMotion:'reduce',trace:'retain-on-failure'},
 webServer:[
  {command:'make migrate-test && backend/.venv/bin/python -m tests.e2e_server',cwd:root,url:'http://127.0.0.1:8000/api/health',timeout:120000,reuseExistingServer:false,
   env:{AUTH_LOGIN_ATTEMPTS_PER_MINUTE:'100',INFRAARCH_TEST_BOOTSTRAP:'1',PYTHONPATH:[path.join(root,'backend/tests/bootstrap'),path.join(root,'backend')].join(path.delimiter),DATABASE_URL:database,MIGRATION_DATABASE_URL:owner,TEST_DATABASE_URL:database,TEST_MIGRATION_DATABASE_URL:owner,LLM_PROVIDER:'stub',LLM_MODEL:'',LLM_API_KEY:'',LLM_BASE_URL:'',LLM_REASONING_EFFORT:'',SECURITY_FIX_PROVIDER:'stub',SECURITY_FIX_MODEL:'',SECURITY_FIX_REASONING_EFFORT:'',PIPELINE_DEMO_SCENARIO:'review',API_KEY:'phase8-e2e-only',CREDENTIAL_ENCRYPTION_KEY:'MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=',CREDENTIAL_ENCRYPTION_KEY_VERSION:'1'}},
  {command:'npm run dev',env:{INFRAARCH_BACKEND_URL:'http://127.0.0.1:8000'},url:'http://127.0.0.1:5173',timeout:60000,reuseExistingServer:false},
 ],
});
