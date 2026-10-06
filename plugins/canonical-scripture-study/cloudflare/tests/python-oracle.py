"""Compare the Worker port with the existing published Python runtime."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bible_study.engine import Engine
from bible_study.evaluation import evaluate_variant
from bible_study.handoff import validate_handoff
from bible_study.store import StudyError

engine = Engine()

def call(case):
    kind, args = case["kind"], case["args"]
    functions = {
        "plan": engine.plan,
        "passage": engine.reader.passage,
        "apparatus": engine.reader.apparatus,
        "dss": engine.reader.dss,
        "word": engine.knowledge.word,
        "lexical": engine.knowledge.lexical,
        "trajectory": engine.knowledge.trajectory,
        "evaluate": evaluate_variant,
        "handoff": validate_handoff,
        "portions": engine.refs.portions,
        "native": engine.reader.native_chapter,
    }
    try:
        return functions[kind](*args)
    except StudyError as error:
        # Domain error messages can differ; the contract is the machine-readable code.
        return {"domain_error": error.code}

print(json.dumps([call(case) for case in json.load(sys.stdin)], ensure_ascii=False))
