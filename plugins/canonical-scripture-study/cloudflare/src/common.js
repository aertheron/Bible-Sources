import books from '../../bible_study/config/books.json' with {type: 'json'};
import base from '../../bible_study/config/base-references.json' with {type: 'json'};
import chunking from '../../bible_study/config/chunking.json' with {type: 'json'};
import literary from '../../bible_study/config/literary-units.json' with {type: 'json'};
import method from '../../bible_study/config/method.json' with {type: 'json'};
import profile from '../../bible_study/config/source-profile.json' with {type: 'json'};
import cases from '../../bible_study/config/textual-cases.json' with {type: 'json'};
import trajectories from '../../bible_study/config/trajectories.json' with {type: 'json'};
import wordAliases from '../../bible_study/config/word-aliases.json' with {type: 'json'};
import manifest from '../../plugin.json' with {type: 'json'};

export const configs = {books, 'base-references': base, chunking, 'literary-units': literary, method, 'source-profile': profile, 'textual-cases': cases, trajectories, 'word-aliases': wordAliases};
export const VERSION = manifest.version;
export const config = name => configs[name];
export class StudyError extends Error {
  constructor(code, message) {super(message); this.code = code;}
  asDict() {return {error: {code: this.code, message: this.message}};}
}
export const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
export const exactKeys = (value, keys) => isObject(value) && Object.keys(value).length === keys.length && keys.every(k => Object.hasOwn(value, k));
export const nonempty = x => typeof x === 'string' && Boolean(x.trim());
export const strings = (x, max = Infinity) => Array.isArray(x) && x.length <= max && x.every(v => typeof v === 'string');
// Python's packet budgets and surface offsets count Unicode codepoints, not UTF-16 units.
export const charCount = text => [...text].length;
export function bounded(value, limit = 60000) {
  const size = charCount(JSON.stringify(value));
  if (size > limit) throw new StudyError('packet_budget', `Packet has ${size} characters; limit ${limit}. Retrieve fewer verses, witnesses or records and merge concise findings at the next stage.`);
  return value;
}
export const lookupKey = value => value.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '').replace(/[\s_.-]+/g, '');
export const pick = (object, keys) => Object.fromEntries(keys.filter(k => Object.hasOwn(object, k)).map(k => [k, object[k]]));
export const FORMATS = new Set(['plain_working', 'transliteration_interlinear', 'original_interlinear']);
export function validatePreferences(language, format) {
  if (typeof language !== 'string' || !/^[a-z]{2,3}(?:-[A-Za-z]{2,8})?$/.test(language)) throw new StudyError('language', 'Use a language code such as en, nl or es.');
  if (!FORMATS.has(format)) throw new StudyError('translation_format', 'Use plain_working, transliteration_interlinear or original_interlinear.');
}
