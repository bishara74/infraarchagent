/** Explicit fixture capture against a local, dotenv-disabled stub/review backend. */
import { request } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';

export async function recordFixtures() {
  const context = await request.newContext({ baseURL: 'http://127.0.0.1:8000', timeout: 180000 });
  const directory = new URL('../../src/test/fixtures/', import.meta.url);
  try {
    const response = await context.post('/api/pipeline/run', { data: { text: 'Create a secure AWS web service with Terraform.', config: { provider: 'stub' } } });
    if (response.status() !== 202) throw new Error('Stub submission failed.');
    const { run_id: id } = await response.json() as { run_id: string };
    const stream = await context.get(`/api/pipeline/${id}/stream`);
    if (!stream.ok()) throw new Error('Stream capture failed.');
    const events = await stream.text();
    const pending = await (await context.get(`/api/pipeline/${id}/results`)).json() as { packages: { variant: string; review_available: boolean }[] };
    if (!pending.packages.some(item => item.variant === 'security' && item.review_available)) throw new Error('Review scenario prerequisites are not satisfied.');
    const cursor = [...events.matchAll(/^id: (\d+)$/gm)].at(-1)?.[1];
    const retry = await context.post(`/api/pipeline/${id}/packages/security/review`, { data: { action: 'retry', feedback: 'Declare the missing review_demo local.' } });
    if (retry.status() !== 202) throw new Error('Retry failed.');
    const retried = await context.get(`/api/pipeline/${id}/stream`, { headers: cursor ? { 'Last-Event-ID': cursor } : {} });
    const retryEvents = await retried.text();
    const repaired = await (await context.get(`/api/pipeline/${id}/results`)).json();
    await mkdir(directory, { recursive: true });
    for (const [name, value] of Object.entries({ 'pending-results.json': JSON.stringify(pending, null, 2), 'repaired-results.json': JSON.stringify(repaired, null, 2), 'run.sse': events, 'retry.sse': retryEvents })) await writeFile(new URL(name, directory), value + '\n');
    console.log('Recorded pending and repaired results and both SSE streams.');
  } finally { await context.dispose(); }
}
if (process.argv[1]?.endsWith('/recordFixtures.ts')) await recordFixtures();
