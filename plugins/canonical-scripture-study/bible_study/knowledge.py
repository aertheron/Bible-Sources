"""Small complete study entries and context pointers, not corpus-wide retrieval."""
from __future__ import annotations
import json
import re
from .reference import lookup_key
from .store import SourceStore, StudyError, bounded, config


class Knowledge:
    def __init__(self, store=None):
        self.store = store or SourceStore()

    def word(self, query, context_ids=None):
        if not isinstance(query, str) or not query.strip() or len(query) > 300:
            raise StudyError("word_query", "Supply a word, theme, study ID or lexical ID.")
        index = self.store.json("indexes/word-study-index.json")
        if query in index["sense_records"]:
            pointer = index["sense_records"][query]
            return bounded({"query": query, "status": "contextual_sense_record", "record": json.loads(self.store.span(pointer)), "evidence": self.store.evidence(pointer)}, 12000)
        studies = {r["id"]: r for r in index["studies"]}
        ids = []
        if query.upper() in studies:
            ids = [query.upper()]
        elif query.upper() in index["lookup_base_strong"]:
            ids = index["lookup_base_strong"][query.upper()]
        else:
            key = lookup_key(query)
            for label, values in {**index["lookup_terms"], **config("word-aliases")["aliases"]}.items():
                if lookup_key(label) == key:
                    ids.extend(values)
        ids = list(dict.fromkeys(ids))
        if len(ids) > 2:
            return {"query": query, "status": "choose_one", "candidates": [{"id": i, "title": studies[i]["title"]} for i in ids]}
        if not ids:
            return {"query": query, "status": "no_curated_entry", "entries": [], "next_entry_id": index["next_entry_id"], "guidance": "Perform a bounded source-based study; submit a reviewed addition using the collection's update process. Do not publish drafts automatically."}
        if context_ids is not None and (not isinstance(context_ids, list) or len(context_ids) > 6 or any(not isinstance(x, str) for x in context_ids)):
            raise StudyError("word_contexts", "Select up to six contextual record IDs.")
        entries = []; remaining = 6
        for ident in ids:
            row = studies[ident]
            entry = json.loads(self.store.span(row["entry_record"]))
            raw_senses = [json.loads(self.store.span(index["sense_records"][i])) for i in row["sense_ids"]]
            senses = [{k: s[k] for k in ("id", "base_strong", "label", "contextual_summary", "references") if k in s} for s in raw_senses]
            chosen = row["context_ids"] if context_ids is None else [i for i in context_ids if i in row["context_ids"]]
            contexts = []
            for cid in chosen[:remaining]:
                pointer = index["context_records"][cid]
                context = json.loads(self.store.span(pointer))
                contexts.append({k: context[k] for k in ("id", "entry_id", "reference", "source_id", "numbering", "range_all_verses_present") if k in context} | {"record_pointer": self.store.evidence(pointer)})
            remaining -= len(contexts)
            entries.append({"entry": entry, "evidence": self.store.evidence(row["entry_record"]), "review": row["review"], "contextual_senses": senses, "context_pointers": contexts, "deferred_context_ids": chosen[len(contexts):], "related_entry_ids": row["related_entry_ids"]})
        packet = {"query": query, "status": "curated_entries", "entries": entries, "coverage": "50 authored model-assisted studies; selected lexical sources, not an exhaustive concordance or independent peer review.", "sense_record_access": "Use lookup_word with an exact sense ID to retrieve its complete annotation/provenance record.", "related_entries_loaded": False}
        limit = config("method")["budgets"]["word_packet_characters"]
        if len(ids) == 1:
            item = entries[0]
            while item["context_pointers"] and len(json.dumps(packet, ensure_ascii=False, separators=(",", ":"))) > limit:
                removed = item["context_pointers"].pop()
                item["deferred_context_ids"].insert(0, removed["id"])
        try:
            return bounded(packet, limit)
        except StudyError:
            if len(ids) == 2:
                return {"query": query, "status": "choose_one", "reason": "Two complete entries exceed the normal packet budget.", "candidates": [{"id": i, "title": studies[i]["title"]} for i in ids]}
            raise

    def lexical(self, entry_id):
        if not isinstance(entry_id, str) or len(entry_id) > 100:
            raise StudyError("lexical_query", "Supply a selected lexical record ID.")
        index = self.store.json("indexes/lexical-entry-index.json")
        pointers = index.get(entry_id, index.get(entry_id.upper(), []))
        return bounded({"entry_id": entry_id, "records": [{"record": json.loads(self.store.span(p)), "evidence": self.store.evidence(p)} for p in pointers[:6]], "coverage": "606 selected STEP/OSHB supporting records. Full upstream lexicons and a corpus-wide Greek lemma layer are not imported.", "total_candidates": len(pointers)}, 12000)

    def trajectory(self, query):
        if not isinstance(query, str) or len(query) > 300:
            raise StudyError("trajectory_query", "Supply a short theme name.")
        seed = config("trajectories")
        dossiers = [d for d in seed["dossiers"] if lookup_key(query) in {lookup_key(x) for x in [d["id"], *d["aliases"]]}]
        return bounded({"query": query, "dossiers": dossiers[:1], "status": seed["status"], "anchors_loaded": False, "anchor_budget": 6, "research_leads": self.store.json("resources/research-links.json")["resources"][:2], "guidance": "Retrieve only the anchors needed to answer the question. Distinguish quotation, echo, typology and thematic development. Do not fetch every Bible book."}, 8000)
