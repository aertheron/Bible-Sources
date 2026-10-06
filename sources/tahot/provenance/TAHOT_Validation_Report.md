# TAHOT book split — validation report

Prepared for Mark Gatzen, 5 October 2026.

**Result: all 39 books pass the content checks.** The split preserves all 305,652 word rows from the full source and all nonempty book-body lines in their original order.

## What was checked

The uploaded `TAHOT.zip` was compared with the user's full `TAHOT(1).txt` and the eight clean-rich files in the supplied plugin. The ZIP contains exactly the expected 39 book files and passes its archive integrity check.

- Every source word reference is present exactly once, in the correct book.
- Every cell of every word row matches the full source: 12 named fields and five empty padding fields.
- Hebrew, transliteration, glosses, morphology, both variant fields, root/instance IDs, alternative IDs, the reserved conjoin field, and expanded lexical tags are preserved.
- Interlinear text, glosses, grammar, significant-variant lines, and repeated column headers are preserved. Blank-line/newline differences do not affect this comparison.
- The seven shared fields match all 305,652 rows in the existing clean-rich extracts.
- No missing, duplicated, reordered, or misplaced source word rows were found.

There are 23,261 source verse references, including numbering conventions such as Psalm title verses. The preserved data includes 1,035 rows with meaning-variant entries, 1,592 with spelling-variant entries, 5,466 with alternative Strong IDs, 4,827 with Aramaic grammar, and 21,918 with alternate Hebrew numbering. These categories can overlap.

Fourteen source rows intentionally have empty Hebrew cells, all marked `Q(K)` and carrying Ketiv information in the variant fields. They match the original and must not be discarded as malformed rows. The reserved “Conjoin word” column is empty in this source.

## Packaging correction

All uploaded files omit the source's STEPBible/Tyndale House attribution and CC BY 4.0 preface. The separate `TAHOT_Books_Verified.zip` restores the original preface before each uploaded book file. The original uploaded bytes are unchanged after that added preface.

The shared introduction already contains one harmless copy edit: “Ben Chaim edtion” has become “Ben Chaim edition”. This is recorded in the audit. The full source also ends with a stray standalone `f`; the user's split correctly leaves it outside the book data. Repeated collection-level introductions between some source books are retained as each book's shared introduction rather than treated as biblical text.

The verified ZIP also includes this report, a per-book CSV, detailed JSON results, and the reproducible check script.

## Per-book results

| Book | Source code | Word rows | Verse references | Result |
| --- | --- | ---: | ---: | --- |
| Genesis | Gen | 20,614 | 1,533 | PASS |
| Exodus | Exo | 16,713 | 1,213 | PASS |
| Leviticus | Lev | 11,950 | 859 | PASS |
| Numbers | Num | 16,413 | 1,288 | PASS |
| Deuteronomy | Deu | 14,300 | 959 | PASS |
| Joshua | Jos | 10,051 | 658 | PASS |
| Judges | Jdg | 9,901 | 618 | PASS |
| Ruth | Rut | 1,294 | 85 | PASS |
| 1 Samuel | 1Sa | 13,323 | 810 | PASS |
| 2 Samuel | 2Sa | 11,054 | 695 | PASS |
| 1 Kings | 1Ki | 13,140 | 816 | PASS |
| 2 Kings | 2Ki | 12,282 | 719 | PASS |
| 1 Chronicles | 1Ch | 10,774 | 942 | PASS |
| 2 Chronicles | 2Ch | 13,314 | 822 | PASS |
| Ezra | Ezr | 3,755 | 280 | PASS |
| Nehemiah | Neh | 5,319 | 406 | PASS |
| Esther | Est | 3,052 | 167 | PASS |
| Job | Job | 8,343 | 1,070 | PASS |
| Psalms | Psa | 19,595 | 2,577 | PASS |
| Proverbs | Pro | 6,915 | 915 | PASS |
| Ecclesiastes | Ecc | 2,988 | 222 | PASS |
| Song of Solomon | Sng | 1,249 | 117 | PASS |
| Isaiah | Isa | 16,931 | 1,292 | PASS |
| Jeremiah | Jer | 21,835 | 1,364 | PASS |
| Lamentations | Lam | 1,542 | 154 | PASS |
| Ezekiel | Ezk | 18,730 | 1,273 | PASS |
| Daniel | Dan | 5,920 | 357 | PASS |
| Hosea | Hos | 2,381 | 197 | PASS |
| Joel | Jol | 957 | 73 | PASS |
| Amos | Amo | 2,042 | 146 | PASS |
| Obadiah | Oba | 291 | 21 | PASS |
| Jonah | Jon | 688 | 48 | PASS |
| Micah | Mic | 1,396 | 105 | PASS |
| Nahum | Nam | 558 | 47 | PASS |
| Habakkuk | Hab | 671 | 56 | PASS |
| Zephaniah | Zep | 767 | 53 | PASS |
| Haggai | Hag | 600 | 38 | PASS |
| Zechariah | Zec | 3,128 | 211 | PASS |
| Malachi | Mal | 876 | 55 | PASS |

## Use in the plugin

These files preserve materially more source information than the seven-column clean-rich extracts, while retaining every shared field unchanged. Use the verified book files as the preserved TAHOT source. Add exact reference indexes and bounded passage retrieval so the study workflow can obtain complete relevant rows and variants.

TAHOT is an amalgamated study text. Its Qere selections, restored parallels (`R`), and LXX-based reconstructed Hebrew (`X`) must remain distinguishable from an unchanged Leningrad/MT witness. Preserve its English/Hebrew numbering and source marker explanations. The dataset's own header says that many listed variant categories remain to be added; this is not a comprehensive critical apparatus.

Book splitting gives clearer retrieval targets and preserves the full source content. Retrieval quality still needs passage tests; this audit establishes the split's content fidelity.

## Reproduction and scope

Run the included script against the original sources:

```bash
python tools/check_tahot.py BOOK_FOLDER --source FULL_TAHOT_FILE --rich ORIGINAL_PLUGIN_REFERENCES --output NEW_AUDIT_FOLDER
```

For this repeat check, `BOOK_FOLDER` is the original uploaded split before the added attribution prefaces. The script identifies the 39 English filenames used in the upload.

Full source bytes: `70741577`. Full source SHA-256: `3278db0c0a917a3328db3dcf811fc664e3d3947d874b35cf1cce7527ce1ae97e`. Per-book uploaded checksums are recorded in `TAHOT_Validation_Details.json`.

The checks establish fidelity to the user's complete TAHOT source and supplied plugin extracts. They do not independently validate the edition's translations, morphology, apparatus judgments, or underlying manuscripts.
