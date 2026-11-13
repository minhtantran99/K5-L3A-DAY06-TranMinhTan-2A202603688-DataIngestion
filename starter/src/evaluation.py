"""Complete evidence match. Qualitative labels are assessed separately."""
import re

def canonical(text):
    return re.sub(r"\s+", " ", text).strip()

def evaluate_query(question, hits):
    golds = question.get("gold_alternatives", []) + [{
        "source_id": question["gold_source_id"], "page": question["gold_page"],
        "evidence_quote": question["evidence_quote"]}]
    matches = [any(h["document_id"] == g["source_id"] and h["page"] == g["page"]
                   and canonical(g["evidence_quote"]) in canonical(h["text"])
                   for g in golds) for h in hits]
    return {"question": question, "hits": hits, "evidence_matches": matches,
            "hit1": bool(matches and matches[0]), "hit3": any(matches)}

def summarize(traces):
    rows = []
    for strategy in "ABC":
        for split in ("dev", "test"):
            group = [t for t in traces if t["strategy"] == strategy
                     and t["question"]["split"] == split]
            if not group:
                continue
            n = len(group)
            h1, h3 = sum(t["hit1"] for t in group), sum(t["hit3"] for t in group)
            rows.append({"strategy": strategy, "split": split, "n": n,
                         "hit1_n": h1, "hit3_n": h3, "hit1": h1 / n, "hit3": h3 / n})
    return rows
