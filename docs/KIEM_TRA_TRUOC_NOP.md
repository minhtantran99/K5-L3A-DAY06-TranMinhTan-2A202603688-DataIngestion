# Kiểm tra trước khi nộp

## Đã có bằng chứng

- 62 trang nội dung PDF (9–70), manifest có hash, số ký tự, nguồn nhận và ghi nhận quyền sử dụng.
- Pipeline Python: đọc, chuẩn hóa, chia chunk, embedding thật, Qdrant local lưu bền vững và metadata filter.
- Ba cấu hình A/B/C, cùng model/corpus/benchmark; B–C chỉ thay filter.
- 20 câu hỏi có gold/evidence, 15 dev / 5 test, 3 câu filter gồm 1 câu test; input đã khóa trước chạy.
- 60 trace truy xuất, tổng 180 kết quả; chỉ số dev/test, thời gian, chi phí API và kết quả kiểm tra nạp lại.
- Báo cáo đủ năm khía cạnh, ví dụ lỗi và giới hạn; sáu kiểm thử kỹ thuật đạt.
- Giao diện local để demo; slide chi tiết 14 trang, PDF và lời thuyết trình.

## Chưa hoàn tất theo checklist đề

1. **Chấm thủ công:** `results/human_review.csv` vẫn chưa có `human_score`/`reviewer`. Có 30 mẫu coherence và 15 mẫu grounding. Nhận xét hiện tại do AI hỗ trợ; không được đổi nhãn thành đã được học viên xác nhận khi chưa làm. Metadata có 45 bản ghi đối chiếu tự động, còn chờ người học kiểm chứng với nguồn. Sau khi xác nhận, cập nhật báo cáo tương ứng, giữ phân biệt điểm AI và điểm người chấm.
2. **Nộp repo:** repo đích là `https://github.com/minhtantran99/K5-L3-Day06-DataIngestionEngineering`, nhánh `tan_branch`; commit triển khai ghi trong STUDENT.md. Học viên tự nộp link theo kênh lớp. Chỉ dùng tài khoản `minhtantran99`.
3. **Cấp quyền xem bằng chứng:** PDF, corpus và trace có text vẫn bị bỏ qua trong Git vì chưa xác minh quyền đăng công khai. Bản ZIP local có các file này để chấm riêng. Cần cung cấp cho người chấm qua kênh phù hợp hoặc hướng dẫn truy cập hợp lệ; chưa có URL tải gốc để tự động lấy lại PDF.

Không yêu cầu bổ sung lớp theo chỉ dẫn của học viên. Điểm test thấp không phải lý do phải chạy lại hoặc tinh chỉnh trước nộp; rubric đánh giá bằng chứng và phân tích trung thực.

## Các file phụ đã loại khỏi Git và bản ZIP

- Ảnh xem trước slide và contact sheet.
- Bản PowerPoint một slide cũ đã được thay bằng bộ 14 slide.
- File tạm/khóa PowerPoint có tên bắt đầu `~$`.
- Các script khảo sát ban đầu; code pipeline chính vẫn giữ nguyên.

Cache model, vector database, môi trường ảo và secret tiếp tục được bỏ qua trong Git. Slide chi tiết, benchmark, báo cáo, nhãn audit, kết quả tổng hợp và log kiểm chứng vẫn được giữ. Không dùng `.gitignore` để che thành phần bắt buộc còn thiếu.
