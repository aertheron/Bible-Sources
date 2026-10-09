"""Command routing, reader orientation and explicit continuation state."""
from __future__ import annotations
import re
import unicodedata
from . import __version__
from .evaluation import textual_cases
from .knowledge import Knowledge
from .readers import Reader
from .reference import Passage, References
from .store import SourceStore, StudyError, bounded, config
from .workflow import DEPTH_MODES, DEPTH_OPTIONS, resolve_depth, validate_depth, workflow


FORMATS = {"plain_working", "transliteration_interlinear", "original_interlinear"}
STAGES = {
    "full_study": ["fetch_align", "collate_compare", "evaluate_select", "translate_annotate", "exegetical_synthesis", "theology_review"],
    "translation_only": ["fetch_align", "collate_compare", "evaluate_select", "translate_annotate", "theology_review"],
    "exegesis_only": ["fetch_align", "collate_compare", "evaluate_select", "exegetical_synthesis", "theology_review"],
    "context_history": ["fetch_align", "exegetical_synthesis"],
    "variant_reconciliation": ["fetch_align", "collate_compare", "evaluate_select", "theology_review"],
    "theology_check": ["fetch_align", "exegetical_synthesis", "theology_review"],
    "dss_research": ["dss_research"],
    "study_plan": ["fetch_align", "collate_compare", "evaluate_select", "translate_annotate", "exegetical_synthesis", "theology_review"],
    "word_study": ["fetch_align", "exegetical_synthesis", "theology_review"],
    "theme_study": ["fetch_align", "exegetical_synthesis", "theology_review"],
}
STAGES["standard_study"] = list(STAGES["study_plan"])
STAGES["detailed_study"] = list(STAGES["study_plan"])
ALIASES = {
    "standard_study": ["standard study", "standard", "standaardstudie", "standaard studie", "standaard"],
    "detailed_study": ["detailed study", "detailed", "uitgebreide studie", "uitgebreid"],
    "full_study": ["full study", "volledige studie"],
    "translation_only": ["translation only", "translate", "vertaling alleen", "vertaal"],
    "exegesis_only": ["exegesis only", "exegese alleen"],
    "context_history": ["context and history opening", "context and history", "context history", "context en geschiedenis"],
    "variant_reconciliation": ["translation variance reconciliation", "variant reconciliation", "tekstvarianten"],
    "theology_check": ["theology check", "theologiecontrole"],
    "dss_research": ["dss research", "dead sea scrolls", "dss studie"],
    "word_study": ["word study", "woordstudie"],
    "theme_study": ["theme study", "themastudie"],
    "study_plan": ["study plan", "studieplan"],
}


def validate_preferences(language, translation_format):
    if not isinstance(language, str) or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z]{2,8})?", language):
        raise StudyError("language", "Use a language code such as en, nl or es.")
    if not isinstance(translation_format, str) or translation_format not in FORMATS:
        raise StudyError("translation_format", "Use plain_working, transliteration_interlinear or original_interlinear.")


