# Retrieval Evaluation Report

Ngay test: 2026-09-04

## Muc tieu

Danh gia do chinh xac cua buoc retrieval trong he thong RAG Luat Giao Thong Viet Nam.
Bo test hien co gom 41 cau hoi pho bien, phu nhieu nhom phuong tien va hanh vi vi pham.

## Cac nhom cau hoi

- Xe may
- O to
- Nguoi di bo
- Xe dap
- Xe may chuyen dung / may keo
- Mot so cau hoi tong quat hoac de gay nhieu

## Chu de test

- Nong do con
- Vuot den do / khong chap hanh den tin hieu
- Qua toc do
- Khong doi mu bao hiem
- Sai lan
- Khong co giay phep lai xe
- Khong chap hanh bien bao
- Di vao duong cao toc
- Dung xe trong ham duong bo
- Khong that day an toan

## Metric

- Recall@1: can cu dung nam o vi tri top 1.
- Recall@3: can cu dung nam trong top 3.
- MRR: Mean Reciprocal Rank, can cu dung cang dung cao thi diem cang cao.

## Ket qua hien tai

```text
Cases: 41
Recall@1: 1.00
Recall@3: 1.00
MRR: 1.00
```

Trong bo test hien tai, 41/41 cau truy xuat dung can cu o top 1; 41/41 cau co can cu dung trong top 3.

## Cong thuc hybrid hien tai

He thong dang dung hybrid retrieval voi RRF fusion:

```text
rrf_score = 1 / (60 + dense_rank) + 1 / (60 + sparse_rank)
final_score = rrf_score + 0.02 * metadata_boost
```

Trong do:

- dense_rank den tu Chroma vector search.
- sparse_rank den tu BM25 keyword search.
- metadata_boost giup uu tien dung nhom phuong tien va dung dieu xu phat.

RRF khong cong truc tiep dense_score va sparse_score, ma cong theo thu hang. Cach nay on dinh hon khi diem cua 2 he thong search khac scale nhau.

## Cach chay lai

```powershell
cd D:\rag_giaothong
.\.venv\Scripts\Activate.ps1
$env:PYTHONIOENCODING="utf-8"
python scripts\run_retrieval_eval.py
```

## Luu y

Day la evaluation cho retrieval, chua phai danh gia toan bo cau tra loi cua LLM. De danh gia end-to-end can them bo test cho answer, gom cac tieu chi: dung can cu, khong bia luat, tra loi du muc phat, va citation chinh xac.
