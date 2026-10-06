"""Strict stage envelopes with explicit limits; not a linguistic truth oracle."""
import re
from .engine import FORMATS, validate_preferences
from .reference import References
from .store import StudyError, bounded


PAYLOADS = {
    "fetch_align": {"source_packets": list, "alignment_status": str},
    "collate_compare": {"differences": list, "comparison_limits": list},
    "evaluate_select": {"decisions": list, "unresolved": list},
    "translate_annotate": {"verses": list, "footnotes": list, "term_key": list, "context_preface": str},
    "exegetical_synthesis": {"observations": list, "biblical_development": list, "canonical_links": list, "formation": list},
    "theology_review": {"claim_reconstruction": str, "findings": list, "verdict": str},
    "dss_research": {"records": list, "reconstruction_limits": list},
}


def validate_handoff(packet):
    fields = {"schema_version", "study_id", "stage", "reference", "language", "translation_format", "depends_on", "evidence", "payload", "uncertainties"}
    if not isinstance(packet, dict) or set(packet) != fields:
        raise StudyError("handoff_fields", "Use exactly the ten documented stage-envelope fields.")
    if packet["schema_version"] != "0.1.0" or not isinstance(packet["study_id"], str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", packet["study_id"]):
        raise StudyError("handoff_version", "Use schema 0.1.0 and a short stable study ID.")
    stage = packet["stage"]
    if not isinstance(stage, str) or stage not in PAYLOADS:
        raise StudyError("handoff_stage", "Unrecognized pipeline stage.")
    validate_preferences(packet["language"], packet["translation_format"])
    refs = References(); scope = None
    if packet["reference"] is not None:
        scope = refs.scope(refs.parse(packet["reference"]))
        if refs.count(scope) > 45:
            raise StudyError("handoff_scope", "Process a long chapter in the planned smaller portions before creating this handoff.")
    for name in ("depends_on", "uncertainties"):
        values = packet[name]
        if not isinstance(values, list) or len(values) > 64 or any(not isinstance(v, str) for v in values):
            raise StudyError("handoff_array", f"{name} must be an array of at most 64 strings.")
    evidence = packet["evidence"]
    if not isinstance(evidence, list) or len(evidence) > 64 or any(not isinstance(e, dict) or not all(isinstance(e.get(k), str) and e[k] for k in ("id", "locator")) for e in evidence):
        raise StudyError("handoff_evidence", "Evidence must contain at most 64 objects with nonempty id and locator strings.")
    if len({e["id"] for e in evidence}) != len(evidence):
        raise StudyError("handoff_evidence", "Evidence IDs must be unique.")
    payload = packet["payload"]
    if not isinstance(payload, dict) or set(payload) != set(PAYLOADS[stage]) or any(not isinstance(payload[k], t) for k, t in PAYLOADS[stage].items()):
        raise StudyError("handoff_payload", "Payload must match the exact fields and types for this stage.")
    if stage == "translate_annotate":
        if scope is None or not payload["verses"]:
            raise StudyError("translation_scope", "A translation needs an explicit bounded reference and at least one verse.")
        seen = set()
        for row in payload["verses"]:
            if not isinstance(row, dict) or set(row) != {"reference", "working_translation", "alignment_groups"} or not isinstance(row["working_translation"], str) or not row["working_translation"].strip() or not isinstance(row["alignment_groups"], list):
                raise StudyError("translation_verse", "Each verse needs exactly reference, working_translation and alignment_groups.")
            p = refs.parse(row["reference"])
            if p.book != scope.book or (p.start_chapter, p.start_verse) != (p.end_chapter, p.end_verse) or not scope.contains(p.start_chapter, p.start_verse) or (p.start_chapter, p.start_verse) in seen:
                raise StudyError("translation_verse", "Verse rows must be unique single verses within the envelope reference.")
            seen.add((p.start_chapter, p.start_verse))
            if packet["translation_format"] != "plain_working" and not row["alignment_groups"]:
                raise StudyError("interlinear_alignment", "An interlinear display requires original/transliteration/gloss groups tied to source token IDs.")
            for group in row["alignment_groups"]:
                if not isinstance(group, dict) or set(group) != {"source_token_ids", "original", "transliteration", "gloss"} or not all(isinstance(group[k], str) and group[k].strip() for k in ("original", "transliteration", "gloss")) or not isinstance(group["source_token_ids"], list) or not group["source_token_ids"] or any(not isinstance(i, str) or not i for i in group["source_token_ids"]):
                    raise StudyError("interlinear_alignment", "Each alignment group needs source_token_ids, original, transliteration and gloss.")
    bounded(packet, 16000)
    return {"valid": True, "study_id": packet["study_id"], "stage": stage, "schema_version": "0.1.0", "limitations": "Validation checks structure, scope and size. The host must check complete source coverage, token alignment, cited evidence and interpretive accuracy."}
