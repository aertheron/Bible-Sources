"""Native edition readers; retrieval is not verified cross-edition collation."""
from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from .reference import References
from .store import SourceStore, StudyError, bounded


def surface_tokens(text, prefix):
    """Derived surface segments, with codepoint offsets in unchanged source text."""
    out = []; start = None
    for i, char in enumerate(text + " "):
        is_letter = char.isalpha() or unicodedata.category(char).startswith("M")
        if is_letter or (start is not None and char in "’᾽'"):
            if start is None:
                start = i
        elif start is not None:
            out.append({"id": f"{prefix}:token:{len(out) + 1}", "form": text[start:i], "start": start, "end": i, "annotation_layer": "runtime_surface_tokenization_no_lemma_or_morphology"})
            start = None
    return out


class Reader:
    def __init__(self, store=None, refs=None):
        self.store = store or SourceStore()
        self.refs = refs or References()
        self._chapters = None

    @property
    def chapters(self):
        if self._chapters is None:
            self._chapters = {(r["dataset_id"], r["book_id"], r["chapter"]): r for r in map(json.loads, self.store.read("indexes/chapter-index.jsonl").decode().splitlines())}
        return self._chapters

    def native_chapter(self, dataset, book, chapter, detail="text"):
        pointer = self.chapters.get((dataset, book, chapter))
        if not pointer:
            return {"dataset_id": dataset, "native_book": book, "chapter": chapter, "records": [], "coverage_status": "no_indexed_native_chapter", "warnings": ["Missing dataset coverage is not evidence of omission."]}
        raw = self.store.span(pointer).decode("utf-8")
        records = []
        if dataset == "TAHOT":
            fields = "locator form transliteration english_gloss disambiguated_strong morphology meaningful_variants spelling_variants simple_strong_instance alternate_strong conjoin_word expanded_strong".split()
            for line in raw.splitlines():
                cells = line.split("\t")
                m = re.match(r"[^.]+\.(\d+)\.(\d+).*?#.*?=(.*)", cells[0])
                if not m:
                    continue
                item = dict(zip(fields, cells + [""] * max(0, 12 - len(cells))))
                item.update(id="TAHOT:" + cells[0], chapter=int(m[1]), verse=int(m[2]), flags=m[3], extra_columns=cells[12:])
                records.append(item)
        elif dataset == "SBLGNT":
            for line in raw.splitlines():
                m = re.match(r"([^\t]+?) (\d+):(\d+)\t(.*)$", line)
                if not m:
                    continue
                item = {"id": f"SBLGNT:{book}:{m[2]}:{m[3]}", "chapter": int(m[2]), "verse": int(m[3]), "native_reference": f"{book} {m[2]}:{m[3]}", "text": m[4]}
                if detail == "linguistic":
                    item["tokens"] = surface_tokens(item["text"], item["id"])
                records.append(item)
        else:
            for line in raw.splitlines():
                item = json.loads(line)
                if dataset == "wlc-4.20-oshb":
                    row = {"id": item["record_id"], "chapter": item["chapter"], "verse": item["verse"], "text": item["derived_body_text"], "body_policy": item["body_policy"], "qere_readings": item["qere_readings"], "structured_notes": item["structured_notes"], "reading_status": item["reading_status"], "reference_system": item["reference_system"]}
                    if detail == "linguistic":
                        row["words"] = [{"id": w["record_id"], "source_word_id": w["source_word_id"], "form": w["display_form"], "raw_segmented_form": w["raw_segmented_form"], "role": w["reading_role"], "annotations": w["source_attributes"], "annotation_layer": w["annotation_layer"]} for w in item["source_words"]]
                elif dataset == "uxlc-2.4":
                    row = {"id": item["record_id"], "chapter": item["chapter"], "verse": item["verse"], "text": item["text_with_source_markup"], "qere_ketiv_markers": item["qere_ketiv_markers"], "transcription_note_markers": item["transcription_note_markers"], "reading_status": item["reading_status"], "reference_system": item["reference_system"]}
                else:
                    row = {"id": f"{dataset}:{book}:{item['chapter']}:{item['verse_label']}", "chapter": item["chapter"], "verse": item["verse_number"], "native_verse_label": item["verse_label"], "text": item["text"], "source_lines": item["source_lines"]}
                    if detail == "linguistic":
                        row["tokens"] = surface_tokens(row["text"], row["id"])
                records.append(row)
        return {"dataset_id": dataset, "native_book": book, "chapter": chapter, "evidence": self.store.evidence(pointer), "records": records, "coverage_status": "indexed_source_span_verified"}

    def passage(self, reference, sources=None, detail="text"):
        if detail not in {"text", "linguistic"}:
            raise StudyError("detail", "Detail must be text or linguistic.")
        portions = self.refs.portions(reference)
        p = self.refs.parse(portions[0]["reference"])
        routes = self.refs.books[p.book]["routes"]
        if sources is None:
            sources = ["WLC", "LXX"] if "WLC" in routes else ["SBLGNT"]
            sources = [s for s in sources if s in routes]
        if not isinstance(sources, list) or not 1 <= len(sources) <= 4 or any(s not in {"WLC", "UXLC", "TAHOT", "LXX", "SBLGNT"} for s in sources):
            raise StudyError("sources", "Select one to four named public editions: WLC, UXLC, TAHOT, LXX, SBLGNT.")
        packets = []
        for source in dict.fromkeys(sources):
            if source not in routes:
                packets.append({"source": source, "records": [], "coverage_status": "edition_not_available_for_this_book"})
                continue
            dataset, native_book = routes[source]
            for c in range(p.start_chapter, p.end_chapter + 1):
                packet = self.native_chapter(dataset, native_book, c, detail)
                packet["records"] = [r for r in packet["records"] if p.contains(r["chapter"], r["verse"])]
                packet["source"] = source
                packets.append(packet)
        return bounded({"requested_reference": reference, "current_portion": self.refs.label(p), "pending_references": [x["reference"] for x in portions[1:]], "boundary_status": portions[0]["boundary_status"], "source_packets": packets, "alignment_status": "native_number_candidate_retrieval_not_verified_verse_equivalence", "warnings": ["Native chapter/verse labels are preserved. Verify cross-edition numbering and literary form before collating.", "WLC and UXLC are transcriptions of the same Leningrad manuscript, not independent votes.", "TAHOT Q/R/X annotations remain explicit; restored or reconstructed text is not unqualified manuscript evidence."]})

    def apparatus(self, reference):
        portions = self.refs.portions(reference); p = self.refs.parse(portions[0]["reference"])
        if self.refs.books[p.book]["testament"] != "NT":
            return {"reference": self.refs.label(p), "entries": [], "coverage_status": "no_OT_critical_apparatus_imported"}
        path = f"sources/sblgnt/apparatus/{p.book}.txt"
        raw = self.store.read(path).decode("utf-8")
        headers = list(re.finditer(r"(?m)^[^\n\t]+? (\d+):(\d+)[ \t]*$", raw))
        entries = []
        for i, match in enumerate(headers):
            if p.contains(match[1], match[2]):
                end = headers[i + 1].start() if i + 1 < len(headers) else len(raw)
                entries.append({"native_reference": match[0].strip(), "text": raw[match.start():end].rstrip()})
        return bounded({"reference": self.refs.label(p), "pending_references": [x["reference"] for x in portions[1:]], "entries": entries, "source_file": path, "source_commit": self.store.profile["commit"], "source_sha256": self.store.profile["metadata_hashes"][path], "coverage_status": "edition_comparison_apparatus_not_full_manuscript_apparatus", "warnings": ["No listed entry does not establish that a passage has no textual variants."]})

    def _dss_index(self, category, book):
        path = f"indexes/dss/{category}/{book}.tsv"
        if path not in self.store.profile["metadata_hashes"]:
            return []
        return list(csv.DictReader(io.StringIO(self.store.read(path).decode()), delimiter="\t"))

    @staticmethod
    def _dss_pointer(row, field="file", prefix=""):
        return {"file": "sources/dss/2.0.1/enriched/" + row[field], "byte_offset": int(row[prefix + "byte_offset"]), "byte_length": int(row[prefix + "byte_length"]), "sha256": row[prefix + "sha256"]}

    def dss(self, reference, cursor=0, limit=1, include_linguistics=True):
        if type(cursor) is not int or cursor < 0 or type(limit) is not int or not 1 <= limit <= 3 or type(include_linguistics) is not bool:
            raise StudyError("dss_page", "Use a nonnegative cursor, one to three physical records, and a boolean linguistic option.")
        portions = self.refs.portions(reference); p = self.refs.parse(portions[0]["reference"])
        book = self.refs.books[p.book].get("dss_book")
        rows = [r for r in self._dss_index("records", book) if r["chapter"].isdigit() and r["verse"].isdigit() and p.contains(r["chapter"], r["verse"])] if book else []
        if cursor > len(rows):
            raise StudyError("dss_page", "Cursor exceeds available physical records.")
        selected = rows[cursor:cursor + limit]
        records = []
        for row in selected:
            pointer = self._dss_pointer(row)
            item = {"metadata": row, "evidence": self.store.evidence(pointer), "raw_reading_and_sign_annotations": self.store.span(pointer).decode("utf-8")}
            if include_linguistics:
                lp = self._dss_pointer(row, "linguistics_file", "linguistics_")
                hp = self.store.profile["dss_linguistic_headers"][lp["file"]]
                item["linguistics"] = {"columns": self.store.span(hp).decode().strip().split("\t"), "table": self.store.span(lp).decode("utf-8"), "evidence": self.store.evidence(lp), "value_encoding": "tab_delimited_JSON_cells_null_empty_and_NA_distinct", "provenance": "source.* records Abegg/TF annotations; derived_* records later analyses. Neither layer is automatically surviving ink.", "feature_guide": "sources/dss/2.0.1/enriched/feature_guide.txt"}
            records.append(item)
        physical_ids = {r["record_id"] for r in selected}
        statuses = []
        for row in self._dss_index("passage-status", book) if book else []:
            if physical_ids.intersection(re.findall(r"L\d+-R\d+", row["record_ids"])):
                pointer = self._dss_pointer(row)
                statuses.append({"metadata": row, "text": self.store.span(pointer).decode("utf-8"), "evidence": self.store.evidence(pointer)})
        following = cursor + len(selected)
        return bounded({"reference": self.refs.label(p), "pending_references": [x["reference"] for x in portions[1:]], "total_records": len(rows), "cursor": cursor, "next_cursor": following if following < len(rows) else None, "records": records, "passage_status": statuses, "status_scope": "whole_indexed_scroll_passage_for_returned_physical_records; counts_may_extend_beyond_the_current_page", "coverage_status": "indexed_physical_records" if rows else "no_indexed_DSS_record_not_evidence_of_omission", "licence": "CC BY-NC 4.0", "attribution": "Abegg, Bowley and Cook; TF conversion by Jacobs, Naaijer and Roorda; ETCBC/dss 2.0.1", "warnings": ["Reconstructed letters are editorial readings; preserve their explicit status.", "Unmarked letters have not been independently verified as secure ink.", "Sign-slot totals are not the fraction of an entire biblical verse that survives.", "Modern lexeme pointing and derived grammar are analytical annotations.", "Individual scrolls and their relationships matter; DSS is not one independent vote."]})
