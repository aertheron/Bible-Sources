import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {Engine} from '../src/engine.js';
import {SourceStore, clearCache, bundle, verify, encode} from '../src/store.js';
import {StudyError, bounded} from '../src/common.js';
import {evaluateVariant} from '../src/evaluation.js';
import {validateHandoff} from '../src/handoff.js';
import {surfaceTokens} from '../src/readers.js';

const here = dirname(fileURLToPath(import.meta.url));
const assets = {fetch: async request => {
  const path = new URL(request.url).pathname.slice(1);
  assert.ok(Object.hasOwn(bundle.asset_hashes, path));
  return new Response(readFileSync(resolve(here, '../generated/assets', path)));
}};
const make = () => new Engine(new SourceStore(assets));
async function call({kind, args}) {
  const e = make();
  const functions = {plan: e.plan.bind(e), passage: e.reader.passage.bind(e.reader), apparatus: e.reader.apparatus.bind(e.reader), dss: e.reader.dss.bind(e.reader), word: e.knowledge.word.bind(e.knowledge), lexical: e.knowledge.lexical.bind(e.knowledge), trajectory: e.knowledge.trajectory.bind(e.knowledge), evaluate: evaluateVariant, handoff: validateHandoff, portions: e.refs.portions.bind(e.refs), native: e.reader.nativeChapter.bind(e.reader)};
  try {return await functions[kind](...args);} catch (error) {if (error instanceof StudyError) return {domain_error: error.code}; throw error;}
}
const variant = {reference: 'Matthew 6:13', base_reading_id: 'base', significance: 'semantic', readings: [{id: 'base', text: 'identified base wording', source_ids: ['edition-base'], evidence: [{locator: 'identified source'}], status: 'attested', independence_group: 'base-tradition'}, {id: 'short', text: 'short', source_ids: ['LXX', 'DSS'], evidence: [{locator: 'identified alternative'}], status: 'attested', independence_group: 'other-tradition'}]};
const handoff = {schema_version: '0.1.0', study_id: 'rom12', stage: 'translate_annotate', reference: 'Romans 12:1-2', language: 'en', translation_format: 'plain_working', depends_on: ['reading'], evidence: [{id: 'source', locator: 'Rom 12:1'}], payload: {verses: [{reference: 'Romans 12:1', working_translation: 'Therefore, I appeal to you.', alignment_groups: []}], footnotes: [], term_key: [], context_preface: 'The appeal follows the preceding argument.'}, uncertainties: []};

