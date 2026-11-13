"""Query a completed index without using benchmark gold."""
import argparse
import json
from .prepare import ROOT
from .embeddings import MyEmbedder
from .store import QdrantStore

def main():
    p = argparse.ArgumentParser()
    p.add_argument("question")
    p.add_argument("--strategy", choices=list("ABC"), default="C")
    p.add_argument("--group", choices=["tong_luan_va_so_che", "phoi_hop_nguyen_lieu", "lam_chin", "trinh_bay"])
    args = p.parse_args()
    if args.group and args.strategy != "C":
        p.error("--group only applies to strategy C")
    cfg = json.loads((ROOT / "configs/experiment.json").read_text(encoding="utf-8"))
    embedder = MyEmbedder(cfg["model"], ROOT / ".cache/models")
    store = QdrantStore(ROOT / ".local/qdrant", embedder.dimensions)
    try:
        hits = store.search(args.strategy, embedder.embed_query(args.question),
                            filters={"content_group": args.group} if args.group else {})
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    finally:
        store.close()

if __name__ == "__main__":
    main()
