# Báo cáo cá nhân — Day 06

- Họ tên: Trần Minh Tân
- MSSV: 2A202603688
- Thời điểm hoàn tất lần chạy hiện tại: 2026-11-13T18:14:08.502272+07:00.
- Trạng thái: pipeline và benchmark đã chạy thật. Đánh giá định tính dưới đây là AI-assisted, chưa thay thế phần học viên chấm thủ công theo đề.

## 1. Corpus và xử lý

Corpus là giáo trình Kỹ thuật chế biến món ăn, trình độ sơ cấp, Trường Cao đẳng nghề Kỹ thuật Công nghệ, năm 2019 theo bìa PDF. Học viên cung cấp file; chưa có URL tải gốc được xác minh. Không gán giấy phép mở cho tài liệu. Trang 2 đề cập sử dụng đào tạo/tham khảo, chưa xác minh quyền công bố lại toàn bộ PDF.

PDF có 71 trang vật lý. Sử dụng 62 trang nội dung từ 9 đến 70; loại 1–8 là phần đầu tài liệu và trang 71 chỉ có số trang. Đếm theo trang nội dung PDF, không áp ngưỡng 1.500 ký tự của định dạng không phân trang. Manifest ghi SHA256, số ký tự và nhóm của từng trang. SHA256 PDF: 9ad4d991887b9c4fcb73d832ff7b2042402055936f7dbfe42f59e7420d5df751.

Đọc bằng pypdf, chuẩn hóa Unicode NFC, khoảng trắng ngang và xuống dòng. Loại dòng đầu chỉ khi đúng bằng số trang vật lý. Không sửa suy đoán lỗi chữ như “s ạch”, “nguyên li ệu”. Không OCR vì trích xuất được chữ. Có logging lỗi đọc, dừng khi trích xuất thất bại hoặc thiếu trang đã khai báo. Kết quả text trung gian nằm ở data/normalized/content_pages.jsonl.

Mỗi chunk giữ document_id, source, page, content_group, language, start_char/end_char. Nhóm nội dung lấy từ phạm vi bài đã quan sát: 9–30 tổng luận/sơ chế, 31–42 phối hợp, 43–64 làm chín, 65–70 trình bày. Trang 9 chứa cả bài mở đầu và bài 1 nên dùng content_group thay vì khẳng định một section đơn nhất. Giữ nguyên cách đánh số bài 1, 3, 4, 5 trong nguồn.

## 2. Model, vector store và cấu hình

- Python 3.14.3; FastEmbed 0.9.1; ONNX Runtime 1.31.1; Qdrant client 1.20.0; pypdf 6.21.4.
- Model thật: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, bản ONNX quantized do FastEmbed tải. 384 chiều, CPU 4 threads; không vector mock. Model/file hashes ở results/run_info.json; dependencies khóa ở requirements-lock.txt.
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

benchmark/lock.json ghi hash câu hỏi, cấu hình, quy tắc trang và PDF trước khi chạy model/retrieval. Tiêu chí chọn chốt trước test: ưu tiên dev Hit@3, sau đó dev Hit@1, ít chunk hơn rồi thứ tự A/B/C. Kết quả chọn: **C**. results/selection.json được ghi trước vòng chạy test. Giả thuyết diễn giải trong experiment_log được ghi khi lập báo cáo, không tuyên bố đã preregister riêng.

Hit@1/Hit@3 yêu cầu chunk cùng document_id, trang gold và chứa đủ evidence sau khi chuẩn hóa whitespace. Không tính hit chỉ vì cùng trang; không gộp evidence nhiều chunk vào metric bắt buộc. Hỗ trợ alternative gold nếu được kiểm chứng; hiện chưa rà soát độc lập toàn corpus để bảo đảm mọi bằng chứng tương đương đã được liệt kê.

## 4. Kết quả

| Strategy | Split | Hit@1 | Evidence Hit@3 |
|---|---|---|---|
| A | dev | 2/15 (13.3%) | 4/15 (26.7%) |
| A | test | 0/5 (0.0%) | 2/5 (40.0%) |
| B | dev | 4/15 (26.7%) | 6/15 (40.0%) |
| B | test | 0/5 (0.0%) | 1/5 (20.0%) |
| C | dev | 5/15 (33.3%) | 7/15 (46.7%) |
| C | test | 0/5 (0.0%) | 1/5 (20.0%) |

| Strategy | Chunk | Ký tự tổng | Độ dài TB | Embed (s) | Ghi store (s) | API USD |
|---|---:|---:|---:|---:|---:|---:|
| A | 214 | 129729 | 606.2 | 5.412 | 0.809 | 0 |
| B | 211 | 114450 | 542.4 | 5.713 | 0.858 | 0 |
| C | 211 | 114450 | 542.4 | 0.000 | 0.817 | 0 |

| Strategy | Coherence AI /2 (10 mẫu) | Metadata đúng/đủ | Filter top-3 | Grounding AI 0/1/2 | Grounding AI TB /2 |
|---|---:|---:|---:|---|---:|
| A | 1.0 | 15/15 | 0/1 | 3/0/2 | 0.8 |
| B | 1.6 | 15/15 | 0/1 | 3/1/1 | 0.6 |
| C | 1.6 | 15/15 | 1/1 | 3/1/1 | 0.6 |

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
