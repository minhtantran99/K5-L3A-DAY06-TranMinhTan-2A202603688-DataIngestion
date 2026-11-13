# Day 06 — Data Ingestion Engineering

**Trần Minh Tân — MSSV 2A202603688.** Pipeline Python xử lý giáo trình Kỹ thuật chế biến món ăn, tạo embedding đa ngữ thật và truy xuất bằng Qdrant local.

Đã chạy 62 trang nội dung, 3 cấu hình và 20 câu hỏi (15 dev / 5 test). Chọn C trên dev; giữ nguyên lựa chọn khi test thấp hơn A. Báo cáo: [2A202603688_TranMinhTan.md](report/individual/2A202603688_TranMinhTan.md). [Bảng kết quả](results/summary.md). [Giải thích để học DE](docs/QUY_TRINH_DE.md).

**Repo bài nộp:** https://github.com/minhtantran99/K5-L3A-DAY06-TranMinhTan-2A202603688-DataIngestion — nhánh `tan_branch`, commit triển khai được ghi trong STUDENT.md. Học viên tự nộp link theo kênh lớp.

**Phần chưa xác nhận:** nhãn định tính/evidence do học viên kiểm chứng; URL nguồn/quyền công bố lại PDF. Nhãn AI không được trình bày thành điểm chấm thủ công của học viên. Chỉ dùng tài khoản Git minhtantran99. Không bổ sung lớp theo yêu cầu học viên.

## Giao diện test local

Từ thư mục gốc repo, chạy:

```powershell
.\.venv\Scripts\python.exe -m starter.src.webapp --open
```

Hoặc chạy `.\run_ui.ps1` để mở giao diện trong trình duyệt. Địa chỉ mặc định: **http://127.0.0.1:8080**. Có thể đổi cổng bằng `--port 8081`.

Nhập câu hỏi, chọn A/B/C và bấm **Tìm bằng chứng**. Bộ lọc nhóm chỉ áp dụng cho C; bật **So sánh A/B/C** để xem top-3 của cả ba với cùng câu hỏi. Link trang mở PDF gốc, còn chi tiết truy vết chứa chunk ID và offset. Cosine là độ tương đồng, không phải xác suất đúng. Giao diện không sinh câu trả lời LLM và không thay đổi benchmark.

Giao diện mặc định dùng model đã cache, chạy offline. Nếu chưa tải model, chạy pipeline trước hoặc thêm `--allow-download`. Dừng bằng **Ctrl+C** trước khi chạy pipeline/verify/CLI khác vì Qdrant local chỉ cho một tiến trình mở database. Cấu hình máy chủ chỉ nghe trên 127.0.0.1.

## 1. Môi trường và dữ liệu

Lần chạy thực tế: Windows, Python 3.14.3, CPU. Không cần Docker hoặc API key. Lần đầu cần mạng để tải dependencies và model, dung lượng trống khoảng 1 GB trở lên.

PDF học viên cung cấp nằm ở data/raw/tai_lieu.pdf. Bìa ghi Trường Cao đẳng nghề Kỹ thuật Công nghệ, năm 2019; chưa có URL tải gốc. [Manifest](data/manifest.json) ghi SHA256, provenance/quyền, 62 trang 9–70, số ký tự và metadata. Không thay bằng PDF khác mà giữ kết quả cũ.

Nếu nhận code không kèm PDF: xin file hợp lệ từ người nộp qua kênh chấm bài và đặt đúng đường dẫn, kiểm tra hash:
```powershell
Get-FileHash data/raw/tai_lieu.pdf -Algorithm SHA256
```

Hash mong đợi: `9ad4d991887b9c4fcb73d832ff7b2042402055936f7dbfe42f59e7420d5df751`.

## 2. Cài đặt từ thư mục gốc repo

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

requirements.txt khóa dependency chính; requirements-lock.txt là toàn bộ môi trường đã chạy (ưu tiên Python 3.14 trên Windows để tái lập). Model thật là sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, ONNX quantized, 384 chiều. FastEmbed cache tại .cache/models. Qdrant local lưu bền vững tại .local/qdrant; cosine exact search.

## 3. Chạy pipeline và báo cáo

```powershell
# Chỉ chuẩn bị corpus, kiểm tra gold và khóa input:
.\.venv\Scripts\python.exe -m starter.src.run --prepare-only

# Chạy cả ba cấu hình, chọn bằng dev rồi mới chạy test:
.\.venv\Scripts\python.exe -m starter.src.run

# Xuất các nhận xét AI đã đọc mẫu; không giả làm nhãn người chấm:
.\.venv\Scripts\python.exe -m starter.src.audit

# Sinh bảng và báo cáo từ kết quả thực:
.\.venv\Scripts\python.exe -m starter.src.reporting

# Kiểm tra kỹ thuật và lưu minh chứng:
.\.venv\Scripts\python.exe -m starter.src.verify
```

Để chạy offline sau khi tải model thành công:
```powershell
$env:HF_HUB_OFFLINE='1'
.\.venv\Scripts\python.exe -m starter.src.run
```

Lần đầu chưa có cache thì không bật chế độ offline. Pipeline ghi lỗi và dừng nếu model/backend không hoạt động; không thay bằng mock.

