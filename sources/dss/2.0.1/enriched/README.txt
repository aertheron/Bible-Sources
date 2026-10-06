DSS ENRICHED SOURCE PACKAGE — 2.0.1

This package uses the supplied TF source files and the verified transcription
export. It preserves the existing record IDs and text while adding explicit
critical status and the populated word-level linguistic annotations.

BOOK AND PASSAGE FILES
books/ and other_material/ are marked reading TXT files. Each record now has
critical counts and a word-by-word critical table. Each sign run identifies its
slot IDs, sign type, Unicode glyphs, and raw critical flags. The word-level
transcriptions and lexemes retain all three available encodings in linguistics/.
These are self-contained even when the opening bracket occurred earlier.
The Unicode and Source transcription lines are unchanged from the base export.
Standalone signs remain physically located without invented verse mappings.

passage_status/ has one summary per available biblical verse per TF scroll node,
combining its physical records and half-verses. passage_status_index.tsv supports
exact lookup. Summaries describe available data; they do not imply whole-verse
survival, completeness, manuscript dating, or independent witness counts.
record_status.jsonl.gz contains a summary for all 66,557 physical/reference
records, including non-biblical and unmapped material.

LINGUISTIC FILES
linguistics/ has TXT tables corresponding to every reading file. There are
65 populated raw word features, including original
morphological tags, converted morphology, lexeme forms/encodings, original
transcriptions, BHSA additions, morpheme parsing, correction notes, and errors.
Every 500,995 word node occurs once. The word table also links to source
lexeme nodes and available phrase/clause groups. These groups have limited
coverage and must not be treated as a complete syntactic analysis.
Node IDs are internal identifiers in this TF release, not Strong's numbers.
The source lang feature marks only non-Hebrew: a=Aramaic, g=Greek. An absent
source.lang uses the source's Hebrew default; the raw null is retained.

Each table's COLUMNS line defines the ordered fields. Table cells are independent
JSON values separated by literal tabs. Decode each cell with json.loads after
splitting a row on tabs. null is an absent feature, an empty string is a present
empty value, and "NA" or "unknown" remains a literal source value. These cases
are deliberately preserved. The exact lookup script prints the column schema
alongside retrieved linguistic records; semantic retrieval also needs the schema.

feature_catalog.json retains all original TF metadata lines and provenance
groups; feature_guide.txt explains each field from the source's own metadata.
The ten node features with no word values are not empty repeated columns;
their metadata remains in the catalogue, and sign-critical flags are in the
critical runs. other_linguistic_nodes.jsonl.gz preserves available features,
memberships, and sign slots for lexeme, clause, and phrase nodes.

PROVENANCE GROUPS
source.*: Abegg source plus TF transcription/lexeme conversion and morphology
decomposed from the source tags. The e suffix in fulle, glyphe, lexe, and glexe
means ETCBC transliteration of the source, not a new linguistic opinion.
derived_model.*: BHSA/model additions identified by their feature metadata.
derived_parsing.*: the added parsing pipeline whose metadata declares automatic
generation and correction by Thijs Amersfoort. The header describes the pipeline;
it does not establish that every individual token was manually checked.
derived_bhsa.*: other BHSA additions whose headers do not specify that method.
g_cons is a derived parsing feature despite having no _etcbc suffix.
No source tag is replaced with a derived tag. Disagreements and missing values
remain visible. Different tag vocabularies need interpretation before comparison.

CRITICAL STATUS DEFINITIONS
ALL_LETTER_SLOTS_RECONSTRUCTED: every represented letter slot has rec=1.
PARTLY_RECONSTRUCTED: some represented letter slots have rec=1.
NO_LETTER_RECONSTRUCTION_MARKED: no represented letter slot has rec=1.
NO_LETTER_SLOTS: the word/record contains no classified letter slots.
These labels do not certify ink, correctness, or the absence of missing text.
A letter slot is type cons/vwl, or type foreign containing a Unicode letter.
Counts are source sign units, not Unicode code points or estimated gap lengths.
Missing and uncertainty symbols are counted separately. Flag counts may overlap.
unc=1..4 records source uncertainty levels; type=unc also signals an uncertain
symbol even without a level flag. cor=1 is modern correction, 2 ancient, 3 ancient
supralinear. rem=1 is modern removal, 2 ancient. alt=1 is an alternative; vac=1
marks vacant space. rec=1 is modern editorial reconstruction.
An omitted run flag means the TF feature is absent, not guaranteed certainty.
Lexeme vowels are analytical pointing; they are not supplied manuscript vowels.

LOOKUP AND RECREATION
  python tools/lookup_enriched_dss.py . Genesis 1 28 --scroll 4Q483 --linguistics
  python tools/lookup_enriched_dss.py . Isaiah 53 11 --linguistics
  python tools/lookup_enriched_dss.py . --record L1575897-R002 --linguistics
The script verifies checksums and returns the verse summary, reading status,
letter details, and optional full linguistic rows without loading TF.
Keep indexed files unchanged; edits/newline conversion require index regeneration.
To regenerate, install tools/requirements.txt, recreate the base with export_dss.py,
then run enrich_dss.py TF_FOLDER --base BASE_EXPORT --output NEW_ENRICHED_FOLDER.
The TF source hashes must match the base export; no online source is substituted.
To recheck the saved package against both sources:
  python tools/validate_enriched_dss.py . --base BASE_EXPORT --tf TF_FOLDER

CHECKS AND LIMITS
All 500,995 words and 1,430,241 sign slots are accounted for,
including 20,261 standalone signs. Critical glyphs and flags
were verified for every word sign; persisted record counts were checked against
TF. All populated word-feature streams were verified by checksums, with
5,016 rows also decoded
cell by cell against TF. A specific regression check verifies reconstructed
letters retrieved without their earlier opening bracket.
This preserves TF readings and analyses, without independently examining scroll
images or adjudicating editorial reconstructions. Keep the original TF archive
for the complete graph, other node features, and line-similarity relations.

SOURCE AND TERMS
Repository: https://github.com/ETCBC/dss
Feature documentation: https://github.com/ETCBC/dss/blob/master/docs/feature_documentation.md
Provenance documentation: https://github.com/ETCBC/dss/blob/master/docs/about.md
Added analysis project: https://github.com/ETCBC/DSS2ETCBC
Original attribution: Martin G. Abegg, Jr., James E. Bowley, and Edward M. Cook
Original conversion: Jarod Jacobs, Martijn Naaijer and Dirk Roorda
Source licence: Creative Commons Attribution-NonCommercial 4.0 International License
Licence URL: http://creativecommons.org/licenses/by-nc/4.0/
The export adds packaging, indexes, status summaries and joins; original values
are retained. Preserve source attribution and terms with the corpus.

COMPACT PACKAGING
Machine-readable record, auxiliary-node, and standalone-sign inventories use
lossless gzip compression. Decompress with Python gzip.open(..., 'rt', encoding='utf-8').
The reading TXT files retain Unicode glyphs and all critical flags for each sign.
Repeated sign-level transliterations are omitted from that reading view; all
65 populated word features, including full/glyph/lexeme encodings, remain intact.
The original TF archive retains every sign encoding and the complete graph.
