# Source rights and transcription notes

Checked 6 October 2026. Preserve this notice and the source-specific licences with the package.

## UXLC 2.4

The publisher permits unrestricted viewing and copying of its biblical Hebrew text and asks users to cite the source. It specifically distinguishes UXLC from WLC. Cite: Unicode/XML Leningrad Codex 2.4, Build 27.5, https://tanach.us/.

The permission for biblical Hebrew text does not extend automatically to the publisher's site software, design or font files. Those files are not included in this package. The scripts here were created for this conversion and are not copied site code.

Primary documentation:

- [Licence](https://tanach.us/License.html)
- [About the edition](https://www.tanach.us/Pages/About.html)
- [Text-file conventions](https://www.tanach.us/Pages/TextFiles.html)
- [Editorial changes and releases](https://www.tanach.us/Pages/Changes.html)
- [Publisher transcription-note legend](https://tanach.us/Books/TanachHeader.xml)

The following is a short paraphrase of the publisher's current note legend for the codes found in the supplied UXLC 2.4 export. Counts are occurrences of bracketed codes in verse bodies, not counts of distinct words.

| Code | Occurrences | Meaning |
| --- | ---: | --- |
| `4` | 16 | Extraordinary dots above or below letters; not a supplied-vowel flag. |
| `5` | 4 | Enlarged letters. |
| `6` | 3 | Reduced-size letters. |
| `7` | 4 | Suspended letters. |
| `8` | 9 | Inverted nun. |
| `c` | 101 | A peculiar form is accepted as matching the Leningrad Codex. |
| `d` | 27 | Tipeha here where other texts show dehi. |
| `m` | 39 | Meteg here where other texts show merkha. |
| `q` | 35 | A UXLC Qere differs from the conventional Qere form. |
| `t` | 218 | Uncertain transcription; inspect the manuscript image for alternatives. |
| `X` | 2 | Verse absent from the physical codex, supplied for numbering continuity. |
| `y` | 36 | Preceding letter marked as yatir, a superfluous letter. |

The two `X` cases are Joshua 21:36–37. An edition's encoded accents, vowels and supplied records must not all be described as independently verified manuscript ink. The publisher's change documentation also describes editorially supplied vowels in Numbers 7.

## WLC 4.20 through OSHB

The pinned OSHB distribution declares the underlying WLC text public domain and licenses its lemma/morphology work under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).

Required source credit:

> Original work of the Open Scriptures Hebrew Bible available at https://github.com/openscriptures/morphhb

This package retains the pinned upstream `original/wlc_4_20_oshb/README.md` and `LICENSE.md`. The source revision is `3d15126fb1ef74867fc1434be1942e837932691f`; see the download manifest for file URLs, sizes and hashes.

Changes made for this package: structured passage records, modern annotation roles, display views without segmentation slashes, a SQLite index, source-preservation checks and bounded retrieval. Original upstream files were not edited. Credit does not imply OSHB endorsement.

OSHB/WLC note codes are edition-specific. Preserve their original attributes and note structures; use the OSHB definitions when implementing additional decoding. The UXLC table above is not a WLC decoding table.
