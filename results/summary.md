# Kết quả thực nghiệm

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

Nhãn định tính do AI xem xét, chưa được học viên chấm thủ công xác nhận. Metadata được đối chiếu với text trích xuất và cấu hình, không phải kiểm chứng trực quan độc lập toàn bộ PDF.