benchmark/lock.json bảo vệ hash PDF, cấu hình, quy tắc trang và câu hỏi. Không sửa hoặc xóa lock để tinh chỉnh dựa trên test; tạo vòng thí nghiệm mới và bộ test phù hợp nếu cần. Lần chạy xác nhận sau sửa lỗi lưu trữ có cùng metrics với lần đầu; không coi đây là một test độc lập mới.

## 4. Demo truy xuất

```powershell
.\.venv\Scripts\python.exe -m starter.src.query "Trang trí đối xứng qua tâm nên dùng đĩa gì?" --strategy C --group trinh_bay
```

Kết quả chứa top-3 text, score, nguồn, trang và metadata; không sinh câu trả lời LLM. Giá trị group hợp lệ: tong_luan_va_so_che, phoi_hop_nguyen_lieu, lam_chin, trinh_bay. Chỉ cung cấp filter từ yêu cầu/ngữ cảnh có trước, không lấy gold để lọc.

## 5. Thiết kế và đánh giá

| Cấu hình | Chunk | Filter |
|---|---|---|
| A | 700 ký tự, overlap 100 | Không |
| B | Gom đoạn/câu, tối đa 700, overlap 0 | Không |
| C | Cùng chunk và vector B | content_group khi câu hỏi có yêu cầu |

A–B so sánh cả công thức chunking; B–C chỉ khác lọc. C tái sử dụng embedding B. Cả ba cùng corpus, model, metric, bộ câu hỏi và định nghĩa hit.

Hit yêu cầu cùng document_id/page và đủ evidence trong một chunk. Không suy ra coherence/grounding từ Hit@3. AI đọc 10 vị trí nguồn/cấu hình và top-3 của 5 test/cấu hình; metadata được kiểm tra đủ 45 bản ghi test. Nhãn này chờ học viên kiểm chứng ở results/human_review.csv và results/metadata_audit.jsonl.

## 6. Artifacts chính

| Đường dẫn | Nội dung |
|---|---|
| data/manifest.json | Nguồn, quyền, hash, trang, schema |
| data/content_rules.json | Phạm vi nhóm nội dung |
| benchmark/questions.jsonl, lock.json | Câu hỏi/gold/split và dấu khóa trước chạy |
| configs/experiment.json | Tham số và tiêu chí chọn |
| results/traces.jsonl | 60 lượt truy xuất, top-3 đầy đủ |
| results/traces_public.jsonl | 60 trace bỏ toàn văn chunk, dùng xem hạng/score/nguồn trong repo |
| results/selection.json | Lựa chọn bằng dev trước test |
| results/metrics.json, ingestion_stats.json | Chỉ số, tài nguyên, kiểm tra nạp lại |
| results/coherence_samples.jsonl, test_audit_samples.jsonl | Mẫu xem xét có text |
| results/*ai_review.jsonl | Nhãn AI và lý do từng mẫu |
| results/metadata_audit.jsonl | Đối chiếu 45 bản ghi với nguồn trích xuất |
| results/human_review.csv | Cột điểm/người chấm còn để trống |
| results/run_info.json | Phiên bản, hashes model, thời gian/chi phí |
| results/pipeline.log, source_quality.json | Log và lỗi/chất lượng nguồn |
| artifacts/experiment_log.csv | Bảng A/B/C và kết quả |
| results/verification.json, tests.log | Kết quả kiểm chứng kỹ thuật |
| report/individual/2A202603688_TranMinhTan.md | Báo cáo cá nhân |

Qdrant upsert stable ID chống trùng; full refresh xóa điểm trước khi nạp để không giữ chunk cũ. Đã kiểm tra cập nhật hai chunk xuống một, filter và mở lại store. Full refresh chưa atomic, không phải thiết kế production.

## 7. Bài nộp và quyền chia sẻ

File submission_2A202603688_PRIVATE.zip được tạo bằng `python -m starter.src.package_submission`, chứa code, PDF, corpus, benchmark, artifacts và báo cáo; không chứa môi trường ảo/cache model/database hay secret. Đây là bản đóng gói local phục vụ chấm học tập, chưa gửi đi và không mặc định được phép đăng công khai.

.gitignore loại PDF/corpus/database/model và trace có nội dung nguồn khỏi Git để tránh công bố ngoài ý muốn khi chưa xác minh quyền. Các file vẫn tồn tại local và trong bản ZIP riêng cho người chấm. Nếu công bố repo, cung cấp hướng dẫn truy cập nguồn hợp lệ, kiểm tra quyền đối với cả đoạn trích, và báo người chấm cách nhận artifacts bị hạn chế. Chưa có URL gốc nên chưa thể tự tải lại nguồn từ Internet.

Thông tin repo/commit ở STUDENT.md. Bản ZIP chứa PDF và trace đầy đủ để cung cấp riêng cho người chấm; repo giữ trace đã bỏ toàn văn chunk. Học viên tự kiểm chứng nhãn và tự nộp link theo kênh lớp.

## 8. Tài liệu

- [Đề bài README gốc](docs/DE_BAI_GOC.md), [GUIDE](GUIDE.md), [BENCHMARK](BENCHMARK.md), [RUBRIC](RUBRIC.md).
- [Qdrant local mode chính thức](https://github.com/qdrant/qdrant-client).
- [FastEmbed — model và phương thức query/passage](https://qdrant.tech/documentation/embeddings/fastembed/).
- PostgreSQL/pgvector là lựa chọn starter gốc, không dùng trong bản thực nghiệm này. Hướng dẫn cũ được lưu ở docs/STARTER_GOC.md.
