"""Study depth and delivery contracts; interpretation remains the host's task."""
from .store import StudyError, config

DEPTH_MODES = {"standard_study": "standard", "detailed_study": "detailed", "full_study": "full"}
DEPTH_OPTIONS = {"standard": "standard", "standaard": "standard", "detailed": "detailed", "uitgebreid": "detailed", "full": "full", "volledig": "full"}


def validate_depth(depth):
    if depth is not None and (not isinstance(depth, str) or depth not in config("method")["study_depths"]):
        raise StudyError("study_depth", "Use standard, detailed or full.")


def resolve_depth(mode, depth=None):
    validate_depth(depth)
    return DEPTH_MODES.get(mode, depth or config("method")["default_study_depth"])



DELIVERY_MILESTONES = {
    "orientation": {"id": "orientation", "ready_when": "The scope and necessary preceding context are identified; do not imply a translation is already verified.", "present": "A brief aim and orientation, without a lengthy plan."},
    "translation_ready": {"id": "translation_ready", "ready_when": "The relevant source wording, consequential variants and contextual translation have been checked.", "present": "The complete working translation for this bounded portion, with necessary factual footnotes; distinguish unresolved readings."},
    "explanation_ready": {"id": "explanation_ready", "ready_when": "Local wording, literary design and historical-cultural claims have been checked against the passage.", "present": "Exegesis, relevant terms, names and literary structure at the selected depth."},
    "synthesis_ready": {"id": "synthesis_ready", "ready_when": "Relevant canonical connections and theological claims have been checked, including substantive uncertainty.", "present": "Bounded biblical/canonical development, proportional theological synthesis and a conclusion."},
    "evidence_ready": {"id": "evidence_ready", "ready_when": "Relevant source evidence is retrieved and its limits identified.", "present": "Direct source observations and meaningful alternatives; do not imply a completed assessment."},
    "assessment_ready": {"id": "assessment_ready", "ready_when": "The focused assessment has been validated against available evidence.", "present": "Evidence-based assessment and what remains unresolved."},
}
FOCUSED_MILESTONES = {
    "translation_only": ["orientation", "translation_ready"],
    "exegesis_only": ["orientation", "explanation_ready", "synthesis_ready"],
    "context_history": ["orientation", "explanation_ready"],
    "variant_reconciliation": ["orientation", "evidence_ready", "assessment_ready"],
    "theology_check": ["orientation", "evidence_ready", "synthesis_ready"],
    "dss_research": ["orientation", "evidence_ready", "assessment_ready"],
    "word_study": ["orientation", "evidence_ready", "synthesis_ready"],
    "theme_study": ["orientation", "evidence_ready", "synthesis_ready"],
}

WORD_STUDY_SECTIONS = {
  "standard": [
    "core_meanings",
    "key_occurrences",
    "verified_lexical_evidence",
    "brief_contextual_and_canonical_summary"
  ],
  "detailed": [
    "core_meanings",
    "key_occurrences",
    "contextual_contrasts",
    "verified_lexical_evidence",
    "bounded_canonical_development"
  ],
  "full": [
    "source_forms_and_range",
    "contextual_sense_comparison",
    "key_occurrences_and_counterexamples",
    "verified_lexical_and_translation_evidence",
    "semantic_overlap_and_uncertainties",
    "canonical_development",
    "theological_synthesis_and_limits"
  ]
}
WORD_STUDY_GUIDANCE = {
  "standard": "Present a compact word study: core meaning range, 2–3 diagnostic biblical occurrences with explicit references, one noteworthy distinction or uncertainty, and a brief synthesis. Do not turn a normal word study into a long passage-by-passage survey.",
  "detailed": "Explain additional contextual contrasts and selected textual connections without forcing a comprehensive concordance or exhaustive canonical survey.",
  "full": "Produce a developed word study: original forms, occurrence-specific senses, 4–6 diagnostic passages including meaningful counterexamples, semantic overlap, relevant translation traditions and bounded canonical development. Compare external lexica or scholarship only when the actual entries are available and read; retain unresolved alternatives."
}
WORD_CITATION_POLICY = {
  "mode": "claim_level_verified_provenance",
  "primary_text": "For every decisive occurrence, give book/chapter/verse; identify source edition or witness when a wording, morphology, textual variant or translation claim depends on it. Cite the actual retrieved passage, not a remembered reading.",
  "lexical": "For each attributed lexicon claim, name the lexicon/source, lemma or entry ID, exact sense/subsection when available, and verse/example supporting the sense. Quote or paraphrase only entries actually retrieved/read. Do not attribute a sense to BDB, HALOT or another work just because the claim is plausible. Selected STEP/OSHB records do not verify BDB or HALOT.",
  "external": "If the original lexicon or other scholarly work is not accessible, state that the particular attribution has not been verified; describe the contextual reading as your own assessment instead of inventing a quotation, section, page or URL. For explicit lexicon questions, seek the requested source if available at any depth.",
  "source_classification": "Distinguish the primary biblical text, our curated model-assisted word-study record, selected lexicon data, and external scholarship. An internal study ID or source hash is provenance for project data, not proof that BDB/HALOT says something.",
  "placement": "Attach short readable references to the individual key claims; for Full, include a compact Sources consulted section with exact consulted entries and links only when verified. Do not add empty bibliographies or raw internal cache paths."
}

