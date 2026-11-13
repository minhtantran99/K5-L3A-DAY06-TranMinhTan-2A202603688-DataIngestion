# Pipeline đã hiện thực

Bản bài làm dùng Qdrant local + FastEmbed đa ngữ thay cho PostgreSQL/pgvector. Không cần Docker/API key.

Từ thư mục gốc repo:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m starter.src.run
.\.venv\Scripts\python.exe -m starter.src.audit
.\.venv\Scripts\python.exe -m starter.src.reporting
```

Xem README.md ở root cho setup, dữ liệu, kết quả và phần cần học viên xác nhận. Docker Compose, init.sql, requirements.txt cũ trong starter chỉ phục vụ lựa chọn PostgreSQL ban đầu; bản hiện tại dùng requirements ở root. Hướng dẫn starter ban đầu đã lưu ở docs/STARTER_GOC.md.
