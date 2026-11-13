"""Prepare source records, manifest, and immutable benchmark inputs."""
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from .ingestion import load_pdf
from .evaluation import canonical

ROOT = Path(__file__).resolve().parents[2]
DOC = "giao_trinh_che_bien_2019"

def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

def save_jsonl(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for value in values:
            f.write(json.dumps(value, ensure_ascii=False) + "\n")

def prepare_pages():
    pdf = ROOT / "data/raw/tai_lieu.pdf"
    rules = json.loads((ROOT / "data/content_rules.json").read_text(encoding="utf-8"))
    pages = load_pdf(pdf, DOC, "data/raw/tai_lieu.pdf")
    selected, excluded = [], []
    for page in pages:
        # Strip only a leading line exactly equal to the physical page number.
        lines = page.text.splitlines()
        if lines and lines[0].strip() == str(page.page):
            page.text = "\n".join(lines[1:]).strip()
        groups = [g for g in rules["groups"]
                  if g["start_page"] <= page.page <= g["end_page"]]
        if len(groups) > 1:
            raise ValueError(f"Overlapping rules: {page.page}")
        page.metadata.update({"char_count": len(page.text), "language": "vi"})
        if not groups:
            excluded.append({"page": page.page, "char_count": len(page.text),
                             "reason": "front_matter" if page.page <= 8 else "no_useful_content"})
            continue
        if not page.text:
            raise ValueError(f"Selected empty page: {page.page}")
        page.metadata["content_group"] = groups[0]["content_group"]
        selected.append(page)
    expected = {p for g in rules["groups"] for p in range(g["start_page"], g["end_page"] + 1)}
    if {p.page for p in selected} != expected or len(selected) != len(expected):
        raise ValueError("Missing/duplicate source pages")
    if len(selected) < 30:
        raise ValueError("Need at least 30 content pages")
    save_jsonl(ROOT / "data/normalized/content_pages.jsonl", [asdict(p) for p in selected])
    save_json(ROOT / "results/source_quality.json", {
        "physical_pages": len(pages), "selected_pages": len(selected), "excluded": excluded,
        "known_issues": ["PDF extraction splits Vietnamese words; no speculative spelling repair",
                         "Page breaks can interrupt sentences; chunks remain page-bounded",
                         "Line wraps are preserved; paragraph/sentence splitting is heuristic"]})
    save_json(ROOT / "data/manifest.json", {
        "source_id": DOC, "title": "Giáo trình Kỹ thuật chế biến món ăn - trình độ sơ cấp",
        "institution_on_cover": "Trường Cao đẳng nghề Kỹ thuật Công nghệ",
        "source_path_or_url": "data/raw/tai_lieu.pdf", "original_url": None,
        "source_provenance": "PDF supplied by student; original download URL not available",
        "license_or_permission": "No standard open license identified. Page 2 permits educational/reference use; public redistribution not established.",
        "permission_evidence_page": 2, "accessed_at": "2026-11-13",
        "access_date_basis": "student source_notes.md",
        "snapshot_year_on_cover": 2019, "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "physical_page_count": len(pages), "content_page_count": len(selected),
        "counting_rule": "Physical PDF pages 9-70 inclusive; exclude front matter 1-8 and page-number-only page 71; no 1500-character threshold for PDF pages.",
        "pages": [{"page": p.page, "characters": len(p.text),
                   "content_group": p.metadata["content_group"]} for p in selected],
        "metadata_schema": {"document_id": "stable string", "source": "local relative PDF path",
                            "page": "1-based physical PDF page", "language": "vi, observed",
                            "content_group": "string, editorial grouping from observed lesson ranges"},
        "grouping_note": "Page 9 includes introductory lesson and lesson 1, grouped together; retain original numbering (no invented lesson 2).",
        "sharing": "Raw PDF, extracted corpus, vectors, and text-bearing traces excluded from Git by default. Obtain the same PDF legitimately and verify SHA256 to reproduce."
    })
    return selected

# Authored before retrieval. Each evidence span is extracted using these checked
# source anchors, rather than invented text. No gold information enters queries.
SPECS = [
("dev",9,"Sơ chế nguyên liệu là gì và chuẩn bị cho khâu nào?",
 "Loại bỏ phần không ăn được và làm sạch chất độc hại, chuẩn bị cho các khâu chế biến tiếp theo.",
 "Sơ chế nguyên liệu là quá trình","biến tiếp theo.",False),
("dev",10,"Giáo trình liệt kê những tác nhân sinh học nào làm giảm chất lượng thực phẩm?",
 "Côn trùng, ký sinh trùng, vi khuẩn, virus và nấm mốc.",
 "- Tác nhân sinh học:","nấm mốc.",False),
("dev",15,"Theo phần sơ chế, thịt gà dùng để tần, quay, luộc được mổ theo cách nào?",
 "Mổ moi.",
 "Ví dụ: Thịt gà","mổ lưng.",True),
("dev",20,"Đối với nấm nuôi, tiêu chí lựa chọn và các bước sơ chế cơ bản là gì?",
 "Chọn nấm bóng, không dập nát, đều kích thước; cắt chân, rửa, bổ theo yêu cầu.",
 "+ Nấm nuôi:","yêu cầu chế biến.",False),
("dev",31,"Nguyên liệu chính và nguyên liệu phụ khác nhau như thế nào về khả năng thay thế?",
 "Nguyên liệu chính không thể thay thế; nguyên liệu phụ có thể thay thế.",
 "- Nguyên liệu chính:","Nguyên liệu phụ có thể thay thế được.",False),
("dev",32,"Việc phối hợp nguyên liệu được tiến hành ở giai đoạn nào so với chế biến?",
 "Trước, trong và sau khi chế biến.",
 "Phối hợp nguyên liệu không phải","trước, trong và sau khi chế biến",False),
("dev",35,"Trong phần phối hợp nguyên liệu, nguyên liệu lâu chín và nhanh chín được cho vào theo thứ tự nào?",
 "Lâu chín cho trước, nhanh chín cho sau.",
 "- Khi chế biến nhiệt,","nhanh chín cho vào sau.",True),
("dev",41,"Tác dụng quan trọng nhất của gia vị được nêu ở mục 2.2.1 là gì?",
 "Làm tăng mùi, vị, màu sắc của món ăn.",
 "2.2.1. Làm tăng","thể hiện rõ nhất của gia vị.",False),
("dev",43,"Các phương pháp chế biến bằng hơi nước được liệt kê gồm những gì?",
 "Hấp, đồ, tráng, tần.",
 "- Chế biến bằng hơi nước:","Hấp, đồ, tráng, tần.",False),
("dev",52,"Rán ngập chất béo được định nghĩa như thế nào?",
 "Chế biến bằng dầu mỡ, thực phẩm ngập hoàn toàn trong dầu mỡ khi làm chín.",
 "Khái niệm: Rán ng","trong dầu mỡ",False),
("dev",57,"Vì sao giáo trình khuyên dùng chảo sâu đáy thay vì chảo đáy bằng khi xào?",
 "Hạn chế nước tiết ra ngấm trở lại nguyên liệu; nước đọng đáy ít tiếp xúc nguyên liệu.",
 "Dụng cụ để xào","không tiếp súc nhiều với nguyên liệu.",False),
("dev",61,"Phương pháp trộn có dùng nhiệt trực tiếp không và nguyên liệu được phối hợp ra sao?",
 "Không dùng nhiệt ở bước trộn; thực phẩm, gia vị đã cắt thái hoặc chế biến nhiệt sơ bộ được trộn theo công thức và quy trình.",
 "Phương pháp trộn là phương pháp","công thức và quy trình nhất định",False),
("dev",62,"Theo phần phương pháp trộn, những đối tượng nào không nên ăn các món trộn?",
 "Người có bộ máy tiêu hóa kém.",
 "- Chỉ phù hợp","không nên ăn các món trộn",False),
("dev",65,"Trình bày món ăn có những mục đích nào về cảm quan và thương mại?",
 "Tạo thẩm mỹ, tăng giá trị cảm quan, kích thích ngon miệng và tăng giá trị thương mại.",
 "- Tạo tính thẩm mỹ","giá trị thương mại cho món ăn",False),
("dev",66,"Trình bày món ăn phải phù hợp với dụng cụ chứa đựng ở những đặc điểm nào?",
 "Kiểu dáng, màu sắc, chất liệu và phong cách văn hóa của dụng cụ.",
 "2.3. Trình bày món ăn","- Phù hợp với phong cách văn hóa của dụng cụ",False),
("test",25,"Trước khi sơ chế ốc cần ngâm trong những loại nước nào và để làm gì?",
 "Nước lạnh hoặc nước vo gạo để ốc nhả hết bẩn và nhớt.",
 "Ốc trước khi sơ chế","hết bẩn và nhớt.",False),
("test",40,"Trong phần gia vị, cỏ xạ hương được sử dụng cho những nhóm món nào?",
 "Nước dùng, món có mùi hôi và món có thời gian chế biến nhiệt dài.",
 "- Cỏ xạ hương (thyme)","+ Đi cùng các loại ga vị: lá nguyệt quế, nhục đậu khấu…",True),
("test",47,"Theo mục ninh hầm, cần duy trì nhiệt độ ở mức nào?",
 "Duy trì ở nhiệt độ sôi nhẹ.",
 "Môi trường: lượng nước đủ","Nhiệt độ: duy trì ở nhiệt độ sôi nhẹ.",False),
("test",67,"Trang trí đối xứng qua tâm và qua trục nên dùng những dạng đĩa nào?",
 "Qua tâm dùng đĩa tròn; qua trục dùng đĩa bầu dục hoặc chữ nhật.",
 "+ Trang trí đối xứng qua tâm nên dùng đĩa tròn","+ Trang trí đối xứng qua trục nên dùng đĩa bầu dục hay chữ nhật.",False),
("test",70,"Với các món nóng ướt, cách trình bày cần như thế nào để kịp phục vụ?",
 "Đơn giản, nhanh để giữ độ nóng và kịp thời phục vụ khách.",
 "- Các món nóng, ướt:","và kịp thời phục vụ khách.",False),
]

def build_benchmark(pages):
    path = ROOT / "benchmark/questions.jsonl"
    # Never silently rewrite an existing benchmark after results exist.
    if path.exists():
        questions = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    else:
        by_page = {p.page: p for p in pages}
        questions = []
        for i, (split, number, query, answer, first, last, filtered) in enumerate(SPECS, 1):
            page = by_page[number]
            start = page.text.index(first)
            end = page.text.index(last, start) + len(last)
            questions.append({
                "id": f"q{i:02}", "split": split, "question": query,
                "expected_answer": answer, "gold_source_id": DOC,
                "gold_page": number, "evidence_quote": page.text[start:end],
                "filter": {"content_group": page.metadata["content_group"]} if filtered else {},
                "filter_basis": "Question explicitly scopes the lesson group" if filtered else None,
                "evidence_verified_against": "normalized PDF extraction",
            })
        save_jsonl(path, questions)
    by_page = {p.page: p for p in pages}
    for q in questions:
        if canonical(q["evidence_quote"]) not in canonical(by_page[q["gold_page"]].text):
            raise ValueError(f"Invalid evidence: {q['id']}")
        if q["filter"] and any(by_page[q["gold_page"]].metadata[k] != v
                               for k, v in q["filter"].items()):
            raise ValueError(f"Invalid filter: {q['id']}")
    counts = {s: sum(q["split"] == s for q in questions) for s in ("dev", "test")}
    if counts["dev"] < 15 or counts["test"] < 5 or sum(bool(q["filter"]) for q in questions) < 3:
        raise ValueError("Benchmark too small")
    if not any(q["split"] == "test" and q["filter"] for q in questions):
        raise ValueError("Missing test filter")
    return questions
