# Đọc lại bài lab theo góc nhìn Data Engineer

## Dữ liệu đi qua đâu?

PDF gốc → pypdf đọc từng trang → chuẩn hóa text → chọn trang và gắn nhóm → chia chunk → model tạo vector → Qdrant lưu vector/metadata → tìm top-3 → đo và xem lỗi.

Mục tiêu của embedding là biểu diễn ý nghĩa văn bản bằng vector. Qdrant so sánh vector câu hỏi và vector tài liệu; model nhỏ vẫn có thể nhầm các đoạn có từ ngữ gần nhau. Vì vậy phải có benchmark thay vì chỉ nhìn một truy vấn có vẻ đúng.

## Các file nên đọc theo thứ tự

1. starter/src/models.py: schema DocumentPage và Chunk.
2. starter/src/ingestion.py: đọc PDF, Unicode và whitespace.
3. data/content_rules.json và starter/src/prepare.py: quy tắc nghiệp vụ, source lineage, kiểm tra thiếu trang, manifest.
4. starter/src/chunking.py: offset, stable ID, hai cách chia.
5. starter/src/embeddings.py: model thật, batch, document/query.
6. starter/src/store.py: lưu bền vững, cosine, filter, upsert và refresh.
7. starter/src/evaluation.py: định nghĩa hit chặt chẽ.
8. starter/src/run.py: điều phối toàn luồng, khóa input, chọn bằng dev, chạy test.
9. tests/test_pipeline.py: kiểm tra các lỗi có thể làm số liệu sai.
10. results và báo cáo cá nhân: đối chiếu kết luận với trace thật.

## Vì sao giữ nhiều lớp dữ liệu?

- data/raw: file nguồn bất biến, để đọc lại khi code thay đổi.
- data/processed: các text khám phá ban đầu do học viên tạo.
- data/normalized: bản ghi đã có schema, normalization và metadata.
- results/chunks_*.jsonl: dữ liệu biến đổi dùng để tạo index.
- .local/qdrant: kho truy vấn, có thể dựng lại từ nguồn và code.

Đó là cách tách dữ liệu nguồn, dữ liệu đã xử lý và dữ liệu phục vụ truy vấn. Bài nhỏ chưa cần Airflow/Spark; vẫn có những nguyên tắc DE cốt lõi.

## Những khái niệm cần giải thích được

**Lineage:** chunk thuộc document_id nào, file nào, trang nào, vị trí ký tự nào? Khi retrieval sai phải lần ngược được về nguồn.

**Idempotency:** upsert lại cùng chunk ID không tạo bản ghi mới. Nếu tài liệu thay đổi thì stable ID của phần thay đổi khác; vì vậy chỉ upsert là chưa đủ, cần loại chunk cũ. Bài dùng full refresh qua API Qdrant.

**Data quality:** đọc được 71 trang không có nghĩa 71 trang hợp lệ. Bìa/mục lục/trang chỉ có số không được tính. Kiểm tra đủ 62 trang đã khai báo trước khi nạp.

**Schema/metadata:** content_group là string do phạm vi bài trong nguồn quyết định. Giá trị nhóm là cách mã hóa phục vụ hệ thống, không phải thông tin được bịa vào nội dung.

**Reproducibility:** cùng PDF hash, cùng benchmark/config hash, model files hash và versions giúp người khác dựng lại. Model cache/database không cần commit vì tái tạo được.

**Observability:** pipeline.log, source_quality.json, thời gian, số chunk và count sau reopen cho biết pipeline đã làm gì. Lỗi provider/trích xuất phải hiện rõ, không âm thầm đổi sang mock.

**Evaluation leakage:** dùng dev để chọn; chốt rồi mới test. Nếu xem test và sửa tham số để tăng điểm thì kết quả đó không còn độc lập. Vòng này giữ kết quả thấp; sửa lỗi lưu trữ được ghi riêng.

## Bài tập tự kiểm tra sau khi nộp

- Tìm q17 trong traces.jsonl: vì sao filter đúng nhưng vẫn thiếu evidence?
- Đối chiếu chunk trang 13 của A và B: vị trí bắt đầu/kết thúc khác thế nào?
- Tại sao C có thời gian embed bằng 0 nhưng vẫn là model thật?
- Tại sao page 71 không rỗng khi mới đọc nhưng vẫn bị loại?
- Nếu refresh bị dừng giữa chừng, người dùng sẽ thấy gì? Thiết kế staging collection + chuyển alias sẽ cải thiện điều gì?

Khi tự trả lời được các câu này bằng code và artifacts, bạn đã hiểu phần DE chính của lab.
