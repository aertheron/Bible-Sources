import {config, lookupKey, StudyError} from './common.js';
export class Passage {
  constructor(book, sc, sv, ec, ev) {Object.assign(this, {book, start_chapter: sc, start_verse: sv, end_chapter: ec, end_verse: ev});}
  contains(chapter, verse) {const c = Number(chapter), v = Number(verse); return (c > this.start_chapter || c === this.start_chapter && v >= this.start_verse) && (c < this.end_chapter || c === this.end_chapter && v <= this.end_verse);}
}
export class References {
  constructor() {
    this.books = config('books').books;
    this.aliases = new Map(Object.entries(this.books).flatMap(([book, row]) => [book, row.name, ...row.aliases].map(a => [lookupKey(a), book])));
    this.verses = config('base-references').verses;
  }
  book(label) {const found = this.aliases.get(lookupKey(label)); if (!found) throw new StudyError('unknown_book', `Unrecognized book: ${label}`); return found;}
  last(book, chapter) {const values = this.verses[book][chapter]; if (!values?.length) throw new StudyError('invalid_chapter', `${this.books[book].name} has no chapter ${chapter} in the selected base.`); return Math.max(...values);}
  parse(reference, allowBook = false) {
    if (typeof reference !== 'string' || reference.length > 240) throw new StudyError('reference', 'Supply a short Bible reference.');
    const text = reference.trim().replace(/[–—]/g, '-');
    if (allowBook) {
      const stripped = text.replace(/^(?:the\s+)?(?:whole(?:\s+of)?|all(?:\s+of)?|hele|heel)\s+/i, '');
      if (this.aliases.has(lookupKey(stripped))) {const book = this.book(stripped), end = Math.max(...Object.keys(this.verses[book]).map(Number)); return new Passage(book, 1, 1, end, this.last(book, end));}
    }
    const m = /^(.+?)\s+(\d+)(?::(\d+))?(?:\s*-\s*(\d+)(?::(\d+))?)?$/.exec(text);
    if (!m) throw new StudyError('reference', 'Use a reference such as Genesis 1:1-2:3 or Romans 12:1-2.');
    const book = this.book(m[1]), sc = +m[2], sv = +(m[3] ?? 1);
    let ec, ev;
    if (m[4] === undefined) {ec = sc; ev = m[3] ? +m[3] : this.last(book, sc);}
    else if (m[5] !== undefined) {ec = +m[4]; ev = +m[5];}
    else if (m[3] !== undefined) {ec = sc; ev = +m[4];}
    else {ec = +m[4]; ev = this.last(book, ec);}
    if (sc < 1 || ec < 1 || sv < 1 || ev < 1 || sv > this.last(book, sc) || ev > this.last(book, ec) || sc > ec || sc === ec && sv > ev) throw new StudyError('invalid_reference', 'The requested chapter/verse range is invalid for the named base text.');
    return new Passage(book, sc, sv, ec, ev);
  }
  label(p) {
    const name = this.books[p.book].name;
    if (p.start_chapter === p.end_chapter) {
      if (p.start_verse === 1 && p.end_verse === this.last(p.book, p.start_chapter)) return `${name} ${p.start_chapter}`;
      return `${name} ${p.start_chapter}:${p.start_verse}${p.start_verse === p.end_verse ? '' : '-' + p.end_verse}`;
    }
    return `${name} ${p.start_chapter}:${p.start_verse}-${p.end_chapter}:${p.end_verse}`;
  }
  scope(p) {
    if (p.end_chapter === p.start_chapter) return p;
    if (p.end_chapter === p.start_chapter + 1) {
      const tail = this.last(p.book, p.start_chapter) - p.start_verse + 1, head = p.end_verse;
      if (Math.min(tail, head) <= 5 && !(p.start_verse === 1 && head === this.last(p.book, p.end_chapter))) return p;
    }
    throw new StudyError('portion_scope', 'This stage accepts one chapter plus a few adjacent verses. Plan the request into sequential portions first.');
  }
  count(p) {let n = 0; for (let c = p.start_chapter; c <= p.end_chapter; c++) n += this.verses[p.book][c].filter(v => p.contains(c, v)).length; return n;}
  portions(reference) {
    const p = this.parse(reference, true), policy = config('chunking');
    try {this.scope(p); if (this.count(p) <= policy.soft_max_verses) return [{reference: this.label(p), boundary_status: 'requested_bounded_portion'}];} catch (error) {if (!(error instanceof StudyError)) throw error;}
    const out = [];
    for (let c = p.start_chapter; c <= p.end_chapter; c++) {
      const start = c === p.start_chapter ? p.start_verse : 1, end = c === p.end_chapter ? p.end_verse : this.last(p.book, c);
      if (end - start + 1 <= policy.soft_max_verses) {out.push({reference: this.label(new Passage(p.book, c, start, c, end)), boundary_status: 'chapter_or_requested_boundary'}); continue;}
      const units = policy.chapter_units[`${p.book}:${c}`];
      const bounds = units ? units.filter(([a, b]) => b >= start && a <= end).map(([a, b]) => [Math.max(start, a), Math.min(end, b)]) : Array.from({length: Math.ceil((end - start + 1) / policy.fallback_verses)}, (_, i) => [start + i * policy.fallback_verses, Math.min(start + (i + 1) * policy.fallback_verses - 1, end)]);
      out.push(...bounds.map(([a, b]) => ({reference: this.label(new Passage(p.book, c, a, c, b)), boundary_status: units ? 'curated_literary_boundary' : 'provisional_size_boundary_review_discourse'})));
    }
    return out;
  }
  next(current) {
    const p = this.parse(current), last = this.last(p.book, p.end_chapter);
    if (p.end_verse < last) return this.portions(this.label(new Passage(p.book, p.end_chapter, p.end_verse + 1, p.end_chapter, last)))[0];
    const c = p.end_chapter + 1;
    return this.verses[p.book][c] ? this.portions(`${this.books[p.book].name} ${c}`)[0] : null;
  }
}
