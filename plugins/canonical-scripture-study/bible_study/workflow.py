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
        "response_sections": focused.get(mode, profile["sections"]),
        "delivery": {
            "mode": "progressive_in_current_turn",
            "preferred_surface": "sequential_assistant_messages_if_supported",
            "fallback_surface": "single_streamed_answer_with_milestones",
            "requires_user_prompt_between_milestones": False,
            "background_jobs": False,
            "milestones": [DELIVERY_MILESTONES[id] for id in FOCUSED_MILESTONES.get(mode, ["orientation", "translation_ready", "explanation_ready", "synthesis_ready"])],
            "instruction": "Complete every applicable milestone for the current passage without waiting for user input. Prefer a short visible orientation, then separate visible assistant updates as each verified result is ready; present the translation and notes before deeper explanation. If the host cannot issue successive assistant messages, stream a single answer in the same order. Never claim later tool calls or background work will happen after the reply ends. Next means a different passage, not the next study phase.",
        },
        "source_policy": {"order": method["source_order"], "independent_analysis_first": True, "external_research_default": "selective_after_independent_analysis" if depth == "full" else "off", "explicit_research_request_can_override": True, "instruction": method["secondary_resources"]},
        "reading_aids": {"names_and_places": "Explain relevant names, places or objects from attested wording, explicit biblical wordplay or a sourced etymology; mark disputed or unknown origins and do not derive doctrine from a name.", "literary_structure": "Show verse-linked line breaks, parallelism, repetition or a compact structure table where it aids comprehension at any depth. Label a proposed chiasm and do not manufacture symmetry."},
        "budgets": budgets,
    }
