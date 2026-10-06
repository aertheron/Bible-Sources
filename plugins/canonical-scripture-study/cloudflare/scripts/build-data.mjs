// Deterministic deployment assets derived from the pinned, verified source snapshot.
import {readFileSync, writeFileSync, mkdirSync, readdirSync, rmSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../../..');
const here = resolve(root, 'plugins/canonical-scripture-study/cloudflare');
const profile = JSON.parse(readFileSync(resolve(here, '../bible_study/config/source-profile.json')));
const assets = resolve(here, 'generated/assets');
mkdirSync(resolve(here, 'generated'), {recursive: true});
rmSync(assets, {recursive: true, force: true});
mkdirSync(assets, {recursive: true});
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const files = new Map();
const assetHashes = {};
const verifiedMetadata = new Set();
const verifiedSpans = new Set();
let totalBytes = 0;
function source(path) {
  if (typeof path !== 'string' || path.includes('\\') || path.startsWith('/') || path.split('/').includes('..')) throw Error('Unsafe source path');
  if (!files.has(path)) files.set(path, readFileSync(resolve(root, path)));
  return files.get(path);
}
function checked(bytes, expected) {
  if (hash(bytes) !== expected) throw Error(`Source hash mismatch: ${expected}`);
  return bytes;
}
function metadata(path) {const bytes = checked(source(path), profile.metadata_hashes[path]); verifiedMetadata.add(path); return bytes;}
function span(p) {
  const start = Number(p.byte_offset), length = Number(p.byte_length);
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(length) || start < 0 || length < 1 || length > 4 * 1024 * 1024) throw Error('Invalid source span');
  const bytes = checked(source(p.file ?? p.path).subarray(start, start + length), p.sha256);
  verifiedSpans.add(`${p.file ?? p.path}:${start}:${length}:${p.sha256}`);
  return bytes;
}
function text(bytes) {
  const value = bytes.toString('utf8');
  if (!Buffer.from(value, 'utf8').equals(bytes)) throw Error('Invalid UTF-8 source; no lossy conversion allowed');
  return value;
}
function asset(path, bytes) {
  if (bytes.length > 25 * 1024 * 1024) throw Error(`Free static-file size exceeded: ${path}`);
  if (assetHashes[path]) return;
  mkdirSync(dirname(resolve(assets, path)), {recursive: true});
  writeFileSync(resolve(assets, path), bytes);
  assetHashes[path] = {sha256: hash(bytes), bytes: bytes.length};
  totalBytes += bytes.length;
}
function spanAsset(p) {const bytes = span(p); asset(`spans/${p.sha256}.txt`, bytes);}
function tsv(bytes) {
  const lines = text(bytes).replace(/\r\n/g, '\n').trimEnd().split('\n');
  const columns = lines.shift().split('\t');
  return lines.map(line => {const cells = line.split('\t'); return Object.fromEntries(columns.map((c, i) => [c, cells[i] ?? '']));});
}
function pointer(row, field = 'file', prefix = '') {
  return {file: 'sources/dss/2.0.1/enriched/' + row[field], byte_offset: +row[prefix + 'byte_offset'], byte_length: +row[prefix + 'byte_length'], sha256: row[prefix + 'sha256']};
}
function evidence(p) {
  return {repository: profile.repository, source_commit: profile.commit, file: p.file ?? p.path, byte_offset: +p.byte_offset, byte_length: +p.byte_length, sha256: p.sha256};
}

const chapterRows = text(metadata('indexes/chapter-index.jsonl')).trimEnd().split('\n').map(JSON.parse);
const chapters = Object.fromEntries(chapterRows.map(r => [`${r.dataset_id}|${r.book_id}|${r.chapter}`, r]));
chapterRows.forEach(spanAsset);
const wordIndex = JSON.parse(text(metadata('indexes/word-study-index.json')));
const lexicalIndex = JSON.parse(text(metadata('indexes/lexical-entry-index.json')));
const compiledMetadata = {
  'indexes/word-study-index.json': wordIndex,
  'indexes/lexical-entry-index.json': lexicalIndex,
  'resources/research-links.json': JSON.parse(text(metadata('resources/research-links.json'))),
};
for (const row of wordIndex.studies) spanAsset(row.entry_record);
for (const rows of [wordIndex.sense_records, wordIndex.context_records]) Object.values(rows).forEach(spanAsset);
Object.values(lexicalIndex).flat().forEach(spanAsset);
for (const path of Object.keys(profile.metadata_hashes).filter(p => p.startsWith('sources/sblgnt/apparatus/'))) {
  const bytes = metadata(path); asset(`spans/${profile.metadata_hashes[path]}.txt`, bytes);
}