test('Worker matches Python source packets, plans, studies and validation contracts', async t => {
  const cases = [];
  const add = (kind, ...args) => cases.push({kind, args});
  for (const query of ['Translate Genesis 1:1-2:3', 'Translate Genesis 1-2, in Dutch, with original language interlinear', 'Translate the whole of Isaiah', 'Full study Romeinen 12:1-2, in Nederlands, with original interlinear', 'Romans 12:1-2', 'Exegesis only Romans 12:1-2', 'Word study testing. Compare Matthew 6:13 and James 1:13.', 'Theme study salvation', 'Translate Acts 8:37', 'Next', 'help', 'Translate Genesis 0', 'Translate Genesis 1:99', 'Translate Isaiah 67', 'Translate Genesis 5-3', 'Translate Unknown 1']) add('plan', query);
  for (const query of ['Standard study Genesis 1:1', 'Detailed study Genesis 1-2', 'Uitgebreide studie Genesis 1', 'Word study testing, full', 'Exegesis only Romans 12:1-2, detailed', 'Translate Genesis 1, full', 'Genesis 1, standaard', 'Detailed Genesis 1']) add('plan', query);
  for (const depth of ['standard', 'detailed', 'full', 'invalid', [], '__proto__']) add('plan', 'Genesis 1', null, 'en', 'plain_working', null, depth);
  const detailed = (await make().plan('Detailed study Genesis 1-2, in Dutch, with original language interlinear')).continuation_state;
  add('plan', 'Next', null, 'en', 'plain_working', detailed);
  add('plan', 'Next, full', null, 'en', 'plain_working', detailed);
  for (const mode of ['full_study', 'study_plan']) {
    const legacy = {...detailed, request_mode: mode}; delete legacy.study_depth;
    add('plan', 'Next', null, 'en', 'plain_working', legacy);
  }
  for (const depth of ['invalid', [], null]) add('plan', 'Next', null, 'en', 'plain_working', {...detailed, study_depth: depth});
  add('plan', 'Next', null, 'en', 'plain_working', {...detailed, study_depth: 'standard'});
  const state = (await make().plan('Translate Genesis 1-2, in Dutch, with original language interlinear')).continuation_state;
  for (const command of ['Next', 'Next chapter 2', 'Next: Genesis 2', 'Volgende hoofdstuk 2']) add('plan', command, null, 'en', 'plain_working', state);
  add('plan', 'Next', null, 'en', 'plain_working', {request_mode: []});
  for (const [book, row] of Object.entries(make().refs.books)) {
    for (const c of Object.keys(make().refs.verses[book])) add('portions', `${row.name} ${c}`);
  }
  for (const args of [
    ['Genesis 1-2', ['WLC']], ['Genesis 1:1-2:3', ['WLC']],
    ['Genesis 1:1', ['WLC', 'UXLC', 'TAHOT', 'LXX'], 'linguistic'],
    ['Genesis 4:8', ['TAHOT']], ['Romans 12:1-2', ['SBLGNT'], 'linguistic'],
    ['Matthew 6:13', null, 'linguistic'], ['James 1:13', null, 'linguistic'],
    ['Acts 8:37', ['SBLGNT']], ['Genesis 1:1', ['RAHLFS']],
    ['Psalm 119'], ['Isaiah 66:18-24'], ['Jeremiah 31:31-34'],
  ]) add('passage', ...args);
  for (const ref of ['1 Corinthians 1', 'Matthew 6:13', 'John 7:53-8:11', 'Genesis 1']) add('apparatus', ref);
  for (let cursor = 0; cursor < 7; cursor++) add('dss', 'Genesis 1:27', cursor);
  add('dss', 'Genesis 1:27', 2, 3, false);
  for (const ref of ['Genesis 1', 'Isaiah 53:1-3', 'Deuteronomy 32:43', 'Psalms 22:16', 'Esther 1:1']) add('dss', ref);
  add('dss', 'Genesis 1:27', 8);
  add('dss', 'Genesis 1:27', 0, 4);
  for (let n = 1; n <= 50; n++) add('word', `WT${String(n).padStart(3, '0')}`);
  for (const query of ['testing', 'Hades', 'faith', 'unlisted-term']) add('word', query);
  add('word', Object.keys(bundle.compiled_metadata['indexes/word-study-index.json'].sense_records)[0]);
  for (const id of Object.keys(bundle.compiled_metadata['indexes/lexical-entry-index.json'])) add('lexical', id);
  for (const query of ['salvation', 'justification', 'judgment', 'Jesus in the OT', 'presence', 'testing', 'unlisted-theme']) add('trajectory', query);
  add('evaluate', variant);
  add('evaluate', {...variant, significance: 'insignificant'});
  add('evaluate', {...variant, assessment: {selected_reading_id: 'short', reason: 'documented review', evidence: ['source'], counter_evidence: [], reviewer: 'test', confidence: 'low'}});
  add('evaluate', {...variant, readings: variant.readings.map((r, i) => i ? {...r, status: 'reconstructed'} : r), assessment: {selected_reading_id: 'short', reason: 'documented review', evidence: ['source'], counter_evidence: [], reviewer: 'test', confidence: 'low'}});
  for (const [key, value] of [['significance', []], ['base_reading_id', []], ['requested_inclusion_id', []]]) add('evaluate', {...variant, [key]: value});
  add('handoff', handoff);
  add('handoff', {...handoff, extra: true});
  add('handoff', {...handoff, reference: 'Romans 12-13'});
  add('handoff', {...handoff, translation_format: 'original_interlinear'});
  add('handoff', {...handoff, payload: {...handoff.payload, context_preface: 'x'.repeat(16001)}});
  const expected = JSON.parse(execFileSync('python3', [resolve(here, 'python-oracle.py')], {input: JSON.stringify(cases), maxBuffer: 16 * 1024 * 1024, encoding: 'utf8'}));
  for (let i = 0; i < cases.length; i++) assert.deepEqual(await call(cases[i]), expected[i], `${i}: ${cases[i].kind} ${JSON.stringify(cases[i].args).slice(0, 150)}`);
  t.diagnostic(`${cases.length} parity cases matched, including 1,189 chapter boundaries, all 50 studies and all selected lexical IDs.`);
});

