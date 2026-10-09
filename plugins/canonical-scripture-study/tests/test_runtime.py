"""Behavioral checks against the pinned public source snapshot."""
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bible_study.engine import Engine
from bible_study.evaluation import evaluate_variant
from bible_study.handoff import validate_handoff
from bible_study.reference import Passage
from bible_study.store import StudyError, bounded, config


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = Engine()

    def test_creation_unit_is_kept(self):
        p = self.engine.plan("Translate Genesis 1:1-2:3")
        self.assertEqual(p["reference"], "Genesis 1:1-2:3")
        self.assertEqual(p["continuation_state"]["pending_references"], [])
        self.assertEqual(p["next"]["reference"], "Genesis 2:4-25")
        data = self.engine.reader.passage(p["reference"], ["WLC"])
        self.assertEqual(sum(len(c["records"]) for c in data["source_packets"]), 34)

    def test_next_follows_curated_literary_unit_without_expanding_current_scope(self):
        standard = self.engine.plan("Genesis 1:1-3")
        self.assertEqual(standard["reference"], "Genesis 1:1-3")
        self.assertEqual(standard["next"]["reference"], "Genesis 1:4-2:3")
        self.assertEqual(standard["next"]["literary_unit_reference"], "Genesis 1:1-2:3")
        self.assertEqual(standard["next"]["boundary_basis"], "curated_literary_continuation")
        after = self.engine.plan("Next", study_state=standard["continuation_state"])
        self.assertEqual(after["reference"], "Genesis 1:4-2:3")
        source = self.engine.reader.passage(after["reference"], ["WLC"])
        self.assertEqual(sum(len(packet["records"]) for packet in source["source_packets"]), 31)
        self.assertEqual(after["study_depth"], "standard")
        self.assertEqual(after["next"]["reference"], "Genesis 2:4-25")

        whole_chapter = self.engine.plan("Genesis 1")
        self.assertEqual(whole_chapter["next"]["reference"], "Genesis 2:1-3")
        self.assertEqual(self.engine.plan("Next chapter 2", study_state=standard["continuation_state"])["reference"], "Genesis 2")
        explicitly_scoped = self.engine.plan("Full study Genesis 1:1-2:3")
        self.assertEqual(explicitly_scoped["reference"], "Genesis 1:1-2:3")
        self.assertEqual(explicitly_scoped["next"]["reference"], "Genesis 2:4-25")
        # Fallback to existing size-safe, curated chunks where no parent unit is indexed.
        self.assertEqual(self.engine.refs.next("Luke 1:1-25")["reference"], "Luke 1:26-56")
        self.assertEqual(self.engine.refs.next("Psalms 119:1-8")["reference"], "Psalms 119:9-16")

    def test_two_chapters_continue_in_same_mode(self):
        p = self.engine.plan("Translate Genesis 1-2, in Dutch, with original language interlinear")
        self.assertEqual(p["reference"], "Genesis 1")
        for command in ("Next", "Next chapter 2", "Next: Genesis 2", "Volgende hoofdstuk 2"):
            n = self.engine.plan(command, study_state=p["continuation_state"])
            self.assertEqual((n["reference"], n["mode"], n["language"], n["translation_format"]), ("Genesis 2", "translation_only", "nl", "original_interlinear"))
            self.assertEqual(n["next"]["reference"], "Genesis 3")

    def test_large_source_request_returns_first_portion(self):
        p = self.engine.reader.passage("Genesis 1-2", ["WLC"])
        self.assertEqual(p["current_portion"], "Genesis 1")
        self.assertEqual(p["pending_references"], ["Genesis 2"])
        self.assertEqual(len(p["source_packets"][0]["records"]), 31)

    def test_whole_book_is_a_sequence(self):
        p = self.engine.plan("Translate the whole of Isaiah")
        self.assertEqual(p["reference"], "Isaiah 1")
        self.assertEqual(len(p["continuation_state"]["pending_references"]), 65)
        self.assertEqual(p["next"]["reference"], "Isaiah 2")

    def test_long_chapter_literary_portions(self):
        p = self.engine.refs.portions("Psalm 119")
        self.assertEqual(len(p), 22)
        self.assertEqual(p[0]["reference"], "Psalms 119:1-8")
        self.assertEqual(p[-1]["reference"], "Psalms 119:169-176")
        self.assertEqual([x["reference"] for x in self.engine.refs.portions("Luke 1")], ["Luke 1:1-25", "Luke 1:26-56", "Luke 1:57-80"])

    def test_curated_boundaries_cover_without_overlap(self):
        for key, units in config("chunking")["chapter_units"].items():
            book, chapter = key.split(":"); chapter = int(chapter)
            got = [v for a, b in units for v in range(a, b + 1)]
            self.assertEqual(got, list(range(1, self.engine.refs.last(book, chapter) + 1)), key)
            self.assertTrue(all(b - a + 1 <= 45 for a, b in units))

    def test_invalid_references_are_not_rewritten(self):
        for ref in ("Genesis 0", "Genesis 1:99", "Isaiah 67", "Genesis 5-3", "Unknown 1"):
            with self.subTest(ref=ref), self.assertRaises(StudyError):
                self.engine.plan("Translate " + ref)

    def test_continuation_requires_valid_state(self):
        self.assertEqual(self.engine.plan("Next")["status"], "needs_input")
        with self.assertRaises(StudyError): self.engine.plan("Next", study_state={"request_mode": "word_study"})

    def test_dutch_alias_and_dependent_opening(self):
        p = self.engine.plan("Full study Romeinen 12:1-2, in Nederlands, with original interlinear")
        self.assertEqual(p["language"], "nl")
        self.assertTrue(p["context_preface"]["required"])
        self.assertEqual(p["context_preface"]["preceding_context_reference"], "Romans 11:32-36")
        self.assertEqual(self.engine.refs.parse("Matteüs 6:13").book, "Matt")

    def test_bare_reference_is_a_plan(self):
        self.assertEqual(self.engine.plan("Romans 12:1-2")["mode"], "study_plan")
        p = self.engine.plan("Exegesis only Romans 12:1-2")
        self.assertNotIn("translate_annotate", p["stages"])

    def test_depth_profiles_and_source_order(self):
        for query, depth, anchors in [("Genesis 1:1", "standard", 2), ("Standard study Genesis 1:1", "standard", 2), ("Detailed study Genesis 1:1", "detailed", 4), ("Full study Genesis 1:1", "full", 6), ("Uitgebreide studie Genesis 1:1", "detailed", 4)]:
            with self.subTest(query=query):
                p = self.engine.plan(query)
                self.assertEqual(p["study_depth"], depth)
                self.assertEqual(p["budgets"]["canonical_anchors"], anchors)
                self.assertEqual(p["source_policy"]["order"][0], "primary_source_text_and_local_context")
                self.assertTrue(p["source_policy"]["independent_analysis_first"])
                self.assertFalse(p["delivery"]["background_jobs"])
                self.assertEqual(p["source_policy"]["external_research_default"], "selective_after_independent_analysis" if depth == "full" else "off")
        self.assertEqual(self.engine.plan("Genesis 1", study_depth="detailed")["study_depth"], "detailed")
        self.assertEqual(self.engine.plan("Translate Genesis 1, full")["study_depth"], "full")
        self.assertEqual(self.engine.plan("help")["default_study_depth"], "standard")

    def test_word_study_standard_full_and_citation_contracts(self):
        basic = self.engine.plan("Woordstudie ruach", language="nl")
        self.assertEqual(basic["mode"], "word_study")
        self.assertEqual(basic["topic"], "ruach")
        self.assertEqual(basic["study_depth"], "standard")
        self.assertEqual(basic["word_study_policy"]["selected_depth"], "standard")
        self.assertEqual(basic["word_study_policy"]["target_diagnostic_occurrences"], 3)
        self.assertIn("key_occurrences", basic["response_sections"])
        self.assertNotIn("theological_synthesis_and_limits", basic["response_sections"])
        self.assertEqual(basic["budgets"]["secondary_sources"], 0)
        self.assertIn("BDB", basic["word_study_policy"]["citation_policy"]["lexical"])

        for cmd in ("Full word study ruach", "Volledige woordstudie ruach", "Word study ruach, full", "Woordstudie ruach, volledig"):
            with self.subTest(command=cmd):
                full = self.engine.plan(cmd, language="nl")
                self.assertEqual(full["mode"], "word_study")
                self.assertEqual(full["topic"], "ruach")
                self.assertEqual(full["study_depth"], "full")
                self.assertEqual(full["word_study_policy"]["target_diagnostic_occurrences"], 6)
                self.assertIn("theological_interpretation_and_limits", full["response_sections"])
                self.assertIn("sense_inventory_and_lexical_boundaries", full["response_sections"])
                self.assertIn("contextual_senses_by_occurrence_and_participants", full["response_sections"])
                self.assertIn("related_terms_and_concepts_with_distinctions", full["response_sections"])
                self.assertIn("semantic_method", full["word_study_policy"])
                self.assertIn("homographs", full["word_study_policy"]["semantic_method"]["sense_inventory"])
                self.assertIn("grammatical subject", full["word_study_policy"]["semantic_method"]["participants_and_relations"])
                self.assertIn("theological synthesis", full["word_study_policy"]["semantic_method"]["theological_interpretation"])
                self.assertIn("not an upper bound", full["word_study_policy"]["semantic_method"]["coverage_rule"])
                self.assertNotIn("semantic_method", basic["word_study_policy"])
                self.assertEqual(full["budgets"]["secondary_sources"], 2)
                self.assertTrue(full["word_study_policy"]["citation_policy"]["source_classification"])

        for cmd in ("Standard word study ruach", "Standaard woordstudie ruach", "Word study ruach, standard"):
            with self.subTest(command=cmd):
                self.assertEqual(self.engine.plan(cmd)["study_depth"], "standard")

        self.assertEqual(self.engine.plan("Word study ruach", study_depth="full")["study_depth"], "full")
        full = self.engine.plan("Full word study ruach")
        self.assertEqual(full["delivery"]["milestones"][1]["id"], "evidence_ready")
        self.assertFalse(full["delivery"]["background_jobs"])
        self.assertEqual(self.engine.plan("Full study Genesis 1:1-3")["mode"], "full_study")

    def test_depth_continuation_and_legacy_state(self):
        p = self.engine.plan("Detailed study Genesis 1-2, in Dutch, with original language interlinear")
        saved = copy.deepcopy(p["continuation_state"])
        n = self.engine.plan("Next", study_state=saved)
        self.assertEqual((n["reference"], n["study_depth"], n["language"], n["translation_format"]), ("Genesis 2", "detailed", "nl", "original_interlinear"))
        self.assertEqual(saved, p["continuation_state"])
        changed = self.engine.plan("Next, full", study_state=saved)
        self.assertEqual((changed["mode"], changed["study_depth"]), ("full_study", "full"))
        old = self.engine.plan("Full study Genesis 1-2")["continuation_state"]
        old.pop("study_depth")
        self.assertEqual(self.engine.plan("Next", study_state=old)["study_depth"], "full")
        old["request_mode"] = "study_plan"
        self.assertEqual(self.engine.plan("Next", study_state=old)["study_depth"], "standard")
        for bad in ("unknown", [], None):
            with self.subTest(bad=bad), self.assertRaises(StudyError):
                self.engine.plan("Next", study_state={**old, "study_depth": bad})
        with self.assertRaises(StudyError):
            self.engine.plan("Next", study_state={**old, "extra": True})
        with self.assertRaises(StudyError):
            self.engine.plan("Next", study_state={**saved, "study_depth": "standard"})
        for bad in ("unknown", [], "__proto__"):
            with self.subTest(bad=bad), self.assertRaises(StudyError):
                self.engine.plan("Genesis 1", study_depth=bad)

    def test_focused_depth_does_not_force_passage_translation(self):
        p = self.engine.plan("Word study testing. Compare Matthew 6:13 and James 1:13., full")
        self.assertEqual(p["mode"], "word_study")
        self.assertEqual(p["study_depth"], "full")
        self.assertIn("Compare", p["follow_up_requested"])
        self.assertNotIn("translation_notes", p["response_sections"])
        e = self.engine.plan("Exegesis only Romans 12:1-2, detailed")
        self.assertNotIn("translate_annotate", e["stages"])
        self.assertTrue(e["context_preface"]["required"])
        self.assertEqual(e["context_preface"]["preceding_context_reference"], "Romans 11:32-36")
        translation = self.engine.plan("Translate Genesis 1:1, full")
        self.assertEqual(translation["response_sections"], ["orientation", "translation_notes"])

    def test_source_editions_have_native_status(self):
        p = self.engine.reader.passage("Genesis 1:1", ["WLC", "UXLC", "TAHOT", "LXX"], "linguistic")
        self.assertEqual(len(p["source_packets"]), 4)
        self.assertIn("not_verified", p["alignment_status"])
        w = p["source_packets"][0]["records"][0]
        self.assertTrue(w["words"][0]["id"].startswith("wlc-4.20-oshb:"))
        self.assertIn("qere_readings", w)
        t = p["source_packets"][2]["records"][0]
        self.assertTrue(all(k in t for k in "locator form transliteration english_gloss disambiguated_strong morphology meaningful_variants spelling_variants simple_strong_instance alternate_strong conjoin_word expanded_strong".split()))

    def test_tahot_reconstruction_is_visible(self):
        p = self.engine.reader.passage("Genesis 4:8", ["TAHOT"])
        self.assertTrue(any("X" in r["flags"] for r in p["source_packets"][0]["records"]))

    def test_greek_tokens_preserve_forms_offsets(self):
        rows = self.engine.reader.passage("Romans 12:1-2", ["SBLGNT"], "linguistic")["source_packets"][0]["records"]
        ids = []
        for row in rows:
            for token in row["tokens"]:
                self.assertEqual(token["form"], row["text"][token["start"]:token["end"]])
                self.assertNotIn("morphology", token)
                ids.append(token["id"])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreater(len(ids), 20)

    def test_private_rahlfs_is_not_a_source(self):
        with self.assertRaises(StudyError): self.engine.reader.passage("Genesis 1:1", ["RAHLFS"])

    def test_apparatus_parses_numbered_book_names(self):
        self.assertTrue(self.engine.reader.apparatus("1 Corinthians 1")["entries"])
        self.assertTrue(self.engine.reader.apparatus("Matthew 6:13")["entries"])

    def test_absent_base_verse_is_not_filled(self):
        data = self.engine.reader.passage("Acts 8:37", ["SBLGNT"])
        self.assertEqual(data["source_packets"][0]["records"], [])
        self.assertTrue(self.engine.plan("Translate Acts 8:37")["textual_review_flags"])

    def test_dss_reconstruction_and_linguistic_provenance(self):
        data = self.engine.reader.dss("Genesis 1:27")
        self.assertEqual(data["total_records"], 7)
        first = data["records"][0]
        self.assertEqual(first["metadata"]["letter_reconstruction"], "ALL_LETTER_SLOTS_RECONSTRUCTED")
        self.assertEqual(first["metadata"]["scroll"], "4Q483")
        self.assertTrue(any(c.startswith("derived_") for c in first["linguistics"]["columns"]))
        self.assertTrue(any(c.startswith("source.") for c in first["linguistics"]["columns"]))
        self.assertTrue(data["passage_status"])
        self.assertEqual(data["licence"], "CC BY-NC 4.0")

    def test_dss_paging_keeps_all_physical_ids(self):
        cursor = 0; ids = []
        while cursor is not None:
            packet = self.engine.reader.dss("Genesis 1:27", cursor=cursor)
            ids.extend(r["metadata"]["record_id"] for r in packet["records"])
            cursor = packet["next_cursor"]
        self.assertEqual(len(ids), 7)
        self.assertEqual(len(set(ids)), 7)

    def test_missing_dss_is_not_omission(self):
        p = self.engine.reader.dss("Esther 1:1")
        self.assertEqual(p["total_records"], 0)
        self.assertIn("not_evidence_of_omission", p["coverage_status"])

    def test_all_fifty_entries_are_complete_and_bounded(self):
        for n in range(1, 51):
            with self.subTest(entry=n):
                packet = self.engine.knowledge.word(f"WT{n:03}")
                self.assertEqual(packet["status"], "curated_entries")
                self.assertTrue(packet["entries"][0]["entry"]["core_study"])
                self.assertLessEqual(len(packet["entries"][0]["context_pointers"]), 6)
                bounded(packet, 12000)
                self.assertFalse(packet["related_entries_loaded"])

    def test_word_query_testing_and_followup(self):
        p = self.engine.plan("Word study testing. Compare Matthew 6:13 and James 1:13.")
        self.assertIn("Compare", p["follow_up_requested"])
        data = self.engine.knowledge.word(p["topic"])
        self.assertEqual(data["entries"][0]["entry"]["id"], "WT008")
        self.assertNotIn("verses", data["entries"][0]["context_pointers"][0])

    def test_trajectory_pointers_do_not_fetch_canon(self):
        for row in config("trajectories")["dossiers"]:
            result = self.engine.knowledge.trajectory(row["id"])
            self.assertFalse(result["anchors_loaded"])
            self.assertLessEqual(len(result["dossiers"][0]["anchors"]), 6)
            for anchor in row["anchors"]: self.engine.refs.parse(anchor["reference"])
        self.assertEqual(self.engine.knowledge.trajectory("testing")["dossiers"][0]["word_study"], "WT008")

    def test_lexical_coverage_is_selected(self):
        index = self.engine.store.json("indexes/lexical-entry-index.json")
        result = self.engine.knowledge.lexical(next(iter(index)))
        self.assertTrue(result["records"])
        self.assertIn("selected", result["coverage"])

    def test_rich_study_defers_only_context_pointers(self):
        packet = self.engine.knowledge.word("WT050")
        item = packet["entries"][0]
        index = self.engine.store.json("indexes/word-study-index.json")
        row = next(r for r in index["studies"] if r["id"] == "WT050")
        self.assertEqual(item["entry"], json.loads(self.engine.store.span(row["entry_record"])))
        self.assertEqual([p["id"] for p in item["context_pointers"]] + item["deferred_context_ids"], row["context_ids"])
        sense = self.engine.knowledge.word(item["contextual_senses"][0]["id"])
        self.assertEqual(sense["status"], "contextual_sense_record")
        self.assertIn("lexical_record_ids", sense["record"])

    def test_malformed_structures_produce_domain_errors(self):
        for field, value in [("significance", []), ("base_reading_id", []), ("requested_inclusion_id", [])]:
            packet = self.variant(); packet[field] = value
            with self.assertRaises(StudyError): evaluate_variant(packet)
        state = self.engine.plan("Translate Genesis 1-2")["continuation_state"]
        state["request_mode"] = []
        with self.assertRaises(StudyError): self.engine.plan("Next", study_state=state)
        with self.assertRaises(StudyError): self.engine.plan("Genesis 1", translation_format=[])

    @staticmethod
    def variant():
        return {"reference": "Matthew 6:13", "base_reading_id": "base", "significance": "semantic", "readings": [{"id": "base", "text": "identified base wording", "source_ids": ["edition-base"], "evidence": [{"locator": "identified source"}], "status": "attested", "independence_group": "base-tradition"}, {"id": "short", "text": "short", "source_ids": ["edition-other"], "evidence": [{"locator": "identified alternative"}], "status": "attested", "independence_group": "other-tradition"}]}

    def test_no_automatic_shorter_or_majority(self):
        p = self.variant()
        p["readings"][1]["source_ids"] = ["LXX", "DSS"]
        r = evaluate_variant(p)
        self.assertEqual(r["selected_reading_id"], "base")
        self.assertEqual(r["footnotes"][0]["reading_id"], "short")

    def test_reconstruction_cannot_be_attested_primary(self):
        p = self.variant(); p["readings"][1]["status"] = "reconstructed"
        p["assessment"] = {"selected_reading_id": "short", "reason": "some rationale", "evidence": ["source"], "counter_evidence": [], "reviewer": "test", "confidence": "low"}
        with self.assertRaises(StudyError): evaluate_variant(p)

    def test_base_and_inclusion_need_exact_evidence(self):
        p = self.variant(); p["readings"][0]["evidence"] = []
        with self.assertRaises(StudyError): evaluate_variant(p)
        p = self.variant(); p["readings"][1]["text"] = ""; p["requested_inclusion_id"] = "short"
        with self.assertRaises(StudyError): evaluate_variant(p)

    @staticmethod
    def handoff():
        return {"schema_version": "0.1.0", "study_id": "rom12", "stage": "translate_annotate", "reference": "Romans 12:1-2", "language": "en", "translation_format": "plain_working", "depends_on": ["reading"], "evidence": [{"id": "source", "locator": "Rom 12:1"}], "payload": {"verses": [{"reference": "Romans 12:1", "working_translation": "Therefore, I appeal to you.", "alignment_groups": []}], "footnotes": [], "term_key": [], "context_preface": "The appeal follows the preceding argument."}, "uncertainties": []}

    def test_handoff_fields_scope_and_budget(self):
        self.assertTrue(validate_handoff(self.handoff())["valid"])
        for change in ({"extra": True}, {"reference": "Romans 12-13"}):
            p = self.handoff(); p.update(change)
            with self.assertRaises(StudyError): validate_handoff(p)
        p = self.handoff(); p["payload"]["context_preface"] = "x" * 16001
        with self.assertRaises(StudyError): validate_handoff(p)

    def test_interlinear_requires_alignment(self):
        p = self.handoff(); p["translation_format"] = "original_interlinear"
        with self.assertRaises(StudyError): validate_handoff(p)
        p["payload"]["verses"][0]["alignment_groups"] = [{"source_token_ids": ["SBLGNT:Rom:12:1:token:1"], "original": "Παρακαλῶ", "transliteration": "parakalō", "gloss": "I appeal"}]
        self.assertTrue(validate_handoff(p)["valid"])

    def test_span_integrity_and_path_guard(self):
        pointer = self.engine.reader.chapters[("wlc-4.20-oshb", "Gen", 1)]
        broken = dict(pointer, sha256="0" * 64)
        with self.assertRaises(StudyError): self.engine.store.span(broken)
        for path in ("../secret", "/secret", "dir\\secret"):
            with self.assertRaises(StudyError): self.engine.store.safe_path(path)

    def test_skill_references_resolve(self):
        root = Path(__file__).resolve().parents[1]
        skills = list((root / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 8)
        for skill in skills:
            self.assertLess(len(skill.read_text().splitlines()), 500)
            self.assertNotIn("TODO", skill.read_text())
            for target in re.findall(r"\]\(([^)]+)\)", skill.read_text()):
                if not target.startswith("https:"): self.assertTrue((skill.parent / target).resolve().is_file(), target)


if __name__ == "__main__":
    unittest.main()
