"""Optional MCP 2.3 stdio adapter. All tools are read-only."""
from functools import lru_cache
from typing import Any
from . import __version__
from .engine import Engine
from .evaluation import evaluate_variant
from .handoff import validate_handoff
from .store import StudyError


def build_server():
    try:
        from mcp.server import MCPServer
        from mcp.types import ToolAnnotations
    except ImportError as e:
        raise SystemExit('Install the optional adapter with: pip install ".[mcp]"') from e
    server = MCPServer("source-text-bible-study", version=__version__)
    annotations = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True)

    @lru_cache(maxsize=1)
    def engine():
        return Engine()

    def safe(function, *args):
        try:
            return function(*args)
        except StudyError as error:
            return error.as_dict()

    @server.tool(annotations=annotations, structured_output=True)
    def study_health() -> dict[str, Any]:
        """Describe actual source coverage, pinned revision and MVP limitations."""
        return safe(lambda: engine().health())

    @server.tool(annotations=annotations, structured_output=True)
    def study_plan(query: str, active_reference: str | None = None, language: str = "en", translation_format: str = "plain_working", study_state: dict[str, Any] | None = None) -> dict[str, Any]:
        """Route a command; split long requests and continue with Next and the previous continuation_state."""
        return safe(lambda: engine().plan(query, active_reference, language, translation_format, study_state))

    @server.tool(annotations=annotations, structured_output=True)
    def fetch_passage(reference: str, sources: list[str] | None = None, detail: str = "text") -> dict[str, Any]:
        """Fetch the first bounded portion from named public editions; native labels do not certify alignment."""
        return safe(lambda: engine().reader.passage(reference, sources, detail))

    @server.tool(annotations=annotations, structured_output=True)
    def fetch_apparatus(reference: str) -> dict[str, Any]:
        """Fetch SBLGNT edition-comparison apparatus entries; not a full manuscript apparatus."""
        return safe(lambda: engine().reader.apparatus(reference))

    @server.tool(annotations=annotations, structured_output=True)
    def fetch_dss(reference: str, cursor: int = 0, limit: int = 1, include_linguistics: bool = True) -> dict[str, Any]:
        """Page DSS physical readings, explicit reconstruction statuses and separately attributed linguistic annotations."""
        return safe(lambda: engine().reader.dss(reference, cursor, limit, include_linguistics))

    @server.tool(annotations=annotations, structured_output=True)
    def lookup_word(query: str, context_ids: list[str] | None = None) -> dict[str, Any]:
        """Retrieve one or two complete curated studies and at most six compact context pointers."""
        return safe(lambda: engine().knowledge.word(query, context_ids))

    @server.tool(annotations=annotations, structured_output=True)
    def lookup_lexical(entry_id: str) -> dict[str, Any]:
        """Retrieve selected attributed STEP/Open Scriptures lexical records by ID."""
        return safe(lambda: engine().knowledge.lexical(entry_id))

    @server.tool(annotations=annotations, structured_output=True)
    def lookup_trajectory(query: str) -> dict[str, Any]:
        """Retrieve a small canonical seed dossier; anchors are pointers, not automatically fetched texts."""
        return safe(lambda: engine().knowledge.trajectory(query))

    @server.tool(annotations=annotations, structured_output=True)
    def evaluate_reading(record: dict[str, Any]) -> dict[str, Any]:
        """Validate an evidence-based reading assessment; never choose by theology, length or corpus majority alone."""
        return safe(evaluate_variant, record)

    @server.tool(annotations=annotations, structured_output=True)
    def check_handoff(packet: dict[str, Any]) -> dict[str, Any]:
        """Check strict pipeline stage fields, types, scope and size; interpretive accuracy needs host review."""
        return safe(validate_handoff, packet)

    return server


def main():
    build_server().run()


if __name__ == "__main__":
    main()