def workflow(mode, depth):
    method = config("method")
    profile = method["study_depths"][depth]
    budgets = dict(method["budgets"])
    budgets.update({key: profile[key] for key in ("canonical_anchors", "word_entries", "secondary_sources")})
    if not profile["secondary_sources"]:
        budgets.update(secondary_complete_entries=0, secondary_characters=0)
    focused = {
        "translation_only": ["orientation", "translation_notes"],
        "exegesis_only": ["orientation", "local_exegesis", "canonical_connections"],
        "context_history": ["orientation", "literary_historical_context"],
        "variant_reconciliation": ["orientation", "textual_comparison", "reading_assessment"],
        "theology_check": ["claim_reconstruction", "source_context_check", "theology_review"],
        "dss_research": ["reconstruction_status", "physical_readings", "linguistic_annotations"],
        "word_study": ["occurrence_context", "contextual_senses", "bounded_canonical_connections"],
        "theme_study": ["theme_orientation", "bounded_canonical_connections", "theological_synthesis"],
    }
    return {
        "study_depth": depth,
        "depth_label": profile["label"],
        "response_sections": WORD_STUDY_SECTIONS[depth] if mode == "word_study" else focused.get(mode, profile["sections"]),
        "delivery": {
            "mode": "progressive_in_current_turn",
            "preferred_surface": "sequential_assistant_messages_if_supported",
            "fallback_surface": "single_streamed_answer_with_milestones",
            "requires_user_prompt_between_milestones": False,
            "background_jobs": False,
            "milestones": [DELIVERY_MILESTONES[id] for id in FOCUSED_MILESTONES.get(mode, ["orientation", "translation_ready", "explanation_ready", "synthesis_ready"])],
            "instruction": "Complete every applicable milestone for the current passage without waiting for user input. Prefer a short visible orientation, then separate visible assistant updates as each verified result is ready; present the translation and notes before deeper explanation. If the host cannot issue successive assistant messages, stream a single answer in the same order. Never claim later tool calls or background work will happen after the reply ends. Next means a different passage, not the next study phase.",
        },
        **({"word_study_policy": {"default_depth": "standard", "available_depths": ["standard", "full"], "selected_depth": depth, "guidance": WORD_STUDY_GUIDANCE[depth], "target_diagnostic_occurrences": 6 if depth == "full" else 4 if depth == "detailed" else 3, "citation_policy": WORD_CITATION_POLICY}} if mode == "word_study" else {}),
        "source_policy": {"order": method["source_order"], "independent_analysis_first": True, "external_research_default": "selective_after_independent_analysis" if depth == "full" else "off", "explicit_research_request_can_override": True, "instruction": method["secondary_resources"]},
        "reading_aids": {"names_and_places": "Explain relevant names, places or objects from attested wording, explicit biblical wordplay or a sourced etymology; mark disputed or unknown origins and do not derive doctrine from a name.", "literary_structure": "Show verse-linked line breaks, parallelism, repetition or a compact structure table where it aids comprehension at any depth. Label a proposed chiasm and do not manufacture symmetry."},
        "budgets": budgets,
    }