class Engine:
    def __init__(self, store=None):
        self.store = store or SourceStore()
        self.refs = References(); self.reader = Reader(self.store, self.refs); self.knowledge = Knowledge(self.store)

    def health(self):
        return {"plugin_version": __version__, "source_profile": self.store.profile["profile"], "source_commit": self.store.profile["commit"], "source_access": "local_verified_spans" if self.store.root else "pinned_remote_cache", "base_books": len(self.refs.books), "indexed_chapters": len(self.reader.chapters), "curated_word_studies": 50, "default_study_depth": "standard", "study_depths": list(config("method")["study_depths"]), "canonical_seed_dossiers": len(config("trajectories")["dossiers"]), "translation_and_interpretation": "performed_by_the_host_model_using_skills_not_by_a_dictionary_replacement_algorithm", "limitations": ["Cross-edition verse maps are not verified.", "No full manuscript apparatus, full Greek concordance, exhaustive canonical database or complete imported website claim profile.", "The Python adapter uses stdio; hosted HTTP is provided by the Worker."]}

    def _options(self, query, language, translation_format, study_depth):
        parts = re.split(r",\s*", query)
        retained = []
        for part in parts:
            lower = part.lower().strip()
            if lower in DEPTH_OPTIONS:
                study_depth = DEPTH_OPTIONS[lower]
            elif lower in {"in dutch", "in nederlands", "dutch", "nederlands"}:
                language = "nl"
            elif lower in {"in english", "in engels", "english", "engels"}:
                language = "en"
            elif "interlinear" in lower:
                translation_format = "original_interlinear" if any(x in lower for x in ["original", "origineel", "grondtekst"]) else "transliteration_interlinear"
            elif lower in {"plain translation", "plain working translation", "gewone vertaling"}:
                translation_format = "plain_working"
            else:
                retained.append(part)
        return ", ".join(retained).strip(), language, translation_format, study_depth

    def _state(self, state):
        fields = {"request_mode", "language", "translation_format", "original_reference", "current_reference", "pending_references"}
        if not isinstance(state, dict) or set(state) not in (fields, fields | {"study_depth"}) or not isinstance(state["request_mode"], str) or state["request_mode"] not in STAGES or state["request_mode"] in {"word_study", "theme_study"}:
            raise StudyError("continuation_state", "Supply the exact continuation_state returned by the previous passage plan.")
        validate_preferences(state["language"], state["translation_format"])
        for key in ("original_reference", "current_reference"):
            self.refs.parse(state[key], allow_book=key == "original_reference")
        pending = state["pending_references"]
        if not isinstance(pending, list) or len(pending) > 400:
            raise StudyError("continuation_state", "Invalid pending reference list.")
        for ref in pending:
            self.refs.scope(self.refs.parse(ref))
        depth = state.get("study_depth", resolve_depth(state["request_mode"]))
        validate_depth(depth)
        if depth is None or (state["request_mode"] in DEPTH_MODES and depth != DEPTH_MODES[state["request_mode"]]):
            raise StudyError("continuation_state", "Invalid study depth in continuation state.")
        return {**state, "study_depth": depth}

    def plan(self, query, active_reference=None, language="en", translation_format="plain_working", study_state=None, study_depth=None):
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise StudyError("query", "Supply a study command or Bible reference under 2,000 characters.")
        validate_depth(study_depth)
        text, language, translation_format, study_depth = self._options(query.strip(), language, translation_format, study_depth)
        validate_preferences(language, translation_format)
        if text.lower() in {"help", "commands", "commando's", "hulp"}:
            return {"mode": "help", "commands": {k: v for k, v in ALIASES.items()}, "continuation_commands": ["Next", "Next chapter 2", "Next: Genesis 2", "Volgende"], "translation_formats": sorted(FORMATS), "study_depths": config("method")["study_depths"], "default_study_depth": "standard"}
        nxt = re.fullmatch(r"(?:next|volgende)(?:\s*(?::\s*|\s+)(.*))?", text, re.I)
        if nxt:
            if study_state is None and active_reference is None:
                return {"status": "needs_input", "message": "Continue from a previous passage plan by supplying its continuation_state or active_reference."}
            state = self._state(study_state) if study_state is not None else {"request_mode": "study_plan", "language": language, "translation_format": translation_format, "original_reference": active_reference, "current_reference": active_reference, "pending_references": [], "study_depth": study_depth or "standard"}
            if study_depth is not None:
                state = {**state, "study_depth": study_depth}
                if state["request_mode"] in {"study_plan", *DEPTH_MODES}:
                    state["request_mode"] = next(mode for mode, depth in DEPTH_MODES.items() if depth == study_depth)
            current = self.refs.parse(state["current_reference"])
            pending = list(state["pending_references"])
            target = nxt[1]
            if target:
                chapter = re.fullmatch(r"(?:chapter|hoofdstuk)\s+(\d+)", target, re.I)
                target = f"{self.refs.books[current.book]['name']} {chapter[1]}" if chapter else target
                chosen = self.refs.portions(target)
                target = chosen[0]["reference"]
                if target in pending:
                    pending = pending[pending.index(target) + 1:]
                else:
                    pending = [p["reference"] for p in chosen[1:]]
            elif pending:
                target = pending.pop(0)
            else:
                following = self.refs.next(state["current_reference"])
                if following is None:
                    return {"status": "book_complete", "reference": state["current_reference"]}
                target = following["reference"]
            return self._passage_plan(state["request_mode"], target, state["language"], state["translation_format"], state["original_reference"], pending, study_depth=state["study_depth"])
        mode = "study_plan"
        for alias, candidate in sorted([(a, k) for k, values in ALIASES.items() for a in values], key=lambda pair: len(pair[0]), reverse=True):
            m = re.match(re.escape(alias) + r"(?:\s*:\s*|\s+|$)", text, re.I)
            if m:
                mode = candidate; text = text[m.end():].strip(); break
        if not text:
            text = active_reference or ""
        if not text:
            return {"status": "needs_input", "mode": mode, "message": "Supply the passage, word or theme for this command."}
        if mode in {"word_study", "theme_study"}:
            term, sep, remainder = text.partition(". ")
            return bounded({"mode": mode, "topic": term.rstrip("."), "follow_up_requested": remainder if sep else None, "language": language, "translation_format": translation_format, "stages": STAGES[mode], "retrieval": "lookup_word" if mode == "word_study" else "lookup_trajectory", **workflow(mode, resolve_depth(mode, study_depth)), "method": config("method")["sequence"]}, 16000)
        text = re.sub(r"\.\s*include the linguistic information\.?$", "", text, flags=re.I)
        portions = self.refs.portions(text)
        return self._passage_plan(mode, portions[0]["reference"], language, translation_format, text, [p["reference"] for p in portions[1:]], portions[0]["boundary_status"], resolve_depth(mode, study_depth))

    def _passage_plan(self, mode, current, language, translation_format, original, pending, boundary=None, study_depth=None):
        study_depth = resolve_depth(mode, study_depth)
        p = self.refs.parse(current)
        unit_suggestions = []
        for row in config("literary-units")["units"]:
            q = self.refs.parse(row["reference"])
            if q.book == p.book and (q.start_chapter, q.start_verse) <= (p.end_chapter, p.end_verse) and (p.start_chapter, p.start_verse) <= (q.end_chapter, q.end_verse):
                unit_suggestions.append(row)
        opening = self.reader.passage(self.refs.label(Passage(p.book, p.start_chapter, p.start_verse, p.start_chapter, p.start_verse)), sources=["WLC"] if self.refs.books[p.book]["testament"] == "OT" else ["SBLGNT"])
        records = opening["source_packets"][0]["records"]
        words = records[0].get("text", "") if records else ""
        stripped = "".join(c for c in unicodedata.normalize("NFD", words.lower()) if not unicodedata.combining(c))
        first = " ".join(stripped.split()[:8])
        dependent = bool(re.search(r"\b(?:ουν|αρα|διο|τοιγαρουν)\b|δια τουτο", first) or first.startswith(("לכן", "ועתה")))
        previous = None
        if p.start_verse > 1:
            previous = self.refs.label(Passage(p.book, p.start_chapter, max(1, p.start_verse - 5), p.start_chapter, p.start_verse - 1))
        elif p.start_chapter > 1:
            c = p.start_chapter - 1; last = self.refs.last(p.book, c)
            previous = self.refs.label(Passage(p.book, c, max(1, last - 4), c, last))
        logical_next = pending[0] if pending else (self.refs.next(current) or {}).get("reference")
        state = {"request_mode": mode, "language": language, "translation_format": translation_format, "original_reference": original, "current_reference": current, "pending_references": pending, "study_depth": study_depth}
        return bounded({"mode": mode, "reference": current, "requested_reference": original, "language": language, "translation_format": translation_format, "stages": STAGES[mode], "reader_action": "Complete this bounded passage at the selected depth (Standard by default), showing verified results as early as the host allows; a short plan alone is not completion" if mode == "study_plan" else "Complete this portion in the requested mode and deliver verified milestones early when supported", "study_plan": ["Locate the literary unit and explain necessary preceding context.", "Read our Hebrew/Greek evidence and review consequential variants independently.", "Present a contextual translation with relevant footnotes and a compact term key when the command calls for translation.", "Explain the local argument and bounded canonical connections at the selected depth; use external research only afterwards when warranted.", "Review claims and alternatives, then suggest the logical Next portion."], "literary_unit_suggestions": unit_suggestions, "boundary_status": boundary or "continued_bounded_portion", "context_preface": {"required": dependent, "opening_source_text": words, "preceding_context_reference": previous, "instruction": "Before translation, explain what the dependent opening follows from; retrieve enough discourse to support the summary. This nearby window is a starting point, not the entire argument." if dependent else "Review continuing discourse and scene; add a short context preface if needed."}, "textual_review_flags": textual_cases(current, self.refs), "continuation_state": state, "next": {"command": "Next", "reference": logical_next, "instruction": "Present the current portion only; continue when the user asks Next, preserving mode, depth, language and format."} if logical_next else None, "method": config("method")["sequence"], **workflow(mode, study_depth)}, 16000)
