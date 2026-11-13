"""Local, read-only retrieval UI. Run: python -m starter.src.webapp --open."""
import argparse
import json
import logging
import math
import os
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
WEB = Path(__file__).resolve().parents[1] / "web"
GROUPS = {
    "tong_luan_va_so_che": "Tổng luận & sơ chế",
    "phoi_hop_nguyen_lieu": "Phối hợp nguyên liệu, gia vị",
    "lam_chin": "Phương pháp làm chín",
    "trinh_bay": "Trình bày món ăn",
}


def validate_search(body):
    if not isinstance(body, dict):
        raise ValueError("Yêu cầu phải là một đối tượng JSON.")
    question = body.get("question")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Bạn hãy nhập câu hỏi.")
    if len(question) > 2000:
        raise ValueError("Câu hỏi tối đa 2.000 ký tự.")
    strategy = body.get("strategy", "C")
    if not isinstance(strategy, str) or strategy not in {"A", "B", "C"}:
        raise ValueError("Cấu hình phải là A, B hoặc C.")
    group = body.get("group", "")
    if not isinstance(group, str) or (group and group not in GROUPS):
        raise ValueError("Nhóm nội dung không hợp lệ.")
    compare = body.get("compare", False)
    if not isinstance(compare, bool):
        raise ValueError("Tùy chọn so sánh không hợp lệ.")
    if group and strategy != "C" and not compare:
        raise ValueError("Chỉ cấu hình C sử dụng bộ lọc nhóm nội dung.")
    return question.strip(), strategy, group, compare


class RetrievalApp:
    def __init__(self):
        from .embeddings import MyEmbedder
        from .store import QdrantStore

        self.config = json.loads((ROOT / "configs/experiment.json").read_text(encoding="utf-8"))
        self.embedder = MyEmbedder(self.config["model"], ROOT / ".cache/models")
        self.store = QdrantStore(ROOT / ".local/qdrant", self.embedder.dimensions)
        try:
            self.counts = {s: self.store.count(s) for s in "ABC"}
            if any(n == 0 for n in self.counts.values()):
                raise RuntimeError("Index rỗng. Chạy pipeline trước khi mở giao diện.")
        except Exception:
            self.store.close()
            raise

    def status(self):
        return {"ready": True, "model": self.config["model"], "dimensions": 384,
                "store": "Qdrant local", "counts": self.counts, "groups": GROUPS,
                "source_available": (ROOT / "data/raw/tai_lieu.pdf").is_file()}

    def search(self, body):
        question, strategy, group, compare = validate_search(body)
        started = time.perf_counter()
        vector = self.embedder.embed_query(question)
        results = []
        for selected in "ABC" if compare else [strategy]:
            filters = {"content_group": group} if selected == "C" and group else {}
            hits = self.store.search(selected, vector, top_k=3, filters=filters)
            if any(not math.isfinite(h["score"]) for h in hits):
                raise RuntimeError("Điểm truy xuất không hợp lệ.")
            results.append({"strategy": selected, "filter": filters, "hits": hits})
        return {"question": question, "results": results,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 1)}

    def close(self):
        self.store.close()


def handler_for(app):
    class Handler(BaseHTTPRequestHandler):
        def send_bytes(self, status, data, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "same-origin")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def send_json(self, status, value):
            self.send_bytes(status, json.dumps(value, ensure_ascii=False).encode("utf-8"),
                            "application/json; charset=utf-8")

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/api/status":
                self.send_json(200, app.status())
                return
            assets = {"/": (WEB / "index.html", "text/html; charset=utf-8"),
                      "/app.js": (WEB / "app.js", "text/javascript; charset=utf-8"),
                      "/style.css": (WEB / "style.css", "text/css; charset=utf-8"),
                      "/source.pdf": (ROOT / "data/raw/tai_lieu.pdf", "application/pdf")}
            if path not in assets:
                self.send_json(404, {"error": "Không tìm thấy trang."})
                return
            file, content_type = assets[path]
            if not file.is_file():
                self.send_json(404, {"error": "Không tìm thấy file nguồn."})
                return
            self.send_bytes(200, file.read_bytes(), content_type)

        def do_POST(self):
            if urlsplit(self.path).path != "/api/search":
                self.send_json(404, {"error": "Không tìm thấy chức năng."})
                return
            # Accept only same-origin browser requests to the loopback service.
            origin = self.headers.get("Origin")
            if origin and origin != f"http://{self.headers.get('Host')}":
                self.send_json(403, {"error": "Nguồn yêu cầu không hợp lệ."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16384:
                    raise ValueError("Yêu cầu quá lớn hoặc thiếu nội dung.")
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(200, app.search(body))
            except (ValueError, UnicodeDecodeError) as exc:
                self.send_json(400, {"error": str(exc)})
            except Exception:
                logging.exception("UI retrieval failed")
                self.send_json(500, {"error": "Truy xuất thất bại. Xem lỗi trong terminal và thử lại."})

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--open", action="store_true", help="Open default browser")
    parser.add_argument("--allow-download", action="store_true", help="Allow model download if cache is missing")
    args = parser.parse_args()
    if not args.allow_download:
        os.environ["HF_HUB_OFFLINE"] = "1"
    logging.basicConfig(level=logging.INFO)
    print("Loading model and existing Qdrant index...", flush=True)
    try:
        app = RetrievalApp()
    except Exception as exc:
        raise SystemExit(f"Cannot open index/model: {exc}\nRun pipeline first; close another UI/pipeline using this database.") from exc
    try:
        with HTTPServer(("127.0.0.1", args.port), handler_for(app)) as server:
            url = f"http://127.0.0.1:{server.server_port}"
            print(f"Local UI: {url}\nPress Ctrl+C to stop before running the ingestion pipeline.", flush=True)
            if args.open:
                webbrowser.open(url)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
    finally:
        app.close()


if __name__ == "__main__":
    main()