// One DSS verse per asset; preserve original physical-record and status-row order.
const dssRows = {};
const supportedDssBooks = new Set(Object.values(JSON.parse(readFileSync(resolve(here, '../bible_study/config/books.json'))).books).map(b => b.dss_book).filter(Boolean));
let dssPhysicalRecords = 0, dssPassages = 0;
for (const path of Object.keys(profile.metadata_hashes).filter(p => p.startsWith('indexes/dss/records/') && !p.split('/').at(-1).startsWith('_'))) {
  const book = path.split('/').at(-1).replace(/\.tsv$/, '');
  if (!supportedDssBooks.has(book)) continue;
  const rows = tsv(metadata(path));
  const statusPath = `indexes/dss/passage-status/${book}.tsv`;
  const statuses = profile.metadata_hashes[statusPath] ? tsv(metadata(statusPath)) : [];
  const statusById = new Map();
  statuses.forEach((row, order) => {
    const p = pointer(row);
    const item = {metadata: row, text: text(span(p)), evidence: evidence(p)};
    for (const id of row.record_ids.match(/L\d+-R\d+/g) ?? []) {
      if (!statusById.has(id)) statusById.set(id, []);
      statusById.get(id).push({order, item});
    }
  });
  const byVerse = new Map();
  dssRows[book] = [];
  for (const row of rows) {
    if (!/^\d+$/.test(row.chapter) || !/^\d+$/.test(row.verse)) continue;
    const key = `${+row.chapter}/${+row.verse}`;
    if (!byVerse.has(key)) byVerse.set(key, {records: [], passage_status: new Map()});
    const pack = byVerse.get(key);
    const p = pointer(row), lp = pointer(row, 'linguistics_file', 'linguistics_');
    const hp = profile.dss_linguistic_headers[lp.file];
    const item = {
      metadata: row, evidence: evidence(p), raw_reading_and_sign_annotations: text(span(p)),
      linguistics: {
        columns: text(span(hp)).trim().split('\t'), table: text(span(lp)), evidence: evidence(lp),
        value_encoding: 'tab_delimited_JSON_cells_null_empty_and_NA_distinct',
        provenance: 'source.* records Abegg/TF annotations; derived_* records later analyses. Neither layer is automatically surviving ink.',
        feature_guide: 'sources/dss/2.0.1/enriched/feature_guide.txt',
      },
    };
    dssRows[book].push([+row.chapter, +row.verse, pack.records.length]);
    pack.records.push(item);
    for (const s of statusById.get(row.record_id) ?? []) pack.passage_status.set(s.order, s.item);
    dssPhysicalRecords++;
  }
  for (const [key, pack] of byVerse) {
    asset(`dss/${book}/${key}.json`, Buffer.from(JSON.stringify({records: pack.records, passage_status: [...pack.passage_status].map(([order, item]) => ({order, item}))})));
    dssPassages++;
  }
}

const documents = {};
for (const folder of readdirSync(resolve(here, '../skills'))) {
  const path = `skills/${folder}/SKILL.md`;
  const value = readFileSync(resolve(here, '..', path), 'utf8').replace(/^---\n[\s\S]*?\n---\n/, '');
  documents[path] = value;
}
for (const file of readdirSync(resolve(here, '../references')).filter(n => n.endsWith('.md'))) documents[`references/${file}`] = readFileSync(resolve(here, '../references', file), 'utf8');
const counts = {asset_files: Object.keys(assetHashes).length, asset_bytes: totalBytes, indexed_chapters: chapterRows.length, dss_physical_records: dssPhysicalRecords, dss_passages: dssPassages};
if (counts.asset_files > 20000) throw Error('Cloudflare Free static-file count exceeded');
const bundle = {source_commit: profile.commit, compiled_metadata: compiledMetadata, chapters, dss_rows: dssRows, asset_hashes: assetHashes, documents, counts};
writeFileSync(resolve(here, 'generated/bundle.json'), JSON.stringify(bundle));
writeFileSync(resolve(here, 'generated/build-report.json'), JSON.stringify({schema_version: '0.1.0', source_commit: profile.commit, metadata_verified: verifiedMetadata.size, source_spans_verified: verifiedSpans.size, ...counts, largest_asset_bytes: Math.max(...Object.values(assetHashes).map(x => x.bytes)), free_limits_checked: {asset_files: 20000, individual_asset_bytes: 25 * 1024 * 1024}, source_normalization: false, runtime_source_verification: 'SHA-256 for each asset; original span pointers retained'}, null, 2) + '\n');
console.log(JSON.stringify({source_commit: profile.commit, ...counts}));
