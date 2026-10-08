import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateKeyPair, exportJWK, SignJWT} from 'jose';
import worker from '../src/worker.js';
const here = dirname(fileURLToPath(import.meta.url));
const issuer = 'https://study-auth.example.test';
const audience = 'local-test-audience';
const {privateKey, publicKey} = await generateKeyPair('RS256');
const jwk = {...await exportJWK(publicKey), kid: 'local-key', alg: 'RS256', use: 'sig'};
const sign = (key = privateKey, aud = audience, expiry = '5m') => new SignJWT({email: 'study@example.test'}).setProtectedHeader({alg: 'RS256', kid: 'local-key'}).setIssuer(issuer).setAudience(aud).setIssuedAt().setExpirationTime(expiry).sign(key);
test('Streamable HTTP lifecycle and eleven tools through the actual Worker handler', async () => {
  const actualFetch = globalThis.fetch;
  const token = await sign();
  const env = {TEAM_DOMAIN: issuer, POLICY_AUD: audience, ASSETS: {fetch: async request => new Response(readFileSync(resolve(here, '../generated/assets', new URL(request.url).pathname.slice(1))))}};
  const pending = [];
  const ctx = {waitUntil: promise => pending.push(promise)};
  globalThis.fetch = (input, init) => {
    const request = new Request(input, init);
    if (request.url === `${issuer}/cdn-cgi/access/certs`) return Promise.resolve(Response.json({keys: [jwk]}));
    request.headers.set('Host', new URL(request.url).host);
    request.headers.set('Cf-Access-Jwt-Assertion', token);
    return worker.fetch(request, env, ctx);
  };
  try {await import('../scripts/smoke.mjs'); await Promise.all(pending);} finally {globalThis.fetch = actualFetch;}
});

test('Access validation refuses missing, expired, wrong-audience and forged assertions', async () => {
  const actualFetch = globalThis.fetch;
  globalThis.fetch = async () => Response.json({keys: [jwk]});
  const env = {TEAM_DOMAIN: issuer, POLICY_AUD: audience};
  const request = token => new Request('https://study.example.test/mcp', {method: 'POST', headers: token ? {'Cf-Access-Jwt-Assertion': token} : {}, body: '{}'});
  try {
    assert.equal((await worker.fetch(request(), {}, {})).status, 503);
    assert.equal((await worker.fetch(request(), env, {})).status, 403);
    const forged = await generateKeyPair('RS256');
    for (const token of ['not-a-jwt', await sign(privateKey, audience, Math.floor(Date.now() / 1000) - 60), await sign(privateKey, 'other-audience'), await sign(forged.privateKey)]) {
      assert.equal((await worker.fetch(request(token), env, {})).status, 403);
    }
    // An authenticated oversized body is refused before executing any tool.
    const large = new Request('https://study.example.test/mcp', {method: 'POST', headers: {'Cf-Access-Jwt-Assertion': await sign()}, body: 'x'.repeat(128 * 1024 + 1)});
    assert.equal((await worker.fetch(large, env, {})).status, 413);
    assert.equal((await worker.fetch(new Request('https://study.example.test/health'), {}, {})).status, 200);
  } finally {globalThis.fetch = actualFetch;}
});
