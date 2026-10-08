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
        "delivery": {"mode": "progressive_in_current_turn", "background_jobs": False, "instruction": "State a short plan, retrieve necessary evidence, then show context and translation/notes before deeper explanation when the host supports progressive output. Complete the requested scope in this turn; do not require Continue for the same portion or promise work after the reply ends."},
        "source_policy": {"order": method["source_order"], "independent_analysis_first": True, "external_research_default": "selective_after_independent_analysis" if depth == "full" else "off", "explicit_research_request_can_override": True, "instruction": method["secondary_resources"]},
        "reading_aids": {"names_and_places": "Explain relevant names, places or objects from attested wording, explicit biblical wordplay or a sourced etymology; mark disputed or unknown origins and do not derive doctrine from a name.", "literary_structure": "Show verse-linked line breaks, parallelism, repetition or a compact structure table where it aids comprehension at any depth. Label a proposed chiasm and do not manufacture symmetry."},
        "budgets": budgets,
    }
