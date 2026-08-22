# Retrieval Evaluation Report

Ngày test: 2026-08-21

## Mục tiêu

Đánh giá độ chính xác của bước retrieval trong hệ thống RAG Luật Giao Thông Việt Nam.

Bộ test gồm 41 câu hỏi phổ biến, phủ các nhóm:

- Xe máy
- Ô tô
- Người đi bộ
- Xe đạp
- Xe máy chuyên dùng / máy kéo
- Một số câu hỏi tổng quát hoặc dễ gây nhiễu

Các chủ đề gồm:

- Nồng độ cồn
- Vượt đèn đỏ / không chấp hành đèn tín hiệu
- Quá tốc độ
- Không đội mũ bảo hiểm
- Sai làn
- Không có giấy phép lái xe
- Không chấp hành biển báo
- Đi vào đường cao tốc
- Dừng xe trong hầm đường bộ
- Không thắt dây an toàn

## Metric

- Recall@1: kết quả đúng nằm ở vị trí top 1.
- Recall@3: kết quả đúng nằm trong top 3.
- MRR: Mean Reciprocal Rank, kết quả đúng càng đứng cao thì điểm càng cao.

## Kết quả

```text
Cases: 41
Recall@1: 0.98
Recall@3: 1.00
MRR: 0.99
```

Trong bộ test hiện tại, 40/41 câu truy xuất đúng căn cứ ở top 1; 41/41 câu có căn cứ đúng trong top 3.

## Một case chưa ở top 1

```text
ô tô không thắt dây an toàn bị phạt bao nhiêu
```

Case này có kết quả đúng ở rank 2. Đây là điểm cần cải thiện thêm bằng reranking hoặc rule boost chuyên biệt.

## Cách chạy lại

```powershell
cd D:ag_giaothong
.\.venv\Scripts\Activate.ps1
$env:PYTHONIOENCODING="utf-8"
python scriptsun_retrieval_eval.py
```

## Lưu ý

Đây là evaluation cho retrieval, chưa phải đánh giá toàn bộ câu trả lời của LLM. Để đánh giá end-to-end cần thêm bộ test cho answer, gồm các tiêu chí: đúng căn cứ, không bịa luật, trả lời đủ mức phạt, và citation chính xác.
