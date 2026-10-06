import bundle from '../generated/bundle.json' with {type: 'json'};
import {config, StudyError} from './common.js';
export {bundle};
const decoder = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true});
export const decode = bytes => decoder.decode(bytes);
const encoder = new TextEncoder();
const cache = new Map();
let cacheBytes = 0;
const CACHE_LIMIT = 8 * 1024 * 1024;
export async function verify(bytes, expected) {
  const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(b => b.toString(16).padStart(2, '0')).join('');
  if (typeof expected !== 'string' || digest !== expected) throw new StudyError('source_hash', 'Source bytes do not match the pinned SHA-256; do not interpret this packet.');
  return bytes;
}
export class SourceStore {
  constructor(assets) {
    if (!assets?.fetch) throw new StudyError('deployment_assets', 'This Worker needs its verified ASSETS binding.');
    this.assets = assets;
    this.profile = config('source-profile');
    if (this.profile.commit !== bundle.source_commit) throw new StudyError('source_profile', 'Rebuild deployment assets for the configured source commit.');
    this.root = null;
    this.requestAssets = new Map();
  }
  static safePath(path) {
    if (typeof path !== 'string' || !path || path.includes('\\') || path.startsWith('/') || path.split('/').includes('..')) throw new StudyError('source_path', 'Source paths must stay within the pinned repository.');
    return path;
  }
  async asset(path) {
    SourceStore.safePath(path);
    const meta = Object.hasOwn(bundle.asset_hashes, path) ? bundle.asset_hashes[path] : null;
    if (!meta) throw new StudyError('unregistered_source', 'Asset is not registered in this pinned deployment.');
    const key = `${this.profile.commit}:${meta.sha256}`;
    if (cache.has(key)) {const bytes = cache.get(key); cache.delete(key); cache.set(key, bytes); return bytes;}
    if (this.requestAssets.has(key)) return this.requestAssets.get(key);
    if (this.requestAssets.size >= 40) throw new StudyError('retrieval_budget', 'Retrieve a smaller portion or fewer supporting records per call.');
    const pending = (async () => {
      const response = await this.assets.fetch(new Request(`https://assets.internal/${path}`));
      if (!response.ok) throw new StudyError('source_missing', `Pinned deployment asset unavailable: ${path}`);
      const bytes = new Uint8Array(await response.arrayBuffer());
      if (bytes.length !== meta.bytes) throw new StudyError('source_hash', 'Deployment asset length does not match its verified build manifest.');
      await verify(bytes, meta.sha256);
      if (cache.has(key)) {cacheBytes -= cache.get(key).length; cache.delete(key);}
      while (cacheBytes + bytes.length > CACHE_LIMIT && cache.size) {const oldest = cache.keys().next().value; cacheBytes -= cache.get(oldest).length; cache.delete(oldest);}
      if (bytes.length <= CACHE_LIMIT) {cache.set(key, bytes); cacheBytes += bytes.length;}
      return bytes;
    })();
    this.requestAssets.set(key, pending);
    return pending;
  }
  async json(path) {
    if (Object.hasOwn(bundle.compiled_metadata, path)) return bundle.compiled_metadata[path];
    return JSON.parse(decode(await this.read(path)));
  }
  async read(path) {
    SourceStore.safePath(path);
    const expected = Object.hasOwn(this.profile.metadata_hashes, path) ? this.profile.metadata_hashes[path] : null;
    if (!expected) throw new StudyError('unregistered_source', 'Whole-file reads are limited to registered metadata and apparatus.');
    return this.asset(`spans/${expected}.txt`);
  }
  async span(record) {
    SourceStore.safePath(record.file ?? record.path);
    const offset = Number(record.byte_offset), length = Number(record.byte_length);
    if (!Number.isSafeInteger(offset) || !Number.isSafeInteger(length) || offset < 0 || length < 1 || length > 4 * 1024 * 1024) throw new StudyError('source_span', 'Invalid or oversized byte span.');
    const bytes = await this.asset(`spans/${record.sha256}.txt`);
    if (bytes.length !== length) throw new StudyError('source_span', 'Source span length does not match its pointer.');
    return bytes;
  }
  evidence(record) {return {repository: this.profile.repository, source_commit: this.profile.commit, file: record.file ?? record.path, byte_offset: Number(record.byte_offset), byte_length: Number(record.byte_length), sha256: record.sha256};}
  async dssVerse(book, c, v) {return JSON.parse(decode(await this.asset(`dss/${book}/${c}/${v}.json`)));}
}
export const encode = value => encoder.encode(value);
export function clearCache() {cache.clear(); cacheBytes = 0;}
