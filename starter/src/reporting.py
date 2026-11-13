"""Generate tables from executed results; preserve review provenance."""
import csv
import json
from .prepare import ROOT

def main():
    read = lambda p: json.loads((ROOT / p).read_text(encoding="utf-8"))
    metrics = read("results/metrics.json")
    stats = {r["strategy"]: r for r in read("results/ingestion_stats.json")}
    audits = read("results/audit_summary.json")
    info = read("results/run_info.json")
    selection = read("results/selection.json")
    manifest = read("data/manifest.json")
    retrieval = ["| Strategy | Split | Hit@1 | Evidence Hit@3 |",
                 "|---|---|---|---|"]
    for r in metrics:
        retrieval.append(f"| {r['strategy']} | {r['split']} | {r['hit1_n']}/{r['n']} ({r['hit1']:.1%}) | {r['hit3_n']}/{r['n']} ({r['hit3']:.1%}) |")
    resources = ["| Strategy | Chunk | Ký tự tổng | Độ dài TB | Embed (s) | Ghi store (s) | API USD |",
                 "|---|---:|---:|---:|---:|---:|---:|"]
    for s, r in stats.items():
        resources.append(f"| {s} | {r['chunks']} | {r['total_characters']} | {r['length_mean']:.1f} | {r['embedding_seconds']:.3f} | {r['storage_seconds']:.3f} | 0 |")
    qualitative = ["| Strategy | Coherence AI /2 (10 mẫu) | Metadata đúng/đủ | Filter top-3 | Grounding AI 0/1/2 | Grounding AI TB /2 |",
                   "|---|---:|---:|---:|---|---:|"]
    for r in audits:
        d = r["grounding_distribution"]
        qualitative.append(f"| {r['strategy']} | {r['coherence_ai_mean']:.1f} | {r['metadata_correct_n']}/{r['metadata_n']} | {r['filter_questions_obeyed']}/{r['filter_questions_n']} | {d['0']}/{d['1']}/{d['2']} | {r['grounding_ai_mean']:.1f} |")
    tables = "\n".join(retrieval) + "\n\n" + "\n".join(resources) + "\n\n" + "\n".join(qualitative)
    (ROOT / "results/summary.md").write_text("# Kết quả thực nghiệm\n\n" + tables +
        "\n\nNhãn định tính do AI xem xét, chưa được học viên chấm thủ công xác nhận. Metadata được đối chiếu với text trích xuất và cấu hình, không phải kiểm chứng trực quan độc lập toàn bộ PDF.\n", encoding="utf-8")
    descriptions = {
        "A": ("fixed", "100", "Baseline; cửa sổ cố định có thể cắt giữa ý"),
        "B": ("paragraph_sentence", "0", "Ranh giới câu/đoạn có thể giữ ý tốt hơn nhưng không overlap"),
        "C": ("paragraph_sentence", "0", "Lọc nhóm nội dung có thể giảm kết quả ngoài phạm vi")}
    with (ROOT / "artifacts/experiment_log.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fields = ["strategy","chunking","chunk_size","overlap","metadata","filter","vectorizer",
                  "hypothesis","dev_hit1","dev_hit3","test_hit1","test_hit3","notes"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for s in "ABC":
            dev = next(r for r in metrics if r["strategy"] == s and r["split"] == "dev")
            test = next(r for r in metrics if r["strategy"] == s and r["split"] == "test")
            chunking, overlap, hypothesis = descriptions[s]
            writer.writerow({"strategy":s,"chunking":chunking,"chunk_size":700,"overlap":overlap,
                "metadata":"document_id;source;page;content_group;language;offsets",
                "filter":"content_group when supplied" if s=="C" else "none",
                "vectorizer":info["config"]["model"],"hypothesis":hypothesis,
                "dev_hit1":dev["hit1"],"dev_hit3":dev["hit3"],"test_hit1":test["hit1"],"test_hit3":test["hit3"],
                "notes":"Descriptive hypothesis written with report; not separately preregistered. C reuses B embeddings."})
    report = f"""# Báo cáo cá nhân — Day 06

- Họ tên: Trần Minh Tân
- MSSV: 2A202603688
- Thời điểm hoàn tất lần chạy hiện tại: {info['completed_at']}.
- Trạng thái: pipeline và benchmark đã chạy thật. Đánh giá định tính dưới đây là AI-assisted, chưa thay thế phần học viên chấm thủ công theo đề.

## 1. Corpus và xử lý

Corpus là giáo trình Kỹ thuật chế biến món ăn, trình độ sơ cấp, Trường Cao đẳng nghề Kỹ thuật Công nghệ, năm 2019 theo bìa PDF. Học viên cung cấp file; chưa có URL tải gốc được xác minh. Không gán giấy phép mở cho tài liệu. Trang 2 đề cập sử dụng đào tạo/tham khảo, chưa xác minh quyền công bố lại toàn bộ PDF.

PDF có 71 trang vật lý. Sử dụng 62 trang nội dung từ 9 đến 70; loại 1–8 là phần đầu tài liệu và trang 71 chỉ có số trang. Đếm theo trang nội dung PDF, không áp ngưỡng 1.500 ký tự của định dạng không phân trang. Manifest ghi SHA256, số ký tự và nhóm của từng trang. SHA256 PDF: {manifest['sha256']}.

Đọc bằng pypdf, chuẩn hóa Unicode NFC, khoảng trắng ngang và xuống dòng. Loại dòng đầu chỉ khi đúng bằng số trang vật lý. Không sửa suy đoán lỗi chữ như “s ạch”, “nguyên li ệu”. Không OCR vì trích xuất được chữ. Có logging lỗi đọc, dừng khi trích xuất thất bại hoặc thiếu trang đã khai báo. Kết quả text trung gian nằm ở data/normalized/content_pages.jsonl.

Mỗi chunk giữ document_id, source, page, content_group, language, start_char/end_char. Nhóm nội dung lấy từ phạm vi bài đã quan sát: 9–30 tổng luận/sơ chế, 31–42 phối hợp, 43–64 làm chín, 65–70 trình bày. Trang 9 chứa cả bài mở đầu và bài 1 nên dùng content_group thay vì khẳng định một section đơn nhất. Giữ nguyên cách đánh số bài 1, 3, 4, 5 trong nguồn.

## 2. Model, vector store và cấu hình

- Python {info['python']}; FastEmbed {info['packages']['fastembed']}; ONNX Runtime {info['packages']['onnxruntime']}; Qdrant client {info['packages']['qdrant-client']}; pypdf {info['packages']['pypdf']}.
- Model thật: {info['config']['model']}, bản ONNX quantized do FastEmbed tải. 384 chiều, CPU 4 threads; không vector mock. Model/file hashes ở results/run_info.json; dependencies khóa ở requirements-lock.txt.
- Dùng passage_embed cho tài liệu và query_embed cho câu hỏi, cùng một model, không tự thêm prefix E5 cho MiniLM.
- Qdrant local lưu tại .local/qdrant, collection day06_A/B/C; cosine similarity, exact search. Đây là local backend chính thức của Qdrant, không phải tự viết SQLite search.
- A: cửa sổ 700 ký tự, overlap 100.
- B: gom theo đoạn/câu, tối đa 700 ký tự, không overlap; đơn vị quá dài tách tại khoảng trắng hoặc giới hạn ký tự.
- C: cùng chunk và vector như B, thêm filter content_group khi được cung cấp trong câu hỏi. Không có filter thì như B.
- A–B thay cả cách chọn ranh giới và overlap; chỉ diễn giải tác động của toàn bộ công thức chunking, không quy kết riêng cho một tham số. B–C chỉ thay filter.
- Giữ corpus, model, câu hỏi, metric và store giống nhau. Không đưa expected_answer, gold_page hoặc gold_source_id vào query/filter.

Nạp lại dùng stable chunk ID và upsert. Refresh toàn corpus xóa điểm cũ qua API Qdrant rồi nạp snapshot mới, nên không giữ chunk lỗi thời sau khi nguồn đổi. Unit test đã kiểm tra trường hợp thay nguồn từ hai chunk xuống một. Refresh này không atomic và không phù hợp cho production cần truy vấn liên tục; mô hình đổi số chiều cần collection/path mới.

## 3. Thiết kế benchmark và khóa thí nghiệm

20 câu hỏi có expected_answer, source/page, evidence và filter khi cần. Evidence được trích đúng text chuẩn hóa và kiểm tra tồn tại trước khi retrieval. Tách 15 dev / 5 test theo trang bằng chứng; cùng tài liệu và chủ đề nên không độc lập ở cấp tài liệu. Ba câu filter là q03, q07 (dev) và q17 (test); ít nhất hai phạm vi có giá trị phân biệt.

benchmark/lock.json ghi hash câu hỏi, cấu hình, quy tắc trang và PDF trước khi chạy model/retrieval. Tiêu chí chọn chốt trước test: ưu tiên dev Hit@3, sau đó dev Hit@1, ít chunk hơn rồi thứ tự A/B/C. Kết quả chọn: **{selection['selected_strategy']}**. results/selection.json được ghi trước vòng chạy test. Giả thuyết diễn giải trong experiment_log được ghi khi lập báo cáo, không tuyên bố đã preregister riêng.

Hit@1/Hit@3 yêu cầu chunk cùng document_id, trang gold và chứa đủ evidence sau khi chuẩn hóa whitespace. Không tính hit chỉ vì cùng trang; không gộp evidence nhiều chunk vào metric bắt buộc. Hỗ trợ alternative gold nếu được kiểm chứng; hiện chưa rà soát độc lập toàn corpus để bảo đảm mọi bằng chứng tương đương đã được liệt kê.

## 4. Kết quả

{tables}

Thời gian embed/ghi store ở bảng là lần chạy hiện tại, không gồm thời gian tải model và không gồm mọi bước pipeline. C tái dùng vector B nên embed bằng 0 là tái sử dụng, không phải model chạy tức thì. Chi phí API bằng 0; không đo điện, phần cứng hoặc băng thông. Chạy cùng CPU tuần tự, không lặp nhiều lần để ước lượng độ biến thiên.

## 5. Đánh giá năm khía cạnh

**Retrieval.** C tốt nhất trên dev (7/15 Hit@3); test chỉ 1/5, thấp hơn A (2/5). Giữ lựa chọn C theo dev, không đổi sang A sau khi xem test. Mỗi câu test tương đương 20 điểm phần trăm nên chưa đủ kết luận tổng quát.

**Coherence.** Chọn trước điểm giữa của 10 trang 9–18; lấy chunk đầu tiên bao phủ điểm đó cho mỗi cấu hình. AI đọc các chunk và ghi nhãn 0–2 kèm lý do. A trung bình 1,0/2; B và C 1,6/2. A thường bắt đầu/kết thúc giữa từ hoặc câu. B giữ ý tốt hơn nhưng vẫn có câu rời chủ thể và lỗi ranh giới do dấu chấm trong đề mục PDF. Mẫu tập trung đầu tài liệu nên chưa đại diện toàn corpus. Đây là nhãn AI, không phải số liệu chấm thủ công đã xác nhận.

**Metadata.** Kiểm tra đủ 5 câu test × top-3 × 3 cấu hình: 45 bản ghi. Source, page, group và offset/text khớp dữ liệu trích xuất, mỗi cấu hình 15/15. Kiểm tra này không chứng minh chất lượng nguồn hoặc quyền sử dụng. Với câu filter q17, A và B có top-3 ngoài nhóm (0/1); C tuân thủ phạm vi (1/1), nhưng vẫn không lấy được đáp án. Source/page giúp truy vết, content_group giúp giới hạn phạm vi; group còn khá rộng và cần được cung cấp đáng tin trước truy xuất.

**Grounding.** AI xem toàn bộ top-3 cho cùng 5 câu test. A: mức 0/1/2 là 3/0/2, trung bình 0,8/2. B và C: 3/1/1, trung bình 0,6/2. q20 ở B/C có thông tin liên quan về thời gian nhưng thiếu đủ chỉ dẫn giữ nóng. Nhãn có lý do từng trường hợp trong grounding_ai_review.jsonl; không suy ra nhãn này từ Hit@3. Grounding chỉ đo bằng chứng truy xuất, không phải độ chính xác câu trả lời LLM. Chưa có học viên/người chấm độc lập xác nhận.

**Tác động chiến lược.** A–B: giảm 3 chunk, giảm ký tự do không overlap, coherence AI tăng; dev Hit@3 tăng nhưng test giảm. B–C: dev Hit@3 tăng 1 câu, filter tuân thủ tốt hơn, test Hit@3 không đổi. Filter không sửa được xếp hạng sai trong cùng nhóm. Không đủ bằng chứng để tuyên bố C tốt nhất cho mọi dữ liệu.

## 6. Ví dụ lỗi và đánh đổi

1. **q16, nguồn trang 25:** hỏi ngâm ốc bằng nước lạnh/nước vo gạo để nhả bẩn và nhớt. A trả trang 36, 49, 13; B/C trả 28, 36, 13. Các đoạn có ngâm/rửa/nước nhưng thuộc đối tượng khác; thiếu đúng bằng chứng. Đây là lỗi truy xuất đối tượng, không phải thiếu metadata.
2. **q17, nguồn trang 40:** hỏi cách dùng cỏ xạ hương. C lọc đúng nhóm gia vị nhưng trả trang 39, 39, 38, là mùi tây/hương thảo và gia vị khác. Tuân thủ filter không bảo đảm tìm đúng thực thể.
3. **q20, nguồn trang 70:** A có đủ evidence ở hạng 3, còn B/C không đưa đoạn hướng dẫn trình bày nhanh giữ nóng vào top-3. B/C có coherence tốt hơn trên mẫu đã chọn nhưng không đồng nghĩa retrieval tốt hơn mọi câu.

Ví dụ thành công q19: cả ba lấy được đủ quy tắc đĩa tròn/bầu dục/chữ nhật ở hạng 2 trang 67; A vẫn có Hit@1 = 0 trên test dù Hit@3 có ích.

## 7. Tái lập, kiểm chứng và giới hạn

Lệnh chạy và truy vấn ở README.md. 6 unit/integration tests kiểm tra normalization, bảo toàn nội dung/offset, stable ID, unit quá dài, evidence đủ/đúng nguồn, filter, nạp lại, stale chunk và persistence. Đã chạy lại sau sửa lỗi xóa collection trên Windows; không thay model/cấu hình/câu hỏi sau test. results/metrics_first_run.json giữ kết quả đầu để đối chiếu, lần chạy xác nhận cho cùng metrics.

Giới hạn: chỉ một tài liệu tiếng Việt; lỗi chữ/đơn vị trong PDF; ranh giới trang cắt câu; model quantized nhỏ; chưa rerank/hybrid; test nhỏ; nhãn do cùng AI viết benchmark và đánh giá nên có thiên lệch; chưa có kiểm chứng trực quan độc lập toàn bộ evidence/metadata; URL gốc và quyền tái phân phối chưa xác minh.

Nếu làm vòng nghiên cứu mới: cải thiện đọc layout và lỗi tách chữ có kiểm chứng, thử hybrid BM25/reranker trên dev, lấy test mới khi cần điều chỉnh và bổ sung người chấm độc lập. Không tinh chỉnh vòng hiện tại bằng test đã xem.

## 8. Công khai hỗ trợ AI và phần học viên cần xác nhận

Codex hỗ trợ viết code, xây câu hỏi/evidence, chạy pipeline, phân tích và soạn báo cáo. Không tự ghi nhãn AI thành chấm tay của Trần Minh Tân. File results/human_review.csv có 30 mẫu coherence và 15 mẫu grounding để học viên đọc nguồn, ghi human_score, reviewer và lý do; metadata_audit.jsonl có 45 bản ghi chờ xác nhận. Giữ cột AI riêng khi bổ sung điểm người chấm.

Trước nộp cần xác nhận nhãn/evidence và cấp cho người chấm PDF hợp lệ khớp hash qua kênh phù hợp. Repo bài nộp: https://github.com/minhtantran99/K5-L3A-DAY06-TranMinhTan-2A202603688-DataIngestion, nhánh tan_branch; commit triển khai ghi trong STUDENT.md. Chỉ dùng tài khoản minhtantran99. Học viên tự nộp link theo kênh lớp. Theo yêu cầu học viên, không bổ sung thông tin lớp.
"""
    path = ROOT / "report/individual/2A202603688_TranMinhTan.md"
    path.write_text(report, encoding="utf-8")
    print("Generated measured tables, experiment log and individual report")

if __name__ == "__main__":
    main()
