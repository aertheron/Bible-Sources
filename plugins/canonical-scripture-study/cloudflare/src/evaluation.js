import {bounded, config, exactKeys, isObject, nonempty, strings, StudyError} from './common.js';
import {References} from './reference.js';
export function textualCases(reference, refs = new References()) {
  const p = refs.parse(reference);
  return config('textual-cases').cases.filter(row => {
    let q; try {q = refs.parse(row.reference, true);} catch (error) {if (error instanceof StudyError) return false; throw error;}
    return p.book === q.book && (p.start_chapter < q.end_chapter || p.start_chapter === q.end_chapter && p.start_verse <= q.end_verse) && (q.start_chapter < p.end_chapter || q.start_chapter === p.end_chapter && q.start_verse <= p.end_verse);
  });
}
export function evaluateVariant(record) {
  const required = ['reference', 'base_reading_id', 'significance', 'readings'], allowed = [...required, 'assessment', 'requested_inclusion_id'];
  if (!isObject(record) || !required.every(k => Object.hasOwn(record, k)) || Object.keys(record).some(k => !allowed.includes(k))) throw new StudyError('variant_contract', 'Supply reference, base_reading_id, significance and readings; only assessment and requested_inclusion_id are optional.');
  const refs = new References(); refs.scope(refs.parse(record.reference));
  if (!['semantic', 'theological', 'insignificant', 'uncertain'].includes(record.significance)) throw new StudyError('variant_contract', 'Significance must be semantic, theological, insignificant or uncertain.');
  const readings = record.readings;
  if (!Array.isArray(readings) || readings.length < 1 || readings.length > 12) throw new StudyError('variant_contract', 'Supply one to twelve identified readings.');
  const byId = new Map();
  for (const r of readings) {
    if (!exactKeys(r, ['id', 'text', 'source_ids', 'evidence', 'status', 'independence_group'])) throw new StudyError('variant_contract', 'Each reading needs exactly id, text, source_ids, evidence, status and independence_group.');
    if (typeof r.id !== 'string' || !r.id || byId.has(r.id) || typeof r.text !== 'string' || typeof r.independence_group !== 'string') throw new StudyError('variant_contract', 'Reading IDs must be unique; text and independence group must be strings.');
    if (!['attested', 'reconstructed', 'unverified', 'unavailable'].includes(r.status) || !strings(r.source_ids) || r.source_ids.some(x => !x) || !Array.isArray(r.evidence)) throw new StudyError('variant_contract', 'Invalid reading status or source/evidence arrays.');
    if (r.status === 'attested' && (!r.source_ids.length || !r.evidence.length)) throw new StudyError('variant_evidence', 'An attested reading requires an identified source and evidence, including attested omissions.');
    byId.set(r.id, r);
  }
  if (typeof record.base_reading_id !== 'string') throw new StudyError('variant_base', 'The base reading ID must be a string.');
  const base = byId.get(record.base_reading_id);
  if (!base || base.status !== 'attested') throw new StudyError('variant_base', 'The named base reading must be supplied as attested with evidence.');
  let selected = base, status = 'provisional_named_base', reason = 'No completed evidence assessment selects another reading.';
  const assessment = record.assessment ?? null;
  if (assessment !== null) {
    if (!exactKeys(assessment, ['selected_reading_id', 'reason', 'evidence', 'counter_evidence', 'reviewer', 'confidence']) || typeof assessment.selected_reading_id !== 'string' || !['low', 'medium', 'high'].includes(assessment.confidence) || !nonempty(assessment.reason) || !nonempty(assessment.reviewer) || !Array.isArray(assessment.evidence) || !assessment.evidence.length || !Array.isArray(assessment.counter_evidence)) throw new StudyError('variant_assessment', 'Assessment requires the selected ID, reason, evidence, counter_evidence, reviewer and low/medium/high confidence.');
    const candidate = byId.get(assessment.selected_reading_id);
    if (!candidate || candidate.status !== 'attested') throw new StudyError('variant_assessment', 'A reconstructed, unavailable or unverified reading cannot be asserted as the attested primary text.');
    selected = candidate; status = 'reviewed_selection_contract_valid'; reason = assessment.reason;
  }
  if (record.significance === 'insignificant') {selected = base; status = 'insignificant_base_retained'; reason = 'Retain the named base for non-semantic differences; keep all evidence in the packet.';}
  const cases = textualCases(record.reference, refs); let inclusion = null;
  if (record.requested_inclusion_id !== undefined && record.requested_inclusion_id !== null) {
    if (typeof record.requested_inclusion_id !== 'string') throw new StudyError('variant_inclusion', 'The inclusion reading ID must be a string.');
    const r = byId.get(record.requested_inclusion_id);
    if (!cases.length || !r || r.status !== 'attested' || !r.text.trim()) throw new StudyError('variant_inclusion', 'Bracketed study inclusion needs a registered case and exact, nonempty, attested source text.');
    inclusion = {reading_id: r.id, text: r.text, display: 'square_brackets_with_factual_footnote', authenticity: 'separate_from_study_inclusion'};
  }
  return bounded({reference: record.reference, selected_reading_id: selected.id, selected_text: selected.text, status, reason, assessment, footnotes: readings.filter(r => r.id !== selected.id).map(r => ({reading_id: r.id, text: r.text, source_ids: r.source_ids, status: r.status, evidence: r.evidence})), all_readings: readings, special_cases: cases, study_inclusion: inclusion, warnings: ["Contract validation does not independently authenticate cited evidence or certify the reviewer's judgment.", 'Christology, difficulty, brevity and numerical agreement are clues, not automatic winners.', 'A corpus label or a modern edition must not be counted as an independent manuscript vote.']}, 16000);
}
