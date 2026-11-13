"""Materialize explicitly AI-assisted qualitative review, never human labels."""
import csv
import json
import statistics
from .prepare import ROOT, save_json, save_jsonl

# Authored by Codex after reading the sampled chunks and retrieved evidence.
# These are judgment labels, NOT inferred from substring-match metrics.
COHERENCE = {
    "A": [
        (1, "Bắt đầu giữa từ; định nghĩa sơ chế ở cuối bị cắt, nhưng phần giữa còn hiểu được."),
        (1, "Đầu và cuối giữa ý; các ví dụ tác nhân vật lý vẫn đọc hiểu được."),
        (1, "Đầu giữa từ và cuối thiếu phần nguồn gốc; đoạn kiểm soát độc tố còn trọn ý."),
        (1, "Mở đầu thiếu ngữ cảnh, cuối bị cắt giữa từ; mô tả ở giữa hiểu một phần."),
        (1, "Mất đầu từ Thớt; ý khám sức khỏe ở cuối bị cắt."),
        (1, "Đầu nối từ trang trước và cuối cắt mục chất độc; phần bảo quản còn hiểu được."),
        (1, "Mở đầu giữa từ và kết thúc giữa ví dụ; phần yêu cầu sơ chế còn hiểu được."),
        (1, "Mở đầu thiếu đối tượng và cuối cắt tên Tỏi tây; các mục cần tây/cần ta còn rõ."),
        (1, "Mở đầu giữa câu và cuối cắt quy trình su su; các mục mướp còn hiểu được."),
        (1, "Đầu giữa từ, cuối cắt mục củ cải; mục cà rốt ở giữa có thông tin hữu ích.")
    ],
    "B": [
        (2, "Mục tiêu và lý do cần sơ chế có chủ thể và kết thúc câu đầy đủ."),
        (1, "Các mục hóa học đủ câu nhưng mở đầu tiếp danh sách tác nhân, thiếu tiêu đề bao quát."),
        (2, "Các ví dụ và đoạn yêu cầu kiểm soát độc tố giữ được ý, không cắt câu kết."),
        (2, "Các trường hợp bệnh và chuyển sang nguyên liệu thực vật có chủ thể, câu trọn vẹn."),
        (2, "Hai mục thớt và bố trí khu sơ chế có chủ thể, hành động và lý do đầy đủ."),
        (2, "Các lưu ý bảo quản/sơ chế có câu hoàn chỉnh; mục Solamin là ví dụ riêng."),
        (2, "Tiêu đề yêu cầu kỹ thuật và ví dụ mổ gà đi cùng nhau, kết thúc đủ câu."),
        (1, "Đủ ý về cần tây nhưng mở đầu giữa mô tả rau diếp, kết mục cần ta thiếu ứng dụng."),
        (1, "Mở đầu Lựa chọn quả bánh tẻ không nêu tên loại mướp; các mục sau còn hiểu được."),
        (1, "Mở đầu giữa mô tả cà chua và gộp nhiều mục; mục cà rốt giữ ý nhưng ngữ cảnh chưa trọn.")
    ]
}
GROUNDING = {
    "A": {
        "q16": (0, "Top-3 nói về nước mắm, hấp đồ và vệ sinh thớt; không có cách ngâm ốc trang 25."),
        "q17": (0, "Top-3 có mùi tây và rau sơ chế, không có bằng chứng sử dụng cỏ xạ hương trang 40."),
        "q18": (0, "Các đoạn là tan băng và chế biến nóng ướt chung, không chứng minh mức sôi nhẹ của ninh hầm."),
        "q19": (2, "Hit thứ 2 trang 67 có đủ quy tắc đĩa tròn qua tâm và bầu dục/chữ nhật qua trục."),
        "q20": (2, "Hit thứ 3 trang 70 nêu rõ trình bày đơn giản, nhanh để giữ nóng và phục vụ kịp.")
    },
    "B": {
        "q16": (0, "Top-3 về vây/bóng cá, nước mắm và vệ sinh khu sơ chế; không có bằng chứng ngâm ốc."),
        "q17": (0, "Top-3 là rau cải, mùi tây và rau sơ chế; không có mục cỏ xạ hương."),
        "q18": (0, "Top-3 là nhiệt khô, tan băng và quay nướng; thiếu bằng chứng đúng phương pháp ninh hầm."),
        "q19": (2, "Hit thứ 2 trang 67 giữ trọn mục trang trí đối xứng và cả hai quy tắc chọn đĩa."),
        "q20": (1, "Có ý thời gian trình bày nóng ướt rất ít (trang 70) và phục vụ đúng giờ (66), thiếu chỉ dẫn nhanh để giữ nóng.")
    },
    "C": {
        "q16": (0, "Không có filter cho câu này, kết quả như B; không có bằng chứng về ngâm ốc."),
        "q17": (0, "Filter giữ đúng nhóm gia vị nhưng trả về mùi tây/hương thảo và gia vị khác, không có cỏ xạ hương."),
        "q18": (0, "Không có filter cho câu này, kết quả như B; không có bằng chứng sôi nhẹ của ninh hầm."),
        "q19": (2, "Hit thứ 2 trang 67 có cả hai quy tắc chọn đĩa, đủ trả lời và truy nguồn."),
        "q20": (1, "Như B: có thông tin liên quan về thời gian, thiếu ý trình bày nhanh để giữ độ nóng.")
    }
}