test('Preview delivery plans complete Standard studies and gate visible results', async () => {
  const standard = await make().plan('Genesis 1:1-3', null, 'nl');
  assert.equal(standard.study_depth, 'standard');
  assert.match(standard.reader_action, /Complete this bounded passage/);
  assert.deepEqual(standard.delivery.milestones.map(x => x.id), ['orientation', 'translation_ready', 'explanation_ready', 'synthesis_ready']);
  assert.equal(standard.delivery.preferred_surface, 'sequential_assistant_messages_if_supported');
  assert.equal(standard.delivery.fallback_surface, 'single_streamed_answer_with_milestones');
  assert.equal(standard.delivery.requires_user_prompt_between_milestones, false);
  assert.equal(standard.delivery.background_jobs, false);
  assert.match(standard.delivery.instruction, /Next means a different passage/);
  assert.ok(standard.delivery.milestones.every(x => x.ready_when && x.present));

  const translation = await make().plan('Translate Genesis 1:1-3');
  assert.deepEqual(translation.delivery.milestones.map(x => x.id), ['orientation', 'translation_ready']);
  const word = await make().plan('Word study ruach');
  assert.deepEqual(word.delivery.milestones.map(x => x.id), ['orientation', 'evidence_ready', 'synthesis_ready']);
  assert.equal(word.delivery.milestones.some(x => x.id === 'translation_ready'), false);
  const detailed = await make().plan('Detailed study Genesis 1-2');
  const next = await make().plan('Next', null, 'en', 'plain_working', detailed.continuation_state);
  assert.equal(next.reference, 'Genesis 2');
  assert.equal(next.study_depth, 'detailed');
  assert.deepEqual(next.delivery.milestones, detailed.delivery.milestones);
});

test('Next recommendations follow bounded literary units without overriding requested chapters', async () => {
  const engine = make();
  const standard = await engine.plan('Genesis 1:1-3', null, 'nl');
  assert.equal(standard.reference, 'Genesis 1:1-3');
  assert.equal(standard.next.reference, 'Genesis 1:4-2:3');
  assert.equal(standard.next.literary_unit_reference, 'Genesis 1:1-2:3');
  assert.equal(standard.next.boundary_basis, 'curated_literary_continuation');
  const continuation = await engine.plan('Next', null, 'en', 'plain_working', standard.continuation_state);
  assert.equal(continuation.reference, 'Genesis 1:4-2:3');
  assert.equal(continuation.study_depth, 'standard');
  assert.equal(continuation.next.reference, 'Genesis 2:4-25');
  const chapter = await engine.plan('Genesis 1');
  assert.equal(chapter.next.reference, 'Genesis 2:1-3');
  const explicit = await engine.plan('Next chapter 2', null, 'en', 'plain_working', standard.continuation_state);
  assert.equal(explicit.reference, 'Genesis 2');
  const full = await engine.plan('Full study Genesis 1:1-2:3');
  assert.equal(full.reference, 'Genesis 1:1-2:3');
  assert.equal(full.next.reference, 'Genesis 2:4-25');
  assert.equal(engine.refs.next('Luke 1:1-25').reference, 'Luke 1:26-56');
  assert.equal(engine.refs.next('Psalms 119:1-8').reference, 'Psalms 119:9-16');
});

test('Source tampering, unsafe paths and oversized packets fail closed', async () => {
  clearCache();
  const key = Object.keys(bundle.chapters)[0], pointer = bundle.chapters[key];
  const badAssets = {fetch: async () => new Response(new Uint8Array(Number(pointer.byte_length)))};
  await assert.rejects(new SourceStore(badAssets).span(pointer), e => e.code === 'source_hash');
  assert.throws(() => SourceStore.safePath('../private'), e => e.code === 'source_path');
  await assert.rejects(new SourceStore(assets).asset('__proto__'), e => e.code === 'unregistered_source');
  assert.deepEqual((await make().knowledge.lexical('constructor')).records, []);
  await assert.rejects(verify(encode('wrong'), '0'.repeat(64)), e => e.code === 'source_hash');
  assert.throws(() => bounded({text: 'x'.repeat(60000)}), e => e.code === 'packet_budget');
});

test('Greek surface offsets retain codepoints and no invented morphology', () => {
  const text = '𐀀 Παρὰ τῷ θεῷ', chars = [...text];
  for (const token of surfaceTokens(text, 'test')) {assert.equal(token.form, chars.slice(token.start, token.end).join('')); assert.ok(!Object.hasOwn(token, 'morphology'));}
});

test('Deployment assets remain within free file allowances and exclude private Rahlfs', () => {
  const report = JSON.parse(readFileSync(resolve(here, '../generated/build-report.json')));
  assert.ok(report.asset_files <= 20000);
  assert.ok(report.largest_asset_bytes < 25 * 1024 * 1024);
  assert.equal(report.indexed_chapters, 4150);
  assert.ok(Object.values(bundle.chapters).every(r => !/rahlfs/i.test(r.file ?? r.path)));
});
