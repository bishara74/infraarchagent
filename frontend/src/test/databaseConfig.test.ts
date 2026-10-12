import { expect, it } from 'vitest';
import { assertTestDatabases } from '../../e2e/support/testDatabase';
const app='postgresql+asyncpg://infraarch_app:test-only@127.0.0.1:55436/infraarch_test';
const owner=app.replace('infraarch_app','infraarch_owner');
it('NFR-01 E2E accepts only the exact test database and normal roles',()=>expect(()=>assertTestDatabases(app,owner)).not.toThrow());
it.each([app.replace('/infraarch_test','/infraarch_test_other'),app.replace('/infraarch_test','/infraarch_dev?name=/infraarch_test'),app.replace('infraarch_app','infraarch_owner'),'invalid',''])('NFR-01 rejects unsafe verification URLs without echoing credentials',value=>{try{assertTestDatabases(value,owner);throw new Error('Expected rejection');}catch(error){expect((error as Error).message).not.toContain('test-only');expect((error as Error).message).toMatch(/E2E|Export/);}});
