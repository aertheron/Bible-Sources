import {bounded, charCount, config, lookupKey, pick, strings, StudyError} from './common.js';
import {decode} from './store.js';
export class Knowledge {
  constructor(store) {this.store = store;}
  async word(query, contextIds = null) {
    if (typeof query !== 'string' || !query.trim() || charCount(query) > 300) throw new StudyError('word_query', 'Supply a word, theme, study ID or lexical ID.');
    const index = await this.store.json('indexes/word-study-index.json');
    if (Object.hasOwn(index.sense_records, query)) {const pointer = index.sense_records[query]; return bounded({query, status: 'contextual_sense_record', record: JSON.parse(decode(await this.store.span(pointer))), evidence: this.store.evidence(pointer)}, 12000);}
    const studies = Object.fromEntries(index.studies.map(r => [r.id, r]));
    let ids = [];
    if (Object.hasOwn(studies, query.toUpperCase())) ids = [query.toUpperCase()];
    else if (Object.hasOwn(index.lookup_base_strong, query.toUpperCase())) ids = index.lookup_base_strong[query.toUpperCase()];
    else for (const [label, values] of Object.entries({...index.lookup_terms, ...config('word-aliases').aliases})) if (lookupKey(label) === lookupKey(query)) ids.push(...values);
    ids = [...new Set(ids)];
    const candidates = () => ids.map(id => ({id, title: studies[id].title}));
    if (ids.length > 2) return {query, status: 'choose_one', candidates: candidates()};
    if (!ids.length) return {query, status: 'no_curated_entry', entries: [], next_entry_id: index.next_entry_id, guidance: "Perform a bounded source-based study; submit a reviewed addition using the collection's update process. Do not publish drafts automatically."};
    if (contextIds !== null && !strings(contextIds, 6)) throw new StudyError('word_contexts', 'Select up to six contextual record IDs.');
    const entries = []; let remaining = 6;
    for (const id of ids) {
      const row = studies[id], entry = JSON.parse(decode(await this.store.span(row.entry_record))), senses = [];
      for (const i of row.sense_ids) senses.push(pick(JSON.parse(decode(await this.store.span(index.sense_records[i]))), ['id', 'base_strong', 'label', 'contextual_summary', 'references']));
      const chosen = contextIds === null ? row.context_ids : contextIds.filter(i => row.context_ids.includes(i)), contexts = [];
      for (const cid of chosen.slice(0, remaining)) {const pointer = index.context_records[cid], context = JSON.parse(decode(await this.store.span(pointer))); contexts.push({...pick(context, ['id', 'entry_id', 'reference', 'source_id', 'numbering', 'range_all_verses_present']), record_pointer: this.store.evidence(pointer)});}
      remaining -= contexts.length;
      entries.push({entry, evidence: this.store.evidence(row.entry_record), review: row.review, contextual_senses: senses, context_pointers: contexts, deferred_context_ids: chosen.slice(contexts.length), related_entry_ids: row.related_entry_ids});
    }
    const packet = {query, status: 'curated_entries', entries, coverage: '50 authored model-assisted studies; selected lexical sources, not an exhaustive concordance or independent peer review.', sense_record_access: 'Use lookup_word with an exact sense ID to retrieve its complete annotation/provenance record.', related_entries_loaded: false};
    const limit = config('method').budgets.word_packet_characters;
    if (ids.length === 1) {const item = entries[0]; while (item.context_pointers.length && charCount(JSON.stringify(packet)) > limit) item.deferred_context_ids.unshift(item.context_pointers.pop().id);}
    try {return bounded(packet, limit);} catch (error) {if (!(error instanceof StudyError)) throw error; if (ids.length === 2) return {query, status: 'choose_one', reason: 'Two complete entries exceed the normal packet budget.', candidates: candidates()}; throw error;}
  }
  async lexical(entryId) {
    if (typeof entryId !== 'string' || charCount(entryId) > 100) throw new StudyError('lexical_query', 'Supply a selected lexical record ID.');
    const index = await this.store.json('indexes/lexical-entry-index.json'), pointers = Object.hasOwn(index, entryId) ? index[entryId] : Object.hasOwn(index, entryId.toUpperCase()) ? index[entryId.toUpperCase()] : [], records = [];
    for (const p of pointers.slice(0, 6)) records.push({record: JSON.parse(decode(await this.store.span(p))), evidence: this.store.evidence(p)});
    return bounded({entry_id: entryId, records, coverage: '606 selected STEP/OSHB supporting records. Full upstream lexicons and a corpus-wide Greek lemma layer are not imported.', total_candidates: pointers.length}, 12000);
  }
  async trajectory(query) {
    if (typeof query !== 'string' || charCount(query) > 300) throw new StudyError('trajectory_query', 'Supply a short theme name.');
    const seed = config('trajectories'), dossiers = seed.dossiers.filter(d => [d.id, ...d.aliases].some(x => lookupKey(x) === lookupKey(query)));
    return bounded({query, dossiers: dossiers.slice(0, 1), status: seed.status, anchors_loaded: false, anchor_budget: 6, research_leads: (await this.store.json('resources/research-links.json')).resources.slice(0, 2), guidance: 'Retrieve only the anchors needed to answer the question. Distinguish quotation, echo, typology and thematic development. Do not fetch every Bible book.'}, 8000);
  }
}
