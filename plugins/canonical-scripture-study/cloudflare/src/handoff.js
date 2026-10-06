import {bounded, exactKeys, isObject, nonempty, strings, StudyError, validatePreferences} from './common.js';
import {References} from './reference.js';
const PAYLOADS = {
  fetch_align: {source_packets: 'array', alignment_status: 'string'},
  collate_compare: {differences: 'array', comparison_limits: 'array'},
  evaluate_select: {decisions: 'array', unresolved: 'array'},
  translate_annotate: {verses: 'array', footnotes: 'array', term_key: 'array', context_preface: 'string'},
  exegetical_synthesis: {observations: 'array', biblical_development: 'array', canonical_links: 'array', formation: 'array'},
  theology_review: {claim_reconstruction: 'string', findings: 'array', verdict: 'string'},
  dss_research: {records: 'array', reconstruction_limits: 'array'},
};
export function validateHandoff(packet) {
  if (!exactKeys(packet, ['schema_version', 'study_id', 'stage', 'reference', 'language', 'translation_format', 'depends_on', 'evidence', 'payload', 'uncertainties'])) throw new StudyError('handoff_fields', 'Use exactly the ten documented stage-envelope fields.');
  if (packet.schema_version !== '0.1.0' || typeof packet.study_id !== 'string' || !/^[A-Za-z0-9_.-]{1,80}$/.test(packet.study_id)) throw new StudyError('handoff_version', 'Use schema 0.1.0 and a short stable study ID.');
  const stage = packet.stage;
  if (typeof stage !== 'string' || !Object.hasOwn(PAYLOADS, stage)) throw new StudyError('handoff_stage', 'Unrecognized pipeline stage.');
  validatePreferences(packet.language, packet.translation_format);
  const refs = new References(); let scope = null;
  if (packet.reference !== null) {scope = refs.scope(refs.parse(packet.reference)); if (refs.count(scope) > 45) throw new StudyError('handoff_scope', 'Process a long chapter in the planned smaller portions before creating this handoff.');}
  for (const name of ['depends_on', 'uncertainties']) if (!strings(packet[name], 64)) throw new StudyError('handoff_array', `${name} must be an array of at most 64 strings.`);
  const evidence = packet.evidence;
  if (!Array.isArray(evidence) || evidence.length > 64 || evidence.some(e => !isObject(e) || !nonempty(e.id) || !nonempty(e.locator)) || new Set(evidence.map(e => e.id)).size !== evidence.length) throw new StudyError('handoff_evidence', 'Evidence must contain at most 64 objects with unique nonempty id and locator strings.');
  const payload = packet.payload;
  if (!exactKeys(payload, Object.keys(PAYLOADS[stage])) || Object.entries(PAYLOADS[stage]).some(([k, t]) => t === 'array' ? !Array.isArray(payload[k]) : typeof payload[k] !== t)) throw new StudyError('handoff_payload', 'Payload must match the exact fields and types for this stage.');
  if (stage === 'translate_annotate') {
    if (!scope || !payload.verses.length) throw new StudyError('translation_scope', 'A translation needs an explicit bounded reference and at least one verse.');
    const seen = new Set();
    for (const row of payload.verses) {
      if (!exactKeys(row, ['reference', 'working_translation', 'alignment_groups']) || !nonempty(row.working_translation) || !Array.isArray(row.alignment_groups)) throw new StudyError('translation_verse', 'Each verse needs exactly reference, working_translation and alignment_groups.');
      const p = refs.parse(row.reference), key = `${p.start_chapter}:${p.start_verse}`;
      if (p.book !== scope.book || p.start_chapter !== p.end_chapter || p.start_verse !== p.end_verse || !scope.contains(p.start_chapter, p.start_verse) || seen.has(key)) throw new StudyError('translation_verse', 'Verse rows must be unique single verses within the envelope reference.');
      seen.add(key);
      if (packet.translation_format !== 'plain_working' && !row.alignment_groups.length) throw new StudyError('interlinear_alignment', 'An interlinear display requires original/transliteration/gloss groups tied to source token IDs.');
      for (const group of row.alignment_groups) if (!exactKeys(group, ['source_token_ids', 'original', 'transliteration', 'gloss']) || !['original', 'transliteration', 'gloss'].every(k => nonempty(group[k])) || !strings(group.source_token_ids) || !group.source_token_ids.length || group.source_token_ids.some(i => !i)) throw new StudyError('interlinear_alignment', 'Each alignment group needs source_token_ids, original, transliteration and gloss.');
    }
  }
  bounded(packet, 16000);
  return {valid: true, study_id: packet.study_id, stage, schema_version: '0.1.0', limitations: 'Validation checks structure, scope and size. The host must check complete source coverage, token alignment, cited evidence and interpretive accuracy.'};
}
