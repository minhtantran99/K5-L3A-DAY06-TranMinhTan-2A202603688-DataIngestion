# Benchmark đã khóa

20 câu có đáp án và evidence trích từ text PDF đã chuẩn hóa, 15 dev / 5 test. Ba câu filter: q03, q07 (dev), q17 (test). Filter được xác định từ phạm vi được nói trong câu hỏi, không lấy gold_page/document_id để lọc.

questions.jsonl và configs/experiment.json được hash trong lock.json trước khi embedding/retrieval. selection.json được ghi sau dev, trước khi chạy test. Không sửa cấu hình dựa trên test; kết quả test thấp được giữ nguyên.

Tách theo trang bằng chứng, không theo tài liệu: dev/test vẫn có cùng chủ đề và tài liệu, nên có nguy cơ tương quan/rò rỉ chủ đề. Tập test 5 câu rất nhỏ. Chưa có người thứ hai kiểm chứng nhãn.

Hit yêu cầu đúng document_id, trang vật lý, và toàn bộ evidence trong một chunk (chuẩn hóa whitespace để so sánh). Có hỗ trợ gold_alternatives nếu được xác minh trước khi khóa. Evidence bị chia qua nhiều chunk không được tính hit chính. Bộ gold hiện ghi các đoạn đã xác minh; chưa rà soát toàn corpus để bảo đảm mọi bằng chứng tương đương đã được liệt kê.

Nhãn định tính ở results là AI-assisted, không phải nhãn thủ công đã được học viên xác nhận. Học viên cần mở nguồn và kiểm tra trước khi nộp.

Các đoạn trích phục vụ đối chiếu giáo dục theo tuyên bố trang 2; giấy phép mở/URL công khai chưa xác minh. Không tự suy ra quyền tái phân phối toàn bộ tài liệu.
