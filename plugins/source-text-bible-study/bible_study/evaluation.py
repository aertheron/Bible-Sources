"""Evidence contracts: heuristics never automatically elect a variant."""
from .reference import References
from .store import StudyError, bounded, config


def textual_cases(reference, refs=None):
    refs = refs or References()
    p = refs.parse(reference)
    matches = []
    for row in config("textual-cases")["cases"]:
        try:
            q = refs.parse(row["reference"], allow_book=True)
        except StudyError:
            continue
        if p.book == q.book and (p.start_chapter, p.start_verse) <= (q.end_chapter, q.end_verse) and (q.start_chapter, q.start_verse) <= (p.end_chapter, p.end_verse):
            matches.append(row)
    return matches


def evaluate_variant(record):
    required = {"reference", "base_reading_id", "significance", "readings"}
    allowed = required | {"assessment", "requested_inclusion_id"}
    if not isinstance(record, dict) or not required <= record.keys() or record.keys() - allowed:
        raise StudyError("variant_contract", "Supply reference, base_reading_id, significance and readings; only assessment and requested_inclusion_id are optional.")
    refs = References(); refs.scope(refs.parse(record["reference"]))
    if not isinstance(record["significance"], str) or record["significance"] not in {"semantic", "theological", "insignificant", "uncertain"}:
        raise StudyError("variant_contract", "Significance must be semantic, theological, insignificant or uncertain.")
    readings = record["readings"]
    if not isinstance(readings, list) or not 1 <= len(readings) <= 12:
        raise StudyError("variant_contract", "Supply one to twelve identified readings.")
    by_id = {}
    for r in readings:
        if not isinstance(r, dict) or set(r) != {"id", "text", "source_ids", "evidence", "status", "independence_group"}:
            raise StudyError("variant_contract", "Each reading needs exactly id, text, source_ids, evidence, status and independence_group.")
        if not isinstance(r["id"], str) or not r["id"] or r["id"] in by_id or not isinstance(r["text"], str) or not isinstance(r["independence_group"], str):
            raise StudyError("variant_contract", "Reading IDs must be unique; text and independence group must be strings.")
        if not isinstance(r["status"], str) or r["status"] not in {"attested", "reconstructed", "unverified", "unavailable"} or not isinstance(r["source_ids"], list) or any(not isinstance(x, str) or not x for x in r["source_ids"]) or not isinstance(r["evidence"], list):
            raise StudyError("variant_contract", "Invalid reading status or source/evidence arrays.")
        if r["status"] == "attested" and (not r["source_ids"] or not r["evidence"]):
            raise StudyError("variant_evidence", "An attested reading requires an identified source and evidence, including attested omissions.")
        by_id[r["id"]] = r
    if not isinstance(record["base_reading_id"], str):
        raise StudyError("variant_base", "The base reading ID must be a string.")
    base = by_id.get(record["base_reading_id"])
    if base is None or base["status"] != "attested":
        raise StudyError("variant_base", "The named base reading must be supplied as attested with evidence.")
    selected = base; status = "provisional_named_base"; reason = "No completed evidence assessment selects another reading."
    assessment = record.get("assessment")
    if assessment is not None:
        fields = {"selected_reading_id", "reason", "evidence", "counter_evidence", "reviewer", "confidence"}
        if not isinstance(assessment, dict) or set(assessment) != fields or not isinstance(assessment["selected_reading_id"], str) or not isinstance(assessment["confidence"], str) or assessment["confidence"] not in {"low", "medium", "high"} or not all(isinstance(assessment[k], str) and assessment[k].strip() for k in ["reason", "reviewer"]) or not isinstance(assessment["evidence"], list) or not assessment["evidence"] or not isinstance(assessment["counter_evidence"], list):
            raise StudyError("variant_assessment", "Assessment requires the selected ID, reason, evidence, counter_evidence, reviewer and low/medium/high confidence.")
        candidate = by_id.get(assessment["selected_reading_id"])
        if not candidate or candidate["status"] != "attested":
            raise StudyError("variant_assessment", "A reconstructed, unavailable or unverified reading cannot be asserted as the attested primary text.")
        selected = candidate; status = "reviewed_selection_contract_valid"; reason = assessment["reason"]
    if record["significance"] == "insignificant":
        selected = base; status = "insignificant_base_retained"; reason = "Retain the named base for non-semantic differences; keep all evidence in the packet."
    cases = textual_cases(record["reference"], refs)
    inclusion = None
    if record.get("requested_inclusion_id") is not None:
        if not isinstance(record["requested_inclusion_id"], str):
            raise StudyError("variant_inclusion", "The inclusion reading ID must be a string.")
        r = by_id.get(record["requested_inclusion_id"])
        if not cases or not r or r["status"] != "attested" or not r["text"].strip():
            raise StudyError("variant_inclusion", "Bracketed study inclusion needs a registered case and exact, nonempty, attested source text.")
        inclusion = {"reading_id": r["id"], "text": r["text"], "display": "square_brackets_with_factual_footnote", "authenticity": "separate_from_study_inclusion"}
    return bounded({"reference": record["reference"], "selected_reading_id": selected["id"], "selected_text": selected["text"], "status": status, "reason": reason, "assessment": assessment, "footnotes": [{"reading_id": r["id"], "text": r["text"], "source_ids": r["source_ids"], "status": r["status"], "evidence": r["evidence"]} for r in readings if r["id"] != selected["id"]], "all_readings": readings, "special_cases": cases, "study_inclusion": inclusion, "warnings": ["Contract validation does not independently authenticate cited evidence or certify the reviewer's judgment.", "Christology, difficulty, brevity and numerical agreement are clues, not automatic winners.", "A corpus label or a modern edition must not be counted as an independent manuscript vote."]}, 16000)
