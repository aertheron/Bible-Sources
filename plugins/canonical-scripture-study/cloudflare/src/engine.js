import {bounded, charCount, config, exactKeys, FORMATS, StudyError, validatePreferences, VERSION} from './common.js';
import {References, Passage} from './reference.js';
import {Reader} from './readers.js';
import {Knowledge} from './knowledge.js';
import {textualCases} from './evaluation.js';
import {bundle} from './store.js';
import {DEPTH_MODES, DEPTH_OPTIONS, resolveDepth, validateDepth, workflow} from './workflow.js';
export const STAGES = {
  full_study: ['fetch_align', 'collate_compare', 'evaluate_select', 'translate_annotate', 'exegetical_synthesis', 'theology_review'],
  translation_only: ['fetch_align', 'collate_compare', 'evaluate_select', 'translate_annotate', 'theology_review'],
  exegesis_only: ['fetch_align', 'collate_compare', 'evaluate_select', 'exegetical_synthesis', 'theology_review'],
  context_history: ['fetch_align', 'exegetical_synthesis'],
  variant_reconciliation: ['fetch_align', 'collate_compare', 'evaluate_select', 'theology_review'],
  theology_check: ['fetch_align', 'exegetical_synthesis', 'theology_review'],
  dss_research: ['dss_research'],
  study_plan: ['fetch_align', 'collate_compare', 'evaluate_select', 'translate_annotate', 'exegetical_synthesis', 'theology_review'],
  word_study: ['fetch_align', 'exegetical_synthesis', 'theology_review'],
  theme_study: ['fetch_align', 'exegetical_synthesis', 'theology_review'],
};
STAGES.standard_study = [...STAGES.study_plan];
STAGES.detailed_study = [...STAGES.study_plan];
export const ALIASES = {
  standard_study: ['standard study', 'standard', 'standaardstudie', 'standaard studie', 'standaard'],
  detailed_study: ['detailed study', 'detailed', 'uitgebreide studie', 'uitgebreid'],
  full_study: ['full study', 'volledige studie'],
  translation_only: ['translation only', 'translate', 'vertaling alleen', 'vertaal'],
  exegesis_only: ['exegesis only', 'exegese alleen'],
  context_history: ['context and history opening', 'context and history', 'context history', 'context en geschiedenis'],
  variant_reconciliation: ['translation variance reconciliation', 'variant reconciliation', 'tekstvarianten'],
  theology_check: ['theology check', 'theologiecontrole'],
  dss_research: ['dss research', 'dead sea scrolls', 'dss studie'],
  word_study: ['word study', 'woordstudie'],
  theme_study: ['theme study', 'themastudie'],
  study_plan: ['study plan', 'studieplan'],
};
const escape = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
export class Engine {
  constructor(store) {this.store = store; this.refs = new References(); this.reader = new Reader(store, this.refs); this.knowledge = new Knowledge(store);}
  health() {
    return {plugin_version: VERSION, source_profile: this.store.profile.profile, source_commit: this.store.profile.commit, source_access: 'pinned_verified_worker_assets', base_books: Object.keys(this.refs.books).length, indexed_chapters: bundle.counts.indexed_chapters, curated_word_studies: 50, default_study_depth: 'standard', study_depths: Object.keys(config('method').study_depths), canonical_seed_dossiers: config('trajectories').dossiers.length, translation_and_interpretation: 'performed_by_the_host_model_using_skills_not_by_a_dictionary_replacement_algorithm', deployment: {runtime: 'Cloudflare Worker', services: ['Workers', 'Workers Static Assets'], paid_services_required: false, asset_files: bundle.counts.asset_files, model_api_key_required: false}, limitations: ['Cross-edition verse maps are not verified.', 'No full manuscript apparatus, full Greek concordance, exhaustive canonical database or complete imported website claim profile.', 'Free-plan CPU use must be monitored during real studies; study prose depends on the host.']};
  }
  options(query, language, format, depth) {
    const retained = [];
    for (const part of query.split(/,\s*/)) {
      const lower = part.toLowerCase().trim();
      if (Object.hasOwn(DEPTH_OPTIONS, lower)) depth = DEPTH_OPTIONS[lower];
      else if (['in dutch', 'in nederlands', 'dutch', 'nederlands'].includes(lower)) language = 'nl';
      else if (['in english', 'in engels', 'english', 'engels'].includes(lower)) language = 'en';
      else if (lower.includes('interlinear')) format = ['original', 'origineel', 'grondtekst'].some(x => lower.includes(x)) ? 'original_interlinear' : 'transliteration_interlinear';
      else if (['plain translation', 'plain working translation', 'gewone vertaling'].includes(lower)) format = 'plain_working';
      else retained.push(part);
    }
    return [retained.join(', ').trim(), language, format, depth];
  }
  state(state) {
    if ((!exactKeys(state, ['request_mode', 'language', 'translation_format', 'original_reference', 'current_reference', 'pending_references']) && !exactKeys(state, ['request_mode', 'language', 'translation_format', 'original_reference', 'current_reference', 'pending_references', 'study_depth'])) || typeof state.request_mode !== 'string' || !Object.hasOwn(STAGES, state.request_mode) || ['word_study', 'theme_study'].includes(state.request_mode)) throw new StudyError('continuation_state', 'Supply the exact continuation_state returned by the previous passage plan.');
    validatePreferences(state.language, state.translation_format);
    for (const key of ['original_reference', 'current_reference']) this.refs.parse(state[key], key === 'original_reference');
    if (!Array.isArray(state.pending_references) || state.pending_references.length > 400) throw new StudyError('continuation_state', 'Invalid pending reference list.');
    for (const ref of state.pending_references) this.refs.scope(this.refs.parse(ref));
    const depth = Object.hasOwn(state, 'study_depth') ? state.study_depth : resolveDepth(state.request_mode);
    validateDepth(depth);
    if (depth === null || (Object.hasOwn(DEPTH_MODES, state.request_mode) && depth !== DEPTH_MODES[state.request_mode])) throw new StudyError('continuation_state', 'Invalid study depth in continuation state.');
    return {...state, study_depth: depth};
  }
  async plan(query, activeReference = null, language = 'en', format = 'plain_working', studyState = null, depth = null) {
    if (typeof query !== 'string' || !query.trim() || charCount(query) > 2000) throw new StudyError('query', 'Supply a study command or Bible reference under 2,000 characters.');
    validateDepth(depth);
    let text; [text, language, format, depth] = this.options(query.trim(), language, format, depth);
    validatePreferences(language, format);
    if (['help', 'commands', "commando's", 'hulp'].includes(text.toLowerCase())) return {mode: 'help', commands: ALIASES, continuation_commands: ['Next', 'Next chapter 2', 'Next: Genesis 2', 'Volgende'], translation_formats: [...FORMATS].sort(), study_depths: config('method').study_depths, default_study_depth: 'standard'};
    const nxt = /^(?:next|volgende)(?:\s*(?::\s*|\s+)(.*))?$/i.exec(text);
    if (nxt) {
      if (studyState === null && activeReference === null) return {status: 'needs_input', message: 'Continue from a previous passage plan by supplying its continuation_state or active_reference.'};
      let state = studyState !== null ? this.state(studyState) : {request_mode: 'study_plan', language, translation_format: format, original_reference: activeReference, current_reference: activeReference, pending_references: [], study_depth: depth ?? 'standard'};
      if (depth !== null) {
        state = {...state, study_depth: depth};
        if (state.request_mode === 'study_plan' || Object.hasOwn(DEPTH_MODES, state.request_mode)) state.request_mode = Object.keys(DEPTH_MODES).find(mode => DEPTH_MODES[mode] === depth);
      }
      const current = this.refs.parse(state.current_reference); let pending = [...state.pending_references], target = nxt[1];
      if (target) {
        const chapter = /^(?:chapter|hoofdstuk)\s+(\d+)$/i.exec(target);
        if (chapter) target = `${this.refs.books[current.book].name} ${chapter[1]}`;
        const chosen = this.refs.portions(target); target = chosen[0].reference;
        pending = pending.includes(target) ? pending.slice(pending.indexOf(target) + 1) : chosen.slice(1).map(p => p.reference);
      } else if (pending.length) target = pending.shift();
      else {const following = this.refs.next(state.current_reference); if (following === null) return {status: 'book_complete', reference: state.current_reference}; target = following.reference;}
      return this.passagePlan(state.request_mode, target, state.language, state.translation_format, state.original_reference, pending, null, state.study_depth);
    }
    let mode = 'study_plan';
    for (const [alias, candidate] of Object.entries(ALIASES).flatMap(([k, values]) => values.map(a => [a, k])).sort(([a], [b]) => b.length - a.length)) {
      const m = new RegExp('^' + escape(alias) + '(?:\\s*:\\s*|\\s+|$)', 'i').exec(text);
      if (m) {mode = candidate; text = text.slice(m[0].length).trim(); break;}
    }
    if (!text) text = activeReference ?? '';
    if (!text) return {status: 'needs_input', mode, message: 'Supply the passage, word or theme for this command.'};
    if (['word_study', 'theme_study'].includes(mode)) {
      const offset = text.indexOf('. '), term = offset < 0 ? text : text.slice(0, offset), remainder = offset < 0 ? null : text.slice(offset + 2);
      return bounded({mode, topic: term.replace(/\.+$/, ''), follow_up_requested: remainder, language, translation_format: format, stages: STAGES[mode], retrieval: mode === 'word_study' ? 'lookup_word' : 'lookup_trajectory', ...workflow(mode, resolveDepth(mode, depth)), method: config('method').sequence}, 16000);
    }
    text = text.replace(/\.\s*include the linguistic information\.?$/i, '');
    const portions = this.refs.portions(text);
    return this.passagePlan(mode, portions[0].reference, language, format, text, portions.slice(1).map(p => p.reference), portions[0].boundary_status, resolveDepth(mode, depth));
  }
  async passagePlan(mode, current, language, format, original, pending, boundary = null, depth = null) {
    depth = resolveDepth(mode, depth);
    const p = this.refs.parse(current), unitSuggestions = [];
    for (const row of config('literary-units').units) {const q = this.refs.parse(row.reference); if (q.book === p.book && (q.start_chapter < p.end_chapter || q.start_chapter === p.end_chapter && q.start_verse <= p.end_verse) && (p.start_chapter < q.end_chapter || p.start_chapter === q.end_chapter && p.start_verse <= q.end_verse)) unitSuggestions.push(row);}
    const opening = await this.reader.passage(this.refs.label(new Passage(p.book, p.start_chapter, p.start_verse, p.start_chapter, p.start_verse)), [this.refs.books[p.book].testament === 'OT' ? 'WLC' : 'SBLGNT']);
    const records = opening.source_packets[0].records, words = records[0]?.text ?? '', first = words.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '').split(/\s+/).filter(Boolean).slice(0, 8).join(' ');
    const dependent = /(?:^|[^\p{L}\p{N}_])(?:ουν|αρα|διο|τοιγαρουν)(?:$|[^\p{L}\p{N}_])|δια τουτο/u.test(first) || first.startsWith('לכן') || first.startsWith('ועתה');
    let previous = null;
    if (p.start_verse > 1) previous = this.refs.label(new Passage(p.book, p.start_chapter, Math.max(1, p.start_verse - 5), p.start_chapter, p.start_verse - 1));
    else if (p.start_chapter > 1) {const c = p.start_chapter - 1, last = this.refs.last(p.book, c); previous = this.refs.label(new Passage(p.book, c, Math.max(1, last - 4), c, last));}
    const suggestedNext = pending.length ? null : this.refs.next(current);
    const logicalNext = pending[0] ?? suggestedNext?.reference ?? null;
    const state = {request_mode: mode, language, translation_format: format, original_reference: original, current_reference: current, pending_references: pending, study_depth: depth};
    return bounded({mode, reference: current, requested_reference: original, language, translation_format: format, stages: STAGES[mode], reader_action: mode === 'study_plan' ? 'Complete this bounded passage at the selected depth (Standard by default), showing verified results as early as the host allows; a short plan alone is not completion' : 'Complete this portion in the requested mode and deliver verified milestones early when supported', study_plan: ['Locate the literary unit and explain necessary preceding context.', 'Read our Hebrew/Greek evidence and review consequential variants independently.', 'Present a contextual translation with relevant footnotes and a compact term key when the command calls for translation.', 'Explain the local argument and bounded canonical connections at the selected depth; use external research only afterwards when warranted.', 'Review claims and alternatives, then suggest the logical Next portion.'], literary_unit_suggestions: unitSuggestions, boundary_status: boundary ?? 'continued_bounded_portion', context_preface: {required: dependent, opening_source_text: words, preceding_context_reference: previous, instruction: dependent ? 'Before translation, explain what the dependent opening follows from; retrieve enough discourse to support the summary. This nearby window is a starting point, not the entire argument.' : 'Review continuing discourse and scene; add a short context preface if needed.'}, textual_review_flags: textualCases(current, this.refs), continuation_state: state, next: logicalNext ? {command: 'Next', reference: logicalNext, instruction: 'Present the current portion only; continue when the user asks Next, preserving mode, depth, language and format. Prefer a curated literary boundary when safely bounded; never silently expand the passage under study.', ...(suggestedNext?.literary_unit_reference ? {literary_unit_reference: suggestedNext.literary_unit_reference, literary_unit_title: suggestedNext.literary_unit_title, boundary_basis: 'curated_literary_continuation'} : {})} : null, method: config('method').sequence, ...workflow(mode, depth)}, 16000);
  }
}
