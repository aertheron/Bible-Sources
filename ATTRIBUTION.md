# Attribution and source-specific terms

This repository combines separately licensed datasets. It does not replace their terms with a single repository-wide licence. Preserve the relevant attribution, edition, modification notice and licence link when redistributing any source or derived record. No source publisher endorses this repository or its study tool.

## STEP Bible / TAHOT

Data created by STEPBible.org based on work at Tyndale House Cambridge, under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Original releases and updates: https://github.com/STEPBible/STEPBible-Data.

The 39 TAHOT book splits retain all 305,652 word rows and the richer original fields. Their source attribution/licence preface was restored during preparation. Book filenames were made easier to use in paths; the file bytes remain those of the verified, attribution-restored package. The existing split fixes a method-preface typo and omits a stray nonbiblical trailing character; see its retained validation report. No biblical row was silently edited. Keep the source's Qere/restored/reconstructed conventions and its original prefaces.

STEP asks users to obtain original data and updates from its repository. These attributed, application-oriented book files and selected lexical records are maintained with original-source links and hashes; use upstream for authoritative releases.

## Westminster Leningrad Codex / Open Scriptures Hebrew Bible

Original work of the Open Scriptures Hebrew Bible available at https://github.com/openscriptures/morphhb

The WLC text is public domain according to the source distribution. OSHB lemma/morphology work is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The exact pinned [README](sources/leningrad/original/wlc_4_20_oshb/README.md) and [licence](sources/leningrad/original/wlc_4_20_oshb/LICENSE.md) are retained.

All 39 book headers declare WLC 4.20. Snapshot: `3d15126fb1ef74867fc1434be1942e837932691f`. Changes consist of additional readable views, structured verse records and indexes. Original XML files are unchanged. Modern annotations remain explicitly identified.

## Unicode/XML Leningrad Codex

Unicode/XML Leningrad Codex 2.4, Build 27.5, https://tanach.us/.

The publisher [permits unrestricted copying of biblical Hebrew text](https://tanach.us/License.html) and requests citation. Site software, design and fonts have separate terms and are excluded. Keep the proper UXLC name. The upload's export build date and publisher release date are separately recorded in its source manifest.

Original TXT bytes are unchanged. Derived views remove directional controls only from the processing view and keep reading/note markup. See [source rights and note conventions](sources/leningrad/SOURCE_RIGHTS_AND_NOTES.md).

## SBL Greek New Testament

SBL Greek New Testament, edited by Michael W. Holmes. Copyright © 2010 Society of Biblical Literature and Logos Bible Software. Publisher: https://www.sblgnt.com/. Data repository: https://github.com/Faithlife/SBLGNT. Current publisher licence: [CC BY 4.0](https://www.sblgnt.com/license/).

The 27 main-text and 27 apparatus files are the separate user-supplied clean exports. Their Greek text, editorial markers and source labels are unchanged. Additions are attribution, checksums, organization and lookup indexes. These exports are not represented as a full manuscript-by-manuscript NA28/UBS5 apparatus.

## Brenton Greek LXX

Greek Septuagint with Apocrypha, compiled by Sir Lancelot C. L. Brenton, as distributed by eBible.org, publisher ID `grcbrent`, source date 8 April 2026. Source: https://ebible.org/bible/details.php?id=grcbrent. [Publisher public-domain declaration](https://ebible.org/grcbrent/copyright.htm).

Original USFM and edition metadata are preserved. Prepared TXT and structured verse files preserve the native wording, verse labels and paragraph continuations. Additional splitting and indexes do not provide missing books, morphology or a critical apparatus. Do not assume every Greek Daniel/Esther form or numbering system is interchangeable.

## Dead Sea Scrolls — ETCBC / Abegg

Original attribution: Martin G. Abegg, Jr., James E. Bowley and Edward M. Cook. Original conversion: Jarod Jacobs, Martijn Naaijer and Dirk Roorda; ETCBC/CACCHT project. Source repository: https://github.com/ETCBC/dss. Release label: Text-Fabric 2.0.1. Feature/provenance information is retained with the data.

Source terms: [Creative Commons Attribution-NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/). The noncommercial condition applies to this dataset and its derivatives.

Changes consist of marked reading exports, reconstruction/status summaries, modern linguistic joins, physical-location indexes and additional smaller per-book lookup files. Original TF files and source values remain intact. The enriched data includes model/parsing layers that are distinguished from source transcription. Independent scroll-image examination is not claimed.

The original prepared package included processing tools; these are excluded from this public data snapshot. Its original full-package checksum record is retained in `sources/dss/2.0.1/provenance/`. Use this repository's file manifest for checks of the published snapshot.

## Selected lexical records

STEP Bible / Tyndale House Cambridge: selected TBESG/TFLSJ Greek source records and selected TBESH Hebrew identifier metadata, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Source releases: https://github.com/STEPBible/STEPBible-Data. Pinned files and hashes are identified in [the lexical source manifest](sources/lexical/upstream_dataset_manifest.json).

Open Scriptures Hebrew Bible Project: selected lexical bindings and BDB outlines from https://github.com/openscriptures/HebrewLexicon, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Underlying BDB/Strong dictionary prose is public domain according to its source notice; the transcription is a work in progress.

Changes consist of selecting entries, exposing original identifiers and locators, joining declared bindings, removing HTML and normalizing XML display text into fields. Preserve homonyms, extended IDs and editing/coverage states. TBESH definition and gloss prose is excluded because its header has an additional Online Bible permission notice. No TWOT definitions are included. These 606 records are selected supporting data, not a full lexical corpus or a count of independently verified meanings.

## Linked secondary resources

BibleProject, Canonical Theology, Yale, Bible Odyssey and other listed resources retain their own rights. This repository contains links and short catalogue descriptions only; no complete articles, videos, transcripts or modern commentary corpora are reproduced.

## Curated word and theme studies

The 50 studies are original model-assisted material prepared for Mark Gatzen, with contextual translation guidance and biblical/canonical interpretation. See [the collection attribution](knowledge/word-studies/ATTRIBUTION.md) for source evidence, access/review claims and modifications. The collection reuses this repository's selected lexical records and adds selected SBLGNT/TAHOT evidence; their original terms remain in force. No complete linked articles or videos are mirrored.
