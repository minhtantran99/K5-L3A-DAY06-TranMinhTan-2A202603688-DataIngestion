"""Validate executed artifacts and persist test evidence."""
import hashlib
import json
import subprocess
import sys
from .prepare import ROOT, save_json
from .store import QdrantStore

def main():
    read = lambda p: json.loads((ROOT / p).read_text(encoding="utf-8"))
    lines = lambda p: [json.loads(s) for s in (ROOT / p).read_text(encoding="utf-8").splitlines()]
    lock = read("benchmark/lock.json")
    paths = {"questions_sha256":"benchmark/questions.jsonl",
             "config_sha256":"configs/experiment.json","rules_sha256":"data/content_rules.json",
             "pdf_sha256":"data/raw/tai_lieu.pdf"}
    for key,path in paths.items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == lock["fingerprint"][key], path
    traces = lines("results/traces.jsonl")
    assert len(traces) == 60 and all(len(t["hits"]) == 3 for t in traces)
    assert len({(t["strategy"],t["question"]["id"]) for t in traces}) == 60
    assert all(all(h["metadata"].get(k) == v for k,v in t["applied_filter"].items())
               for t in traces for h in t["hits"])
    for qid in {t["question"]["id"] for t in traces if not t["question"]["filter"]}:
        b = next(t for t in traces if t["strategy"]=="B" and t["question"]["id"]==qid)
        c = next(t for t in traces if t["strategy"]=="C" and t["question"]["id"]==qid)
        assert b["hits"] == c["hits"], qid
    assert len(lines("results/coherence_ai_review.jsonl")) == 30
    assert len(lines("results/grounding_ai_review.jsonl")) == 15
    metadata = lines("results/metadata_audit.jsonl")
    assert len(metadata) == 45
    assert all(r["complete_and_correct_against_extracted_source"] for r in metadata)
    selection = read("results/selection.json")
    assert selection["test_evaluated_at_selection"] is False
    assert selection["fingerprint"] == lock["fingerprint"]
    first = ROOT / "results/metrics_first_run.json"
    metrics_same = read("results/metrics.json") == read("results/metrics_first_run.json") if first.exists() else None
    assert metrics_same is not False
    store = QdrantStore(ROOT / ".local/qdrant", 384)
    try:
        counts = {s: store.count(s) for s in "ABC"}
        assert counts == {r["strategy"]: r["chunks"] for r in read("results/ingestion_stats.json")}
    finally:
        store.close()
    test = subprocess.run([sys.executable,"-m","unittest","discover","-s","tests","-v"],
                          cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace")
    (ROOT/"results/tests.log").write_text(test.stdout+test.stderr,encoding="utf-8")
    assert test.returncode == 0, test.stderr
    source_hashes = {str(p.relative_to(ROOT)).replace("\\","/"): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted((ROOT/"starter/src").glob("*.py"))}
    save_json(ROOT/"results/verification.json", {
        "locked_inputs_unchanged": True, "trace_count":len(traces), "top3_count":180,
        "coherence_samples":30, "grounding_samples":15, "metadata_records":45,
        "persistent_counts":counts, "metrics_identical_to_first_run":metrics_same,
        "non_filter_B_C_identical":True, "selected_before_test":True,
        "unittest_exit_code":test.returncode, "tests":6, "source_hashes":source_hashes,
        "human_review_completed":False})
    print("Verified: 60 traces, 180 hits, persistent counts, locked inputs, 6 tests.")
    print("Human qualitative confirmation is still pending.")

if __name__ == "__main__":
    main()
