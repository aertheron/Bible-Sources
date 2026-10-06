import test from 'node:test';
import {readFileSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import worker from '../src/worker.js';
const here = dirname(fileURLToPath(import.meta.url));
test('Streamable HTTP lifecycle and eleven tools through the actual Worker handler', async () => {
  const actualFetch = globalThis.fetch;
  const env = {ASSETS: {fetch: async request => new Response(readFileSync(resolve(here, '../generated/assets', new URL(request.url).pathname.slice(1))))}};
  const pending = [];
  const ctx = {waitUntil: promise => pending.push(promise)};
  globalThis.fetch = (input, init) => {const request = new Request(input, init); request.headers.set('Host', new URL(request.url).host); return worker.fetch(request, env, ctx);};
  try {await import('../scripts/smoke.mjs'); await Promise.all(pending);} finally {globalThis.fetch = actualFetch;}
});
