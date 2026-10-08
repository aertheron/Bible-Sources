"""JSON CLI; stdin/file inputs preserve exact structured records."""
import argparse
import json
from pathlib import Path
import sys
from .engine import Engine
from .evaluation import evaluate_variant
from .handoff import validate_handoff
from .store import SourceStore, StudyError


def load_json(filename):
    return json.load(sys.stdin) if filename == "-" else json.loads(Path(filename).read_text(encoding="utf-8"))


def main(argv=None):
    p = argparse.ArgumentParser(description="Canonical Scripture Study: bounded JSON retrieval and study planning.")
    p.add_argument("--data-root"); p.add_argument("--cache-root"); p.add_argument("--offline", action="store_true", default=None)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("health")
    plan = sub.add_parser("plan"); plan.add_argument("query"); plan.add_argument("--active-reference"); plan.add_argument("--language", default="en"); plan.add_argument("--format", default="plain_working"); plan.add_argument("--state", help="JSON continuation_state file; '-' reads stdin"); plan.add_argument("--depth", choices=["standard", "detailed", "full"])
    read = sub.add_parser("passage"); read.add_argument("reference"); read.add_argument("--sources", nargs="+"); read.add_argument("--detail", choices=["text", "linguistic"], default="text")
    app = sub.add_parser("apparatus"); app.add_argument("reference")
    dss = sub.add_parser("dss"); dss.add_argument("reference"); dss.add_argument("--cursor", type=int, default=0); dss.add_argument("--limit", type=int, default=1); dss.add_argument("--no-linguistics", action="store_true")
    word = sub.add_parser("word"); word.add_argument("query"); word.add_argument("--contexts", nargs="*")
    lex = sub.add_parser("lexical"); lex.add_argument("entry_id")
    trajectory = sub.add_parser("trajectory"); trajectory.add_argument("query")
    for name in ("evaluate", "validate-handoff"):
        item = sub.add_parser(name); item.add_argument("input", help="JSON filename or '-' for stdin")
    args = p.parse_args(argv)
    try:
        engine = Engine(SourceStore(args.data_root, args.cache_root, args.offline))
        if args.command == "health": result = engine.health()
        elif args.command == "plan": result = engine.plan(args.query, args.active_reference, args.language, args.format, load_json(args.state) if args.state else None, args.depth)
        elif args.command == "passage": result = engine.reader.passage(args.reference, args.sources, args.detail)
        elif args.command == "apparatus": result = engine.reader.apparatus(args.reference)
        elif args.command == "dss": result = engine.reader.dss(args.reference, args.cursor, args.limit, not args.no_linguistics)
        elif args.command == "word": result = engine.knowledge.word(args.query, args.contexts)
        elif args.command == "lexical": result = engine.knowledge.lexical(args.entry_id)
        elif args.command == "trajectory": result = engine.knowledge.trajectory(args.query)
        elif args.command == "evaluate": result = evaluate_variant(load_json(args.input))
        else: result = validate_handoff(load_json(args.input))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (StudyError, json.JSONDecodeError) as e:
        error = e.as_dict() if isinstance(e, StudyError) else {"error": {"code": "json_input", "message": str(e)}}
        print(json.dumps(error, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
