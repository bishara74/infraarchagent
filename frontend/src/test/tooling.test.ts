// @vitest-environment node
import { createServer as createHttpServer } from 'node:http';
import type { AddressInfo } from 'node:net';

import { createServer as createViteServer, type ViteDevServer } from 'vite';
import { afterEach, expect, it, vi } from 'vitest';

afterEach(()=>vi.unstubAllEnvs());

it('defaults the backend proxy to port 8000 without dotenv',async()=>{
 vi.stubEnv('INFRAARCH_BACKEND_URL',undefined);vi.resetModules();
 const {default:config}=await import('../../vite.config');
 expect(config.envDir).toBe(false);expect(config.server?.proxy?.['/api']).toMatchObject({target:'http://127.0.0.1:8000'});
});

it('serves the local shell and preserves API requests through the dev proxy', async () => {
  const backend = createHttpServer(async (request, response) => {
    const chunks: Buffer[] = [];
    for await (const chunk of request) {
      chunks.push(Buffer.from(chunk as Uint8Array));
    }
    response.setHeader('Content-Type', 'application/json');
    response.end(JSON.stringify({
      path: request.url,
      method: request.method,
      key: request.headers['x-api-key'],
      body: Buffer.concat(chunks).toString(),
    }));
  });
  await new Promise<void>((resolve, reject) => {
    backend.once('error', reject);
    backend.listen(0, '127.0.0.1', resolve);
  });

  const backendPort = (backend.address() as AddressInfo).port;
  let server: ViteDevServer | undefined;

  try {
    vi.stubEnv('INFRAARCH_BACKEND_URL',`http://127.0.0.1:${backendPort}`);vi.resetModules();
    const {default:config}=await import('../../vite.config');
    const apiProxy = config.server?.proxy?.['/api'];
    if (!apiProxy || typeof apiProxy === 'string') {
      throw new Error('The API proxy configuration is missing.');
    }
    server = await createViteServer({
      ...config,
      configFile: false,
      logLevel: 'silent',
      server: {
        ...config.server,
        port: 0,
        proxy: config.server?.proxy,
      },
    });
    await server.listen();
    const port = (server.httpServer?.address() as AddressInfo).port;
    const origin = `http://127.0.0.1:${port}`;
    const page = await fetch(origin);
    expect(page.status).toBe(200);
    expect(await page.text()).toContain('<title>InfraArchAgent</title>');

    const body = JSON.stringify({ text: 'Deploy an AWS web service' });
    const reply = await fetch(`${origin}/api/pipeline/probe?check=setup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': 'test-only' },
      body,
    });
    expect(reply.status).toBe(200);
    expect(await reply.json()).toEqual({
      path: '/api/pipeline/probe?check=setup',
      method: 'POST',
      key: 'test-only',
      body,
    });
  } finally {
    await server?.close();
    await new Promise<void>((resolve, reject) => {
      backend.close((error) => error ? reject(error) : resolve());
    });
  }
}, 30_000);
