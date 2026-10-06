# Attribution and source handling

## Original authored material

The 50 contextual studies, translation keys, targeted sense summaries, and associated notes are original model-assisted writing prepared for Mark Gatzen. Linked BibleProject and Canonical Theology resources identify discovery leads, methodological material, or attributed project interpretations. They are not represented as sources for every sentence, and full videos, transcripts, or articles are not mirrored in this package. BibleProject videos have not been labeled watched merely because a landing page or transcript was accessed.

## STEP Bible

Selected Greek records and Hebrew identifier metadata are based on data created by [STEP Bible](https://www.stepbible.org/) and Tyndale House Cambridge, from [STEPBible-Data](https://github.com/STEPBible/STEPBible-Data), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The inspected source files identify historical Abbott-Smith material, supplemented where indicated, and formatted LSJ material. See `sources/dataset_manifest.json` for exact filenames, source hashes, and pinned commit.

Changes here consist of selecting relevant records, removing HTML markup, decoding character entities, exposing source identifiers and line locations, and adding separate authored notes. Original extended IDs and parent IDs are preserved. Historical definitions are not claimed as independently corrected modern scholarship; questionable or disputed glosses are flagged in the relevant authored entries.

The source permits incorporation of parts into software/publications and requests that users obtain original datasets from STEP for updates. This package incorporates selected supporting records and points to the original; it does not redistribute a standalone mirror of the full lexicons. No endorsement by STEP or Tyndale House is implied.

The TBESH Hebrew header also requests Online Bible permission for the brief-definition prose. That prose and its brief glosses are excluded here. Hebrew STEP metadata supplies identifiers and lemma links only; the Hebrew prose supplement instead uses the Open Scriptures material below.

## Open Scriptures Hebrew Bible Project

Selected lexical-index bindings and BDB outlines are based on the [Open Scriptures Hebrew Lexicon](https://github.com/openscriptures/HebrewLexicon), credited to the **Open Scriptures Hebrew Bible Project**, under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Underlying BDB and Strong dictionary text is public domain according to the repository's notice.

Changes consist of selecting records, joining their explicitly supplied lexical-index/BDB identifiers, extracting definition text, and normalizing XML text into structured fields. Distinct source entries, homonyms, and editing statuses remain separate. The BDB transcription is a work in progress. Two selected bindings have no definition outline in the inspected file; this is recorded rather than filled with invented BDB prose. TWOT numbers do not provide TWOT definitions, and none are reproduced here.

The retrieved master-file bytes are identified by SHA-256 and access date. No unverified commit is assigned to them, and no endorsement by the project is implied.

## SBL Greek New Testament

Selected Greek biblical excerpts are from the **SBL Greek New Testament**, edited by Michael W. Holmes. Copyright © 2010 [Society of Biblical Literature](https://www.sbl-site.org/) and [Logos Bible Software](https://www.logos.com/). The publisher source is available through [SBLGNT](https://www.sblgnt.com/) and [Faithlife/SBLGNT](https://github.com/Faithlife/SBLGNT), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); see the [current license](https://www.sblgnt.com/license/).

The main-context exports are selected directly from the 27 separate user-supplied clean book files, with verse labels, editorial markers, and exact book-file/line/hash locators preserved. The 27 apparatus files remain a separate source set. Selection and conversion to JSON are the modifications; no complete new Greek edition is claimed. Romans source and apparatus at the pinned publisher commit were separately checked to resolve the doxology's main-text/apparatus location. No endorsement by the editor, SBL, Logos, or Faithlife is implied. The SBLGNT apparatus is an edition-comparison apparatus, not a full NA28 manuscript apparatus.

## TAHOT and the supplied Greek OT

Selected Hebrew evidence is from the user-supplied **Translators Amalgamated Hebrew OT (TAHOT)**, created by **STEP Bible based on work at Tyndale House Cambridge**, under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The source header credits Westminster Leningrad text WLC 4.20 via Open Scriptures for the Hebrew basis and ETCBC for morphology, with the stated Tyndale corrections and additions. Obtain the original data through [STEPBible-Data](https://github.com/STEPBible/STEPBible-Data); no endorsement by these projects is implied.

Changes here consist of selecting word records, retaining their original forms, supplied transliteration/glosses, dStrong identifiers and morphology, and converting them to JSON with source locators. This archive does not replace or mirror the full corpus. The complete original TAHOT attribution and field/variant notices must accompany that corpus during integration; the already attribution-restored book package remains separate. Fetch the full source record for Qere/Ketiv and variant details beyond these selected evidence fields. TAHOT's Qere, restored, and reconstructed additions must not be mistaken for a separate diplomatic WLC witness.

The supplied LXX export's edition and redistribution status remain unresolved. Its Leviticus 18:22 and 20:13 wording was spot-checked, but the package stores locators, hashes, and a short description of the relationship rather than reproducing that unidentified corpus. Do not use this check as a claim of independent critical-edition or manuscript collation.

## Historical dictionary and separate lexicon displays

[Easton's Seal entry via CCEL](https://ccel.org/ccel/easton/ebd2.s.html?term=seal) was inspected as limited background. Its 1897 date and historical perspective are explicit; no complete dictionary or unverified modern archaeology is imported. Separate BDB/Thayer displays are identified in the source register as cross-checks of the historical entries, not endorsements of accompanying website commentary.

## Review claims

“Inspected” means that relevant source records or textual forms were accessed and considered in preparing the entries. “Present” means that the corpus contains the expected verse rows. Neither term means independent peer review, current consensus, automatic local-sense tagging, or that every historical and theological assertion in a source has been accepted.

## Public repository edition — 6 October 2026

This publication contains the 50 studies and their structured entries, targeted sense summaries, selected passage evidence and source register. The separate website correction log, original combined draft, SQLite database and processing scripts remain outside this public collection.

The studies' arguments are unchanged. The lexical-record reference now links to this repository's existing 606 selected source records. English discovery aliases were added to the lookup index. Internal file identifiers were removed from structured locators; verified public book paths and hashes were added. Source identifiers, review qualifications, original terms and variant markers remain visible. Historical preparation hashes remain distinct from public book-file hashes.

The historical unresolved Greek OT pointer is retained as a preparation record. Its corpus and excerpts are not published, and it is not a shared retrieval fallback. This update adds no blanket redistribution licence for the original authored prose. Upstream source material retains the terms documented here and in the repository's source notices.
