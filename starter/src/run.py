"""Run from repo root: python -m starter.src.run."""
import argparse
import hashlib
import importlib.metadata
import json
import logging
import platform
import statistics
import time
from dataclasses import asdict
from datetime import datetime, timezone, timedelta

from .chunking import fixed_size, by_paragraph
from .embeddings import MyEmbedder
from .evaluation import evaluate_query, summarize
from .prepare import ROOT, prepare_pages, build_benchmark, save_json, save_jsonl
from .store import QdrantStore

def stamp():
    return datetime.now(timezone(timedelta(hours=7))).isoformat()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler(results / "pipeline.log", mode="w", encoding="utf-8")])
    try:
        run(args)
    except Exception:
        logging.exception("Pipeline failed; no mock fallback")
        raise

def run(args):
    started = time.perf_counter()
    config_path = ROOT / "configs/experiment.json"
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    pages = prepare_pages()
    questions = build_benchmark(pages)
    lock_path = ROOT / "benchmark/lock.json"
    fingerprint = {"questions_sha256": digest(ROOT / "benchmark/questions.jsonl"),
                   "config_sha256": digest(config_path),
                   "rules_sha256": digest(ROOT / "data/content_rules.json"),
                   "pdf_sha256": digest(ROOT / "data/raw/tai_lieu.pdf")}
    if lock_path.exists():
        old = json.loads(lock_path.read_text(encoding="utf-8"))
        if old["fingerprint"] != fingerprint:
            raise ValueError("Locked inputs changed. Create an explicitly documented new experiment.")
    else:
        save_json(lock_path, {"locked_at": stamp(), "fingerprint": fingerprint,
                             "selection_rule": cfg["selection_rule"],
                             "split_method": "15 dev / 5 test; different evidence pages, same document and topics. Not document-independent.",
                             "author": "Codex AI assistance, to be reviewed by student",
                             "test_use": "Test not used for tuning. Author saw source when writing gold; no blind human adjudication."})
    chunks_by = {}
    for s, c in cfg["strategies"].items():
        chunks_by[s] = [chunk for page in pages for chunk in (
            fixed_size(page, c["size"], c["overlap"]) if c["chunking"] == "fixed"
            else by_paragraph(page, c["size"]))]
        save_jsonl(ROOT / f"results/chunks_{s}.jsonl", [asdict(c) for c in chunks_by[s]])
    # Predeclare qualitative sample positions before examining metrics.
    samples = []
    for s, chunks in chunks_by.items():
        for number in cfg["coherence_pages"]:
            page = next(p for p in pages if p.page == number)
            anchor = len(page.text) // 2
            chunk = next(c for c in chunks if c.page == number
                         and c.metadata["start_char"] <= anchor < c.metadata["end_char"])
            samples.append({"strategy": s, "page": number, "anchor": anchor,
                            "chunk": asdict(chunk), "source_text": page.text,
                            "score": None, "reason": None, "reviewer": None})
    save_jsonl(ROOT / "results/coherence_samples.jsonl", samples)
    if args.prepare_only:
        logging.info("Prepared %s pages and %s questions; benchmark locked", len(pages), len(questions))
        return

    t = time.perf_counter()
    embedder = MyEmbedder(cfg["model"], ROOT / ".cache/models")
    model_load_seconds = time.perf_counter() - t
    store = QdrantStore(ROOT / ".local/qdrant", embedder.dimensions)
    statistics_rows, vectors_by = [], {}
    try:
        for s, chunks in chunks_by.items():
            t = time.perf_counter()
            # B and C use exactly the same chunks/vectors; C cost is reuse + storage.
            if s == "C":
                vectors = vectors_by["B"]
                embedding_seconds = 0.0
            else:
                vectors = embedder.embed_documents([c.text for c in chunks])
                embedding_seconds = time.perf_counter() - t
            vectors_by[s] = vectors
            t = time.perf_counter()
            store.replace(s, chunks, vectors)
            storage_seconds = time.perf_counter() - t
            before = store.count(s)
            store.upsert(s, chunks, vectors)
            after = store.count(s)
            if before != after or after != len(chunks):
                raise ValueError("Duplicate reload detected")
            lengths = [len(c.text) for c in chunks]
            statistics_rows.append({"strategy": s, "chunks": len(chunks),
                "length_min": min(lengths), "length_max": max(lengths),
                "length_mean": statistics.mean(lengths), "total_characters": sum(lengths),
                "embedding_seconds": embedding_seconds, "storage_seconds": storage_seconds,
                "embedding_reused_from": "B" if s == "C" else None,
                "cost_usd": 0, "count_before_upsert": before, "count_after_upsert": after})
            logging.info("Strategy %s: %s chunks, embed %.2fs, store %.2fs, reload OK",
                         s, len(chunks), embedding_seconds, storage_seconds)
        # Close/reopen to actually check persistent storage.
        store.close()
        store = QdrantStore(ROOT / ".local/qdrant", embedder.dimensions)
        for row in statistics_rows:
            row["count_after_reopen"] = store.count(row["strategy"])
            if row["count_after_reopen"] != row["chunks"]:
                raise ValueError("Persistence check failed")
        traces = []
        for split in ("dev", "test"):
            for q in [q for q in questions if q["split"] == split]:
                # Embed only question text. Gold answer/page never enters retrieval.
                vector = embedder.embed_query(q["question"])
                for s in "ABC":
                    filters = q["filter"] if cfg["strategies"][s]["filter"] else {}
                    t = time.perf_counter()
                    hits = store.search(s, vector, cfg["top_k"], filters)
                    trace = evaluate_query(q, hits)
                    trace.update({"strategy": s, "applied_filter": filters,
                                  "search_seconds": time.perf_counter() - t})
                    traces.append(trace)
            if split == "dev":
                metrics = summarize(traces)
                counts = {r["strategy"]: r["chunks"] for r in statistics_rows}
                selected = sorted(metrics, key=lambda r: (
                    -r["hit3"], -r["hit1"], counts[r["strategy"]], r["strategy"]))[0]["strategy"]
                save_json(ROOT / "results/selection.json", {
                    "selected_strategy": selected, "selected_at": stamp(),
                    "rule": cfg["selection_rule"], "dev_metrics": metrics,
                    "test_evaluated_at_selection": False, "fingerprint": fingerprint})
                save_jsonl(ROOT / "results/dev_traces.jsonl", traces)
                logging.info("Selected %s using dev only; now evaluating test", selected)
        save_jsonl(ROOT / "results/traces.jsonl", traces)
        save_json(ROOT / "results/metrics.json", summarize(traces))
        save_json(ROOT / "results/ingestion_stats.json", statistics_rows)
        save_jsonl(ROOT / "results/test_audit_samples.jsonl",
                   [t for t in traces if t["question"]["split"] == "test"])
        packages = {name: importlib.metadata.version(name) for name in (
            "fastembed", "qdrant-client", "pypdf", "onnxruntime", "numpy", "grpcio", "tokenizers")}
        model_files = []
        for path in sorted((ROOT / ".cache/models").rglob("*")):
            if path.is_file() and path.suffix in {".onnx", ".json"}:
                model_files.append({"path": str(path.relative_to(ROOT / ".cache/models")),
                                    "sha256": digest(path)})
        save_json(ROOT / "results/run_info.json", {
            "completed_at": stamp(), "python": platform.python_version(),
            "platform": platform.platform(), "packages": packages, "config": cfg,
            "model_load_seconds": model_load_seconds,
            "total_seconds": time.perf_counter() - started, "api_cost_usd": 0,
            "cost_scope": "No paid API; electricity/hardware/network cost not measured",
            "search": "Qdrant local exact cosine; no ANN index", "fingerprint": fingerprint,
            "model_files": model_files,
            "qualitative_review_status": "AI-assisted inspection; student human confirmation pending"})
    finally:
        store.close()
    logging.info("Completed; results saved under results/")

if __name__ == "__main__":
    main()
