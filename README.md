# Bible-Sources

Public source data and study software for AI-assisted Bible study, maintained by Mark Gatzen. This repository holds identified texts, linguistic data, source notes, curated studies, retrieval indexes and the first public plugin MVP.

## Study plugin

*Study Scripture through its languages, context, and canonical story.*

[Canonical Scripture Study](plugins/canonical-scripture-study/) includes eight modular skills, a pinned source retrieval CLI, an optional read-only local MCP server, study commands and three translation formats. It combines biblical theology, canonical theology and contextual working translation, with explicit textual evidence and a correctable working-theology framework. Larger requests become sequential portions with **Next**, preserving language, mode and format. See its README for setup, examples, checks and remaining limitations.

This public package is not yet a hosted ChatGPT connection or a public Plugins Directory listing. The runtime and skills are MIT licensed; source data retains its own terms.

## Included sources

| Source | Published material | Identity and terms |
| --- | --- | --- |
| [TAHOT](sources/tahot/) | All 39 attribution-restored book files; 305,652 word rows with the full source fields | STEP Bible / Tyndale House Cambridge; CC BY 4.0. An amalgamated study text, with Qere, restored parallels and Greek-based Hebrew reconstruction explicitly marked. |
| [WLC through OSHB](sources/leningrad/original/wlc_4_20_oshb/) | All 39 pinned OSIS XML books, including word IDs, lemmas, morphology, Qere/Ketiv and source notes | WLC 4.20 as distributed by Open Scriptures Hebrew Bible, revision `3d15126fb1ef74867fc1434be1942e837932691f`. WLC text public domain; OSHB annotations CC BY 4.0. |
| [UXLC](sources/leningrad/original/uxlc_2_4/) | All 39 original TXT books, UXLC 2.4, Build 27.5 | Unicode/XML Leningrad Codex; publisher permits copying biblical Hebrew text. Proper edition identity retained. |
| [SBLGNT](sources/sblgnt/) | All 27 clean main-text books and all 27 apparatus books, kept separate; 7,939 main-text verse rows | Edited by Michael W. Holmes; Society of Biblical Literature / Logos Bible Software; CC BY 4.0. The apparatus compares editorial editions. |
| [Brenton Greek LXX](sources/lxx/brenton/) | 52 native book files, original eBible USFM and 28,597 structured verse records | Identified eBible `grcbrent` distribution dated 8 April 2026; public domain. Native references and Greek form identity retained. |
| [DSS TF and enriched exports](sources/dss/2.0.1/) | All 79 supplied TF feature files, marked readings, passage reconstruction summaries, linguistic tables and physical-location indexes | ETCBC/Abegg Text-Fabric release 2.0.1; CC BY-NC 4.0. All 500,995 word nodes and 1,430,241 sign slots remain accounted for in the prepared exports. |
| [Selected lexical data](sources/lexical/) | 606 attributed supporting records: 500 STEP records and 106 Open Scriptures bindings/outlines | CC BY 4.0; selected source data supporting the initial word-study vocabulary. Full upstream lexicons are identified by download URLs and hashes. TBESH definition/gloss prose is excluded. |

See [source-specific attribution and terms](ATTRIBUTION.md). The DSS dataset retains its noncommercial condition; the repository does not grant one blanket licence over every source.

## Curated study knowledge

[Word and theme studies](knowledge/word-studies/) contains the first 50 enriched studies, with contextual translation keys, biblical/canonical development, source pointers and review status. These are original model-assisted study explanations, not another text edition or an independent manuscript witness. The collection can grow as further studies are completed; [the update process](knowledge/word-studies/UPDATING.md) retains stable IDs and a checked [lookup index](indexes/word-study-index.json).

## Retrieval layout

Source books are unpacked and directly readable. Original files are preserved byte for byte where indicated in [the preservation record](provenance/exact-source-file-preservation.json). The [file manifest](provenance/repository-file-manifest.json) identifies the exact files in this public snapshot.

- [Book catalogue](indexes/book-catalog.json): source identity, book file, chapter coverage, record counts and hashes.
- [Chapter index](indexes/chapter-index.jsonl): 4,150 native chapter spans with file paths, byte offsets, lengths and checksums. Counts refer to the record type of that source, such as word rows or verse records.
- [DSS lookup indexes](indexes/dss/): smaller per-book copies of the physical-record and passage-status indexes. They retain original rows and locators; file paths within those rows are relative to `sources/dss/2.0.1/enriched/`.
- [Lexical entry index](indexes/lexical-entry-index.json): entry IDs and exact byte locations, retaining multiple candidates where needed.
- Structured verse JSONL files for WLC/UXLC and Brenton are split by book. Compact Leningrad records retain reading and word data; duplicate serialized views are omitted because the original XML/TXT remains available.

For a study request, the MVP selects the current portion, retrieves small verified native spans and passes bounded packets to the study pipeline. It can read a local checkout or lazily cache pinned GitHub data. The study host performs translation and interpretation using the skills; automatic reviewed cross-edition alignment remains future work. Repository retrieval does not require loading all these files into one model context or uploading them all as Custom GPT knowledge. Model context budgets still apply.

Larger references become a sequence: Genesis 1–2 gives chapter 1 first and chapter 2 on Next; Genesis 1:1–2:3 remains a single literary portion. Very long chapters use smaller portions. A whole-book request starts a bounded sequence instead of an unrestricted whole-book translation.

## Reading and evidence

Preserve the distinction between the physical manuscript, its modern edition, modern linguistic annotations and an interpretation. WLC and UXLC are related transcriptions of the same Leningrad manuscript, not two independent ancient witnesses. TAHOT's added/restored readings must retain their own status. WLC readable body exports include Ketiv, with Qere separately labelled; UXLC reading asterisks and transcription codes remain explicit.

DSS reconstruction, uncertainty, corrections and missing signs remain visible. Missing dataset coverage does not establish a manuscript omission. Analytical lexeme pointing and automatically derived morphology must not be described as surviving ink or independently reviewed analysis. Nonbiblical and unmapped material remains separately labelled.

Reference systems are native to their source. Hebrew and English chapter/verse numbers can differ; Brenton includes lettered verse labels and book/form differences. Cross-edition maps remain to be reviewed before automatic collation. No full critical apparatus is claimed for these datasets.

No Unicode normalization is applied during this repository preparation. Git text conversion is disabled to preserve source bytes and offsets. Source transcriptions and annotation values have not been silently corrected.

## Sources kept elsewhere or pending

The personal Rahlfs/CCAT export is excluded from this public repository. Swete remains pending corpus ingestion and verification. The 50 word/theme studies are published in the curated knowledge directory. Separate unpublished study drafts and private editorial corrections remain outside this snapshot. The MVP's code, skills and reviewable policies are now public in the plugin directory.

BibleProject and scholarly/contextual resources remain [attributed research links](resources/research-links.json), without mirroring their articles, videos or commentary collections. A link is a research lead, not a claim that every resource has been imported or reviewed.

Upstream repositories remain authoritative for their releases and updates. Report suspected source errors to the original maintainers and preserve their edition/version history. See [the transformation notes](provenance/public-data-transformations.json) and the source-specific notices before reusing the data.
