# Môi trường và lỗi setup thực tế

- Python có sẵn: 3.14, môi trường .venv của học viên.
- Pip trong sandbox ban đầu bị chặn mạng (WinError 10013); cài dependency qua quyền network được cấp cho thao tác setup.
- Docker không truy cập được named pipe trong sandbox. Chọn Qdrant local được đề cho phép; không cần Docker.
- Model intfloat/multilingual-e5-small không có trong danh sách FastEmbed đang cài. Chưa chạy retrieval/model đó; chọn paraphrase-multilingual-MiniLM-L12-v2 trước khi khóa benchmark.
- grpcio 1.85.1 bị Windows Application Control chặn DLL. Cài grpcio 1.76.0 tương thích đã import thành công; không thay đổi chính sách Windows.
- FastEmbed tải model thật ONNX từ Hugging Face; có cảnh báo Windows không tạo symlink, dùng cache file thường.
- Chạy benchmark với HF_HUB_OFFLINE=1 sau khi cache đủ model.
- Qdrant local thông báo SearchParams exact không có tác dụng vì local vốn đã tìm kiếm exact. Được ghi nhận, không phải fallback.
- Không dùng API trả phí, không dùng vector giả cho pipeline.