def main():
    read = lambda name: [json.loads(s) for s in (ROOT / name).read_text(encoding="utf-8").splitlines()]
    samples = read("results/coherence_samples.jsonl")
    coherence = []
    for sample in samples:
        strategy, page = sample["strategy"], sample["page"]
        score, reason = COHERENCE["B" if strategy == "C" else strategy][page - 9]
        coherence.append({"strategy": strategy, "page": page, "anchor": sample["anchor"],
            "chunk_id": sample["chunk"]["chunk_id"], "ai_score": score, "reason": reason,
            "reviewer": "Codex AI-assisted inspection", "human_confirmed": False})
    save_jsonl(ROOT / "results/coherence_ai_review.jsonl", coherence)
    traces = read("results/test_audit_samples.jsonl")
    pages = {p["page"]: p for p in read("data/normalized/content_pages.jsonl")}
    grounding, metadata = [], []
    for trace in traces:
        s, q = trace["strategy"], trace["question"]
        score, reason = GROUNDING[s][q["id"]]
        grounding.append({"strategy": s, "question_id": q["id"], "ai_score": score,
                          "reason": reason, "reviewer": "Codex AI-assisted inspection",
                          "human_confirmed": False})
        for rank, hit in enumerate(trace["hits"], 1):
            source = pages[hit["page"]]
            correct = (hit["document_id"] == source["document_id"]
                       and hit["source"] == source["source"]
                       and hit["metadata"]["content_group"] == source["metadata"]["content_group"]
                       and source["text"][hit["metadata"]["start_char"]:hit["metadata"]["end_char"]] == hit["text"])
            obeys = all(hit["metadata"].get(k) == v for k,v in q["filter"].items()) if q["filter"] else None
            metadata.append({"strategy": s, "question_id": q["id"], "rank": rank,
                "chunk_id": hit["chunk_id"], "page": hit["page"], "source": hit["source"],
                "content_group": hit["metadata"]["content_group"],
                "complete_and_correct_against_extracted_source": correct,
                "requested_filter_obeyed": obeys,
                "method": "Programmatic source/offset check plus AI inspection; no independent human validation",
                "human_confirmed": False})
    save_jsonl(ROOT / "results/grounding_ai_review.jsonl", grounding)
    save_jsonl(ROOT / "results/metadata_audit.jsonl", metadata)
    summaries = []
    for s in "ABC":
        co = [x for x in coherence if x["strategy"] == s]
        gr = [x for x in grounding if x["strategy"] == s]
        me = [x for x in metadata if x["strategy"] == s]
        fq = [t for t in traces if t["strategy"] == s and t["question"]["filter"]]
        obey = sum(all(all(h["metadata"].get(k) == v for k,v in t["question"]["filter"].items())
                        for h in t["hits"]) for t in fq)
        summaries.append({"strategy": s, "coherence_ai_mean": statistics.mean(x["ai_score"] for x in co),
            "coherence_n": len(co), "grounding_ai_mean": statistics.mean(x["ai_score"] for x in gr),
            "grounding_distribution": {str(i): sum(x["ai_score"] == i for x in gr) for i in range(3)},
            "metadata_correct_n": sum(x["complete_and_correct_against_extracted_source"] for x in me),
            "metadata_n": len(me), "filter_questions_obeyed": obey, "filter_questions_n": len(fq),
            "human_review_status": "PENDING; AI scores are provisional"})
    save_json(ROOT / "results/audit_summary.json", summaries)
    review_path = ROOT / "results/human_review.csv"
    if review_path.exists():
        review_path = ROOT / "results/human_review_template.csv"
    with review_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dimension","strategy","sample_id","ai_score","human_score","reviewer","reason"])
        writer.writeheader()
        for dimension, rows in (("coherence", coherence), ("grounding", grounding)):
            for row in rows:
                writer.writerow({"dimension": dimension, "strategy": row["strategy"],
                    "sample_id": row.get("question_id", f"page_{row.get('page')}"),
                    "ai_score": row["ai_score"], "human_score": "", "reviewer": "", "reason": row["reason"]})
    print("Saved AI-assisted review, metadata checks, and blank human confirmation sheet")

if __name__ == "__main__":
    main()
