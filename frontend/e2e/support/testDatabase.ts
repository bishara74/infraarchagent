/** Fail before launching any server or migration; never echo credential URLs. */
export function assertTestDatabases(app: string | undefined, owner: string | undefined): [string, string] {
  if (!app || !owner) throw new Error('Export TEST_DATABASE_URL and TEST_MIGRATION_DATABASE_URL; E2E never loads dotenv.');
  try {
    for (const [value, role] of [[app, 'infraarch_app'], [owner, 'infraarch_owner']] as const) {
      const url = new URL(value);
      if (url.protocol !== 'postgresql+asyncpg:' || decodeURIComponent(url.pathname) !== '/infraarch_test' || decodeURIComponent(url.username) !== role) throw new Error('invalid');
    }
  } catch { throw new Error('E2E requires the infraarch_test database with the app and owner roles.'); }
  return [app, owner];
}
