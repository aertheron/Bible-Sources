import {bounded, pick, StudyError} from './common.js';
import {References} from './reference.js';
import {bundle, decode} from './store.js';

export function surfaceTokens(text, prefix) {
  const characters = [...text, ' '], out = [];
  let start = null;
  for (let i = 0; i < characters.length; i++) {
    const c = characters[i], isLetter = /[\p{L}\p{M}]/u.test(c);
    if (isLetter || start !== null && '’᾽\''.includes(c)) {if (start === null) start = i;}
    else if (start !== null) {out.push({id: `${prefix}:token:${out.length + 1}`, form: characters.slice(start, i).join(''), start, end: i, annotation_layer: 'runtime_surface_tokenization_no_lemma_or_morphology'}); start = null;}
  }
  return out;
}
export class Reader {
  constructor(store, refs = new References()) {this.store = store; this.refs = refs; this.chapters = bundle.chapters;}
  async nativeChapter(dataset, book, chapter, detail = 'text') {
    const pointer = this.chapters[`${dataset}|${book}|${chapter}`];
    if (!pointer) return {dataset_id: dataset, native_book: book, chapter, records: [], coverage_status: 'no_indexed_native_chapter', warnings: ['Missing dataset coverage is not evidence of omission.']};
    const raw = decode(await this.store.span(pointer)), records = [];
    for (const line of raw.split(/\r?\n/)) {
      if (!line) continue;
      if (dataset === 'TAHOT') {
        const fields = 'locator form transliteration english_gloss disambiguated_strong morphology meaningful_variants spelling_variants simple_strong_instance alternate_strong conjoin_word expanded_strong'.split(' ');
        const cells = line.split('\t'), m = /[^.]+\.(\d+)\.(\d+).*?#.*?=(.*)/.exec(cells[0]);
        if (!m) continue;
        records.push({...Object.fromEntries(fields.map((f, i) => [f, cells[i] ?? ''])), id: 'TAHOT:' + cells[0], chapter: +m[1], verse: +m[2], flags: m[3], extra_columns: cells.slice(12)});
      } else if (dataset === 'SBLGNT') {
        const m = /^([^\t]+?) (\d+):(\d+)\t(.*)$/.exec(line); if (!m) continue;
        const row = {id: `SBLGNT:${book}:${m[2]}:${m[3]}`, chapter: +m[2], verse: +m[3], native_reference: `${book} ${m[2]}:${m[3]}`, text: m[4]};
        if (detail === 'linguistic') row.tokens = surfaceTokens(row.text, row.id);
        records.push(row);
      } else {
        const item = JSON.parse(line); let row;
        if (dataset === 'wlc-4.20-oshb') {
          row = {id: item.record_id, ...pick(item, ['chapter', 'verse', 'body_policy', 'qere_readings', 'structured_notes', 'reading_status', 'reference_system']), text: item.derived_body_text};
          if (detail === 'linguistic') row.words = item.source_words.map(w => ({id: w.record_id, source_word_id: w.source_word_id, form: w.display_form, raw_segmented_form: w.raw_segmented_form, role: w.reading_role, annotations: w.source_attributes, annotation_layer: w.annotation_layer}));
        } else if (dataset === 'uxlc-2.4') row = {id: item.record_id, ...pick(item, ['chapter', 'verse', 'qere_ketiv_markers', 'transcription_note_markers', 'reading_status', 'reference_system']), text: item.text_with_source_markup};
        else {row = {id: `${dataset}:${book}:${item.chapter}:${item.verse_label}`, chapter: item.chapter, verse: item.verse_number, native_verse_label: item.verse_label, text: item.text, source_lines: item.source_lines}; if (detail === 'linguistic') row.tokens = surfaceTokens(row.text, row.id);}
        records.push(row);
      }
    }
    return {dataset_id: dataset, native_book: book, chapter, evidence: this.store.evidence(pointer), records, coverage_status: 'indexed_source_span_verified'};
  }
  async passage(reference, sources = null, detail = 'text') {
    if (!['text', 'linguistic'].includes(detail)) throw new StudyError('detail', 'Detail must be text or linguistic.');
    const portions = this.refs.portions(reference), p = this.refs.parse(portions[0].reference), routes = this.refs.books[p.book].routes;
    if (sources === null) sources = (routes.WLC ? ['WLC', 'LXX'] : ['SBLGNT']).filter(s => routes[s]);
    if (!Array.isArray(sources) || sources.length < 1 || sources.length > 4 || sources.some(s => !['WLC', 'UXLC', 'TAHOT', 'LXX', 'SBLGNT'].includes(s))) throw new StudyError('sources', 'Select one to four named public editions: WLC, UXLC, TAHOT, LXX, SBLGNT.');
    const packets = [];
    for (const source of new Set(sources)) {
      if (!routes[source]) {packets.push({source, records: [], coverage_status: 'edition_not_available_for_this_book'}); continue;}
      const [dataset, nativeBook] = routes[source];
      for (let c = p.start_chapter; c <= p.end_chapter; c++) {const packet = await this.nativeChapter(dataset, nativeBook, c, detail); packet.records = packet.records.filter(r => p.contains(r.chapter, r.verse)); packet.source = source; packets.push(packet);}
    }
    return bounded({requested_reference: reference, current_portion: this.refs.label(p), pending_references: portions.slice(1).map(x => x.reference), boundary_status: portions[0].boundary_status, source_packets: packets, alignment_status: 'native_number_candidate_retrieval_not_verified_verse_equivalence', warnings: ['Native chapter/verse labels are preserved. Verify cross-edition numbering and literary form before collating.', 'WLC and UXLC are transcriptions of the same Leningrad manuscript, not independent votes.', 'TAHOT Q/R/X annotations remain explicit; restored or reconstructed text is not unqualified manuscript evidence.']});
  }
  async apparatus(reference) {
    const portions = this.refs.portions(reference), p = this.refs.parse(portions[0].reference);
    if (this.refs.books[p.book].testament !== 'NT') return {reference: this.refs.label(p), entries: [], coverage_status: 'no_OT_critical_apparatus_imported'};
    const path = `sources/sblgnt/apparatus/${p.book}.txt`, raw = decode(await this.store.read(path));
    const headers = [...raw.matchAll(/^[^\n\t]+? (\d+):(\d+)[ \t]*$/gm)], entries = [];
    headers.forEach((match, i) => {if (p.contains(match[1], match[2])) entries.push({native_reference: match[0].trim(), text: raw.slice(match.index, headers[i + 1]?.index ?? raw.length).trimEnd()});});
    return bounded({reference: this.refs.label(p), pending_references: portions.slice(1).map(x => x.reference), entries, source_file: path, source_commit: this.store.profile.commit, source_sha256: this.store.profile.metadata_hashes[path], coverage_status: 'edition_comparison_apparatus_not_full_manuscript_apparatus', warnings: ['No listed entry does not establish that a passage has no textual variants.']});
  }
  async dss(reference, cursor = 0, limit = 1, includeLinguistics = true) {
    if (!Number.isSafeInteger(cursor) || cursor < 0 || !Number.isSafeInteger(limit) || limit < 1 || limit > 3 || typeof includeLinguistics !== 'boolean') throw new StudyError('dss_page', 'Use a nonnegative cursor, one to three physical records, and a boolean linguistic option.');
    const portions = this.refs.portions(reference), p = this.refs.parse(portions[0].reference), book = this.refs.books[p.book].dss_book;
    const rows = (bundle.dss_rows[book] ?? []).filter(([c, v]) => p.contains(c, v));
    if (cursor > rows.length) throw new StudyError('dss_page', 'Cursor exceeds available physical records.');
    const selected = rows.slice(cursor, cursor + limit), records = [], statuses = new Map(), packs = new Map();
    for (const [c, v, n] of selected) {
      const key = `${c}:${v}`;
      if (!packs.has(key)) packs.set(key, await this.store.dssVerse(book, c, v));
      const pack = packs.get(key), item = structuredClone(pack.records[n]);
      if (!includeLinguistics) delete item.linguistics;
      records.push(item);
      for (const status of pack.passage_status) if ((status.item.metadata.record_ids.match(/L\d+-R\d+/g) ?? []).includes(item.metadata.record_id)) statuses.set(status.order, status.item);
    }
    const following = cursor + selected.length;
    return bounded({reference: this.refs.label(p), pending_references: portions.slice(1).map(x => x.reference), total_records: rows.length, cursor, next_cursor: following < rows.length ? following : null, records, passage_status: [...statuses].sort(([a], [b]) => a - b).map(([, s]) => s), status_scope: 'whole_indexed_scroll_passage_for_returned_physical_records; counts_may_extend_beyond_the_current_page', coverage_status: rows.length ? 'indexed_physical_records' : 'no_indexed_DSS_record_not_evidence_of_omission', licence: 'CC BY-NC 4.0', attribution: 'Abegg, Bowley and Cook; TF conversion by Jacobs, Naaijer and Roorda; ETCBC/dss 2.0.1', warnings: ['Reconstructed letters are editorial readings; preserve their explicit status.', 'Unmarked letters have not been independently verified as secure ink.', 'Sign-slot totals are not the fraction of an entire biblical verse that survives.', 'Modern lexeme pointing and derived grammar are analytical annotations.', 'Individual scrolls and their relationships matter; DSS is not one independent vote.']});
  }
}
