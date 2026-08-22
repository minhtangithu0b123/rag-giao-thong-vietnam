# Kiến Thức Tổng Quan Project RAG Luật Giao Thông Việt Nam

Tài liệu này dùng để giải thích project cho người chưa từng làm dự án này, đồng thời giúp chuẩn bị trả lời phỏng vấn.

Project này là một chatbot hỏi đáp luật giao thông Việt Nam. Người dùng nhập câu hỏi tự nhiên, hệ thống tìm các đoạn luật liên quan trong dữ liệu đã ingest, sau đó dùng LLM để tạo câu trả lời có trích dẫn văn bản, điều và khoản.

---

## 1. Bài Toán Cần Giải Quyết

### 1.1. Vấn đề

Luật giao thông có nhiều văn bản, điều, khoản, mức phạt và ngoại lệ. Nếu người dùng tự tìm thủ công thì mất thời gian, dễ đọc nhầm hoặc bỏ sót.

Ví dụ người dùng hỏi:

```text
Nồng độ cồn xe máy bị phạt bao nhiêu?
```

Hệ thống cần trả lời dựa trên căn cứ pháp lý thật, không tự đoán.

### 1.2. Mục tiêu project

Project cần làm được các việc sau:

- Nhận câu hỏi tiếng Việt từ người dùng.
- Tìm các đoạn luật liên quan trong dữ liệu.
- Trả lời bằng ngôn ngữ dễ hiểu.
- Kèm nguồn trích dẫn: số hiệu văn bản, điều, khoản.
- Hạn chế hallucination, tức là không bịa luật nếu dữ liệu không đủ căn cứ.
- Hỗ trợ hỏi qua hỏi lại ở mức cơ bản.

---

## 2. RAG Là Gì?

RAG là viết tắt của **Retrieval-Augmented Generation**.

Nói đơn giản:

```text
RAG = Tìm tài liệu liên quan + Dùng LLM viết câu trả lời dựa trên tài liệu đó
```

LLM như GPT có khả năng viết và suy luận tốt, nhưng nếu chỉ hỏi trực tiếp LLM thì có rủi ro:

- LLM có thể không biết dữ liệu mới nhất.
- LLM có thể trả lời sai nhưng nghe rất tự tin.
- LLM không tự có dữ liệu nội bộ của project.
- Với bài toán luật, bịa một mức phạt là rất nguy hiểm.

RAG giải quyết bằng cách đưa tài liệu thật vào context trước khi LLM trả lời.

Pipeline tổng quát:

```text
User Question
      ↓
Retrieve tài liệu liên quan
      ↓
Đưa tài liệu vào prompt
      ↓
LLM trả lời dựa trên context
      ↓
Answer + Citations
```

Trong project này:

```text
Câu hỏi người dùng
      ↓
Query rewriting nếu là câu hỏi nối tiếp
      ↓
Hybrid retrieval: Dense search + BM25 + metadata boost
      ↓
Top chunks luật liên quan
      ↓
LLM tạo câu trả lời
      ↓
Frontend hiển thị answer + citation
```

---

## 3. Dữ Liệu Trong Project

### 3.1. Dữ liệu đầu vào

Dữ liệu là các văn bản pháp luật giao thông đã được tổng hợp dưới dạng JSON.

Mỗi chunk thường có các trường như:

```json
{
  "so_hieu": "168/2024/NĐ-CP",
  "ten_van_ban": "NGHỊ ĐỊNH ...",
  "chuong": "Chương II",
  "dieu": "Điều 7",
  "khoan": "Khoản 8",
  "vehicle_group": "motorbike",
  "text": "Phạt tiền từ ...",
  "citation": "168/2024/NĐ-CP, Điều 7, Khoản 8"
}
```

### 3.2. Chunk là gì?

Chunk là một đoạn nhỏ được tách ra từ tài liệu lớn.

Thay vì đưa nguyên cả văn bản luật rất dài vào LLM, hệ thống chia thành nhiều đoạn nhỏ hơn theo điều/khoản.

Lý do cần chunk:

- LLM có giới hạn context.
- Retrieval chính xác hơn khi tìm trên đoạn nhỏ.
- Citation rõ hơn vì mỗi chunk gắn với điều/khoản.
- Giảm nhiễu khi trả lời.

### 3.3. Metadata là gì?

Metadata là thông tin mô tả chunk, ví dụ:

- Số hiệu văn bản.
- Tên văn bản.
- Điều.
- Khoản.
- Nhóm phương tiện.
- Nguồn URL.

Metadata giúp hệ thống:

- Hiển thị citation.
- Boost kết quả đúng nhóm phương tiện.
- Đánh giá retrieval.
- Lọc hoặc rerank kết quả.

---

## 4. Embedding Và Vector Search

### 4.1. Embedding là gì?

Embedding là cách biểu diễn văn bản thành vector số.

Ví dụ:

```text
"vượt đèn đỏ xe máy" → [0.12, -0.45, 0.88, ...]
```

Các câu có ý nghĩa gần nhau sẽ có vector gần nhau.

Ví dụ:

```text
"vượt đèn đỏ"
"không chấp hành đèn tín hiệu giao thông"
```

Hai câu này khác chữ nhưng gần nghĩa, nên embedding giúp tìm được tài liệu liên quan.

### 4.2. Dense retrieval là gì?

Dense retrieval là tìm kiếm dựa trên embedding/vector.

Các bước:

1. Embed tất cả chunk luật.
2. Lưu vector vào vector database.
3. Khi có câu hỏi, embed câu hỏi.
4. Tìm các chunk có vector gần câu hỏi nhất.

Trong project này, vector database là **ChromaDB**.

### 4.3. Ưu điểm của dense retrieval

- Hiểu được ngữ nghĩa.
- Tìm được tài liệu dù câu hỏi không trùng từ khóa.
- Phù hợp với câu hỏi tự nhiên.

Ví dụ:

```text
User hỏi: vượt đèn đỏ bị phạt sao?
Luật viết: không chấp hành hiệu lệnh của đèn tín hiệu giao thông
```

Dense retrieval có thể nối được hai cách diễn đạt này.

### 4.4. Nhược điểm của dense retrieval

- Có thể bỏ sót từ khóa pháp lý rất cụ thể.
- Có thể trả kết quả gần nghĩa nhưng sai điều/khoản.
- Với luật, một từ nhỏ như “ô tô”, “xe máy”, “xe đạp” rất quan trọng.

Vì vậy project không chỉ dùng vector search, mà dùng **hybrid search**.

---

## 5. BM25 Và Sparse Search

### 5.1. BM25 là gì?

BM25 là thuật toán tìm kiếm theo từ khóa, thường dùng trong search engine.

Nó đánh giá document dựa trên:

- Từ khóa trong query có xuất hiện trong document không.
- Từ đó xuất hiện bao nhiêu lần.
- Từ đó có hiếm không.
- Độ dài document.

BM25 thuộc nhóm **sparse retrieval**.

### 5.2. Vì sao cần BM25?

Trong luật, keyword rất quan trọng.

Ví dụ:

```text
nồng độ cồn
đường cao tốc
mũ bảo hiểm
giấy phép lái xe
biển báo hiệu
```

Nếu chỉ dùng embedding, đôi khi kết quả “gần nghĩa” nhưng không chứa đúng cụm pháp lý. BM25 giúp giữ lại độ chính xác theo keyword.

### 5.3. Ưu điểm của BM25

- Tốt với từ khóa chính xác.
- Nhanh.
- Dễ giải thích.
- Không cần model embedding.

### 5.4. Nhược điểm của BM25

- Không hiểu tốt từ đồng nghĩa.
- Nếu câu hỏi dùng cách nói khác văn bản luật, BM25 có thể miss.

Ví dụ:

```text
User: vượt đèn đỏ
Luật: không chấp hành hiệu lệnh của đèn tín hiệu giao thông
```

BM25 có thể không mạnh nếu không có query expansion.

---

## 6. Hybrid Search Trong Project

### 6.1. Hybrid search là gì?

Hybrid search là kết hợp nhiều phương pháp retrieval.

Trong project này:

```text
Hybrid Search = Dense Search + BM25 Sparse Search + Metadata Boost
```

Luồng xử lý:

```text
Question
   ↓
Query expansion
   ↓
Dense search trong Chroma
   ↓
Sparse search bằng BM25
   ↓
Merge candidates
   ↓
Metadata boost
   ↓
Final ranking
```

### 6.2. Vì sao dùng hybrid search?

Vì luật giao thông vừa cần hiểu nghĩa, vừa cần đúng keyword.

Dense search giúp hiểu:

```text
vượt đèn đỏ ≈ không chấp hành đèn tín hiệu giao thông
```

BM25 giúp bắt keyword:

```text
nồng độ cồn
trên 0,4 mg/l khí thở
đường cao tốc
```

Metadata boost giúp đúng nhóm:

```text
xe máy → Điều 7
ô tô → Điều 6
xe máy chuyên dùng → Điều 8
xe đạp → Điều 9
người đi bộ → Điều 10
```

### 6.3. Công thức score trong project

Project dùng điểm tổng hợp dạng:

```text
final_score = dense_weight * dense_score
            + sparse_weight * sparse_score
            + boost_weight * boost_score
```

Ý nghĩa:

- `dense_score`: điểm semantic similarity.
- `sparse_score`: điểm keyword/BM25.
- `boost_score`: điểm ưu tiên theo metadata và luật nghiệp vụ.

### 6.4. Metadata boost là gì?

Metadata boost là cộng/trừ điểm dựa trên thông tin có cấu trúc.

Ví dụ:

Nếu câu hỏi có “xe máy”:

```text
Chunk Điều 7, vehicle_group=motorbike → cộng điểm
Chunk Điều 6, vehicle_group=car → trừ điểm
```

Nếu câu hỏi có “ô tô”:

```text
Chunk Điều 6, vehicle_group=car → cộng điểm
Chunk Điều 7, vehicle_group=motorbike → trừ điểm
```

Lý do cần boost:

- Nhiều hành vi giống nhau nhưng mức phạt khác theo phương tiện.
- Vector search có thể thấy “nồng độ cồn” ở nhiều điều khác nhau.
- Cần ưu tiên đúng nhóm phương tiện.

---

## 7. Query Expansion

### 7.1. Query expansion là gì?

Query expansion là mở rộng câu hỏi bằng các cụm từ tương đương.

Ví dụ:

```text
vượt đèn đỏ
```

Được mở rộng thành:

```text
vượt đèn đỏ
không chấp hành hiệu lệnh của đèn tín hiệu giao thông
đèn tín hiệu giao thông
```

### 7.2. Vì sao cần query expansion?

Văn bản luật thường dùng ngôn ngữ chính thức, còn người dùng dùng ngôn ngữ đời thường.

Ví dụ:

| Người dùng nói | Văn bản luật viết |
|---|---|
| vượt đèn đỏ | không chấp hành hiệu lệnh của đèn tín hiệu giao thông |
| say rượu lái xe | trong máu hoặc hơi thở có nồng độ cồn |
| sai làn | không đi đúng phần đường, làn đường quy định |

Query expansion giúp bridge khoảng cách giữa ngôn ngữ tự nhiên và ngôn ngữ pháp lý.

---

## 8. Query Rewriting Cho Chatbot Nhiều Lượt

### 8.1. Vấn đề của câu hỏi nối tiếp

Trong chatbot, người dùng thường hỏi ngắn:

```text
User: Nồng độ cồn xe máy bị phạt bao nhiêu?
Bot: ...
User: Còn ô tô thì sao?
```

Câu “Còn ô tô thì sao?” nếu đem đi search trực tiếp thì thiếu ngữ cảnh.

### 8.2. Query rewriting là gì?

Query rewriting là viết lại câu hỏi nối tiếp thành câu hỏi độc lập.

Ví dụ:

```text
Câu trước: nồng độ cồn xe máy bị phạt bao nhiêu
Câu mới: còn ô tô thì sao
```

Viết lại thành:

```text
nồng độ cồn ô tô bị phạt bao nhiêu
```

Sau đó retrieval dùng câu đã rewrite.

### 8.3. Tên kỹ thuật

Kỹ thuật này có thể gọi là:

- Query Rewriting
- Query Reformulation
- Contextual Query Rewriting
- Conversational Query Reformulation
- History-aware Retrieval

### 8.4. Project đang làm thế nào?

Project có module `query_rewriter.py`.

Logic:

1. Kiểm tra câu hỏi có phải follow-up không.
2. Nếu có lịch sử hội thoại và câu hỏi ngắn/mơ hồ, rewrite lại.
3. Có rule-based rewrite nhanh cho các câu đơn giản.
4. Có thể dùng LLM để rewrite câu hỏi khó hơn.
5. Câu rewrite được dùng cho retrieval.

Luồng:

```text
Current question + chat history
        ↓
QueryRewriter
        ↓
Standalone question
        ↓
HybridRetriever
```

### 8.5. Vì sao không dùng history trực tiếp để trả lời?

History chỉ dùng để hiểu câu hỏi, không dùng để bịa căn cứ pháp lý.

Căn cứ pháp lý vẫn phải đến từ retrieved chunks.

Đây là nguyên tắc quan trọng để tránh hallucination.

---

## 9. LLM Answering

### 9.1. LLM dùng để làm gì?

LLM không phải để tự nhớ luật.

Trong project này, LLM dùng để:

- Đọc các chunk luật đã retrieve.
- Tóm tắt thành câu trả lời dễ hiểu.
- Liệt kê mức phạt nếu có nhiều ngưỡng.
- Nêu citation từ context.
- Từ chối hoặc nói chưa đủ căn cứ nếu context không rõ.

### 9.2. Prompt trong project

Prompt có các nguyên tắc:

- Chỉ trả lời dựa trên context.
- Không tự suy đoán mức phạt.
- Không tạo citation mới.
- Nếu thiếu căn cứ, nói chưa tìm thấy căn cứ đủ rõ.
- Với nồng độ cồn, nếu người dùng không nêu ngưỡng cụ thể thì không trả lời một mức duy nhất.
- Trả lời tiếng Việt ngắn gọn.

### 9.3. Vì sao prompt quan trọng?

Với bài toán luật, prompt giúp kiểm soát hành vi của LLM.

Nếu prompt lỏng, LLM có thể:

- Tự đoán mức phạt.
- Gộp sai các khoản.
- Trích dẫn sai điều.
- Trả lời quá dài hoặc lan man.

Prompt tốt giúp LLM bám sát context hơn.

---

## 10. Citation Và Grounding

### 10.1. Citation là gì?

Citation là nguồn trích dẫn cho câu trả lời.

Ví dụ:

```text
168/2024/NĐ-CP, Điều 7, Khoản 8
```

Citation giúp người dùng kiểm tra lại căn cứ.

### 10.2. Grounding là gì?

Grounding nghĩa là câu trả lời được “neo” vào dữ liệu thật.

Trong RAG, grounding đến từ retrieved context.

Câu trả lời tốt phải:

- Có căn cứ trong chunk.
- Không vượt quá nội dung chunk.
- Nêu đúng điều/khoản.
- Không tự thêm luật ngoài context.

### 10.3. Vì sao citation quan trọng trong luật?

Vì câu trả lời pháp lý cần kiểm chứng.

Nếu chatbot nói:

```text
Bạn bị phạt 6 đến 8 triệu.
```

Nhưng không nêu điều/khoản thì khó tin. Nếu có citation, người dùng có thể kiểm tra lại.

---

## 11. FastAPI Backend

### 11.1. FastAPI dùng để làm gì?

FastAPI là framework Python để xây API.

Trong project, backend cung cấp các endpoint:

```text
GET  /health
POST /retrieve
POST /ask
```

### 11.2. `/health`

Dùng để kiểm tra backend có chạy không.

Trả về trạng thái, model LLM, trạng thái query rewrite.

### 11.3. `/retrieve`

Chỉ chạy retrieval, chưa gọi LLM.

Input:

```json
{
  "question": "vượt đèn đỏ xe máy bị phạt bao nhiêu",
  "top_k": 5
}
```

Output:

```json
{
  "question": "...",
  "results": [
    {
      "citation": "168/2024/NĐ-CP, Điều 7, Khoản 1",
      "score": 0.91,
      "text": "..."
    }
  ]
}
```

Endpoint này hữu ích để debug retrieval.

### 11.4. `/ask`

Chạy full RAG pipeline.

Input:

```json
{
  "question": "nồng độ cồn xe máy bị phạt bao nhiêu",
  "top_k": 5,
  "session_id": "demo"
}
```

Output:

```json
{
  "answer": "...",
  "citations": [...],
  "rewritten_question": "...",
  "was_rewritten": true
}
```

---

## 12. Frontend Chatbot

Frontend là UI để người dùng tương tác.

Chức năng chính:

- Nhập câu hỏi.
- Gửi request đến `/ask`.
- Hiển thị câu trả lời.
- Hiển thị citation bên phải.
- Có session id để hỏi qua lại.
- Hiển thị câu hỏi đã rewrite nếu có.
- Có quick prompts để demo nhanh.

Frontend không xử lý logic RAG. Nó chỉ là giao diện.

Logic chính nằm ở backend.

---

## 13. Evaluation Trong Project

### 13.1. Vì sao cần evaluation?

Nếu chỉ demo vài câu thì chưa đủ chứng minh hệ thống tốt.

Evaluation giúp trả lời:

- Retrieval có tìm đúng điều/khoản không?
- Kết quả đúng có nằm trong top 1 hay top 3 không?
- Các nhóm phương tiện có bị nhầm không?

### 13.2. Bộ eval hiện tại

Project có bộ test trong:

```text
evals/retrieval_eval_seed.jsonl
```

Hiện có 41 câu hỏi, phủ nhiều nhóm phương tiện và hành vi.

### 13.3. Metric đang dùng

#### Recall@1

Tỷ lệ câu hỏi có kết quả đúng ở vị trí đầu tiên.

Ví dụ 40/41 câu đúng top 1:

```text
Recall@1 = 40 / 41 = 0.98
```

#### Recall@3

Tỷ lệ câu hỏi có kết quả đúng nằm trong top 3.

Nếu 41/41 câu có kết quả đúng trong top 3:

```text
Recall@3 = 1.00
```

#### MRR

MRR là Mean Reciprocal Rank.

Nếu kết quả đúng ở rank 1, điểm là 1.
Nếu đúng ở rank 2, điểm là 1/2.
Nếu đúng ở rank 3, điểm là 1/3.

MRR càng gần 1 càng tốt.

### 13.4. Kết quả hiện tại

```text
Cases: 41
Recall@1: 0.98
Recall@3: 1.00
MRR: 0.99
```

Ý nghĩa:

- 40/41 câu đúng ngay top 1.
- 41/41 câu đúng trong top 3.
- Ranking nhìn chung rất tốt.

### 13.5. Lưu ý khi nói về eval

Đây là retrieval eval, chưa phải end-to-end answer eval.

Nghĩa là nó đánh giá bước tìm tài liệu, chưa đánh giá LLM trả lời đúng 100% hay không.

Nếu phỏng vấn hỏi, nên nói rõ:

```text
Em đã đánh giá retrieval bằng Recall@1, Recall@3 và MRR. Còn phần answer của LLM cần thêm faithfulness/citation accuracy để đánh giá end-to-end.
```

---

## 14. Các Lỗi Từng Gặp Và Cách Sửa

### 14.1. Nhầm “cao tốc” thành “ô tô”

Khi normalize tiếng Việt bỏ dấu:

```text
cao tốc → cao toc
ô tô → o to
```

Nếu detect vehicle bằng substring đơn giản, `o to` có thể match nhầm trong `cao toc`.

Cách sửa:

- Không dùng substring đơn giản.
- Dùng word-boundary regex để chỉ match từ/cụm từ độc lập.

Đây là ví dụ thực tế về lỗi NLP tiếng Việt.

### 14.2. Dense search trả sai nhóm phương tiện

Ví dụ câu hỏi về xe máy nhưng kết quả ô tô cũng có nội dung nồng độ cồn.

Cách sửa:

- Thêm `vehicle_group` metadata.
- Boost đúng nhóm phương tiện.
- Penalize nhóm phương tiện sai.

### 14.3. Câu hỏi follow-up thiếu ngữ cảnh

Ví dụ:

```text
Còn ô tô thì sao?
```

Cách sửa:

- Dùng query rewriting dựa trên history.

---

## 15. Điểm Mạnh Của Project

Project có nhiều điểm tốt để trình bày trong CV/phỏng vấn:

- Có pipeline RAG đầy đủ.
- Có hybrid retrieval thay vì chỉ vector search.
- Có query rewriting cho hội thoại nhiều lượt.
- Có metadata boost theo nhóm phương tiện.
- Có citation theo văn bản/điều/khoản.
- Có FastAPI backend.
- Có frontend chatbot.
- Có evaluation bằng metric cụ thể.
- Có Docker optional.
- Có prompt kiểm soát hallucination.

---

## 16. Hạn Chế Hiện Tại

Nên trung thực khi trình bày.

Các hạn chế:

- Bộ eval 41 câu vẫn là seed set nhỏ, chưa đại diện toàn bộ luật giao thông.
- Chưa có end-to-end answer evaluation tự động.
- Chưa có reranker chuyên dụng.
- Memory hội thoại mới ở mức đơn giản.
- Chưa deploy public.
- Dữ liệu phụ thuộc vào bộ JSON đã tổng hợp.
- Nếu văn bản luật thay đổi, cần cập nhật data và ingest lại.

---

## 17. Hướng Cải Tiến

### 17.1. Reranking

Sau khi hybrid retrieval lấy top 20, dùng reranker để sắp xếp lại.

Reranker có thể là:

- Cross-encoder.
- LLM reranker.
- Rule-based reranker nâng cao.

Mục tiêu: tăng Recall@1 và giảm sai rank.

### 17.2. Clarification question

Nếu người dùng hỏi thiếu thông tin:

```text
nồng độ cồn bị phạt bao nhiêu?
```

Bot nên hỏi lại:

```text
Bạn đang hỏi xe máy, ô tô, xe đạp hay xe máy chuyên dùng? Và nồng độ cồn ở mức nào?
```

Điều này giúp tránh trả lời sai.

### 17.3. End-to-end evaluation

Cần thêm bộ test đánh giá answer:

- Answer có đúng mức phạt không?
- Citation có đúng không?
- Có hallucination không?
- Có hỏi lại khi thiếu thông tin không?

### 17.4. Deploy

Có thể deploy:

- Backend: Render, Railway, Fly.io.
- Frontend: Vercel, Netlify, GitHub Pages.

### 17.5. Cache

Cache embedding hoặc cache kết quả query để giảm latency.

---

## 18. Câu Hỏi Phỏng Vấn Thường Gặp

### Câu 1: Project của em giải quyết bài toán gì?

Project của em là chatbot RAG tra cứu luật giao thông Việt Nam. Người dùng nhập câu hỏi tự nhiên, hệ thống tìm các đoạn luật liên quan trong dữ liệu đã ingest, sau đó dùng LLM để trả lời có trích dẫn văn bản, điều và khoản. Mục tiêu là giúp người dùng tra cứu nhanh nhưng vẫn có căn cứ pháp lý rõ ràng.

### Câu 2: Vì sao em dùng RAG thay vì hỏi trực tiếp LLM?

Vì bài toán pháp luật cần độ chính xác và căn cứ. Nếu hỏi trực tiếp LLM, model có thể hallucinate hoặc không biết văn bản mới. RAG giúp đưa các chunk luật thật vào context, buộc LLM trả lời dựa trên dữ liệu đã retrieve và kèm citation.

### Câu 3: Pipeline của project hoạt động thế nào?

Pipeline gồm: nhận câu hỏi, rewrite nếu là câu hỏi nối tiếp, chạy hybrid retrieval gồm dense search, BM25 và metadata boost, lấy top chunks liên quan, đưa chunks vào prompt, LLM tạo câu trả lời, sau đó frontend hiển thị answer và citations.

### Câu 4: Hybrid search là gì và vì sao em dùng nó?

Hybrid search là kết hợp dense retrieval và sparse retrieval. Dense retrieval giúp hiểu ngữ nghĩa, còn BM25 giúp bắt keyword pháp lý chính xác. Với luật giao thông, cả hai đều quan trọng vì người dùng có thể hỏi bằng ngôn ngữ đời thường, nhưng văn bản luật lại dùng thuật ngữ chính thức.

### Câu 5: ChromaDB dùng để làm gì?

ChromaDB được dùng làm vector database. Nó lưu embedding của các chunk luật và hỗ trợ tìm các chunk có vector gần với embedding của câu hỏi.

### Câu 6: BM25 dùng để làm gì?

BM25 dùng để tìm kiếm theo keyword. Nó bổ sung cho vector search, đặc biệt với các cụm pháp lý cụ thể như nồng độ cồn, đường cao tốc, mũ bảo hiểm, giấy phép lái xe.

### Câu 7: Metadata boost là gì?

Metadata boost là cộng hoặc trừ điểm dựa trên thông tin có cấu trúc của chunk. Ví dụ nếu câu hỏi có “xe máy”, hệ thống boost các chunk `vehicle_group=motorbike`, thường là Điều 7 của Nghị định 168/2024/NĐ-CP, và giảm điểm các chunk thuộc nhóm ô tô hoặc phương tiện khác.

### Câu 8: Query rewriting là gì?

Query rewriting là viết lại câu hỏi nối tiếp thành câu hỏi độc lập. Ví dụ sau khi hỏi “nồng độ cồn xe máy bị phạt bao nhiêu”, người dùng hỏi “còn ô tô thì sao”, hệ thống rewrite thành “nồng độ cồn ô tô bị phạt bao nhiêu” rồi mới retrieve.

### Câu 9: Làm sao project hạn chế hallucination?

Project hạn chế hallucination bằng nhiều cách: LLM chỉ được trả lời dựa trên context retrieved, prompt cấm tự suy đoán mức phạt hoặc citation, câu trả lời luôn kèm nguồn, và nếu context không đủ thì phải nói chưa tìm thấy căn cứ đủ rõ.

### Câu 10: Em đánh giá retrieval bằng metric nào?

Em dùng Recall@1, Recall@3 và MRR. Recall@1 đo tỷ lệ câu có kết quả đúng ở top 1. Recall@3 đo tỷ lệ câu có kết quả đúng trong top 3. MRR đánh giá vị trí trung bình của kết quả đúng, kết quả đúng càng đứng cao thì MRR càng gần 1.

### Câu 11: Kết quả eval hiện tại là gì?

Trên seed set 41 câu hỏi luật giao thông, hệ thống đạt Recall@1 = 0.98, Recall@3 = 1.00 và MRR = 0.99. Điều đó nghĩa là 40/41 câu đúng ở top 1 và toàn bộ 41 câu có kết quả đúng trong top 3.

### Câu 12: Hạn chế của project là gì?

Hạn chế là bộ eval vẫn còn nhỏ, chưa có đánh giá end-to-end tự động cho answer của LLM, chưa có reranker chuyên dụng, memory hội thoại còn đơn giản, và dữ liệu cần được cập nhật khi luật thay đổi.

### Câu 13: Nếu cải tiến tiếp em sẽ làm gì?

Em sẽ thêm reranker để tăng độ chính xác top 1, thêm clarification question khi người dùng hỏi thiếu thông tin, mở rộng eval set, đánh giá end-to-end answer faithfulness, và deploy backend/frontend để demo public.

### Câu 14: Vì sao luật giao thông cần hỏi lại người dùng trong vài trường hợp?

Vì cùng một hành vi có mức phạt khác nhau tùy loại phương tiện hoặc ngưỡng vi phạm. Ví dụ nồng độ cồn phụ thuộc vào xe máy, ô tô, xe đạp, xe máy chuyên dùng và ngưỡng nồng độ. Nếu người dùng hỏi quá chung, bot nên hỏi lại thay vì đoán.

### Câu 15: Dense search có thay thế được BM25 không?

Không hoàn toàn. Dense search tốt về ngữ nghĩa nhưng có thể miss các keyword pháp lý cụ thể. BM25 tốt về keyword nhưng không hiểu đồng nghĩa tốt. Kết hợp hai cái giúp retrieval ổn định hơn.

---

## 19. Cách Giải Thích Ngắn Gọn Trong CV

Có thể ghi:

```text
Built a Vietnamese Traffic Law RAG chatbot using FastAPI, ChromaDB, hybrid retrieval
(Dense + BM25), query rewriting, metadata boosting, and OpenAI GPT-4o-mini, with cited
legal sources and an interactive web UI. Evaluated retrieval on 41 queries with
Recall@1 = 0.98, Recall@3 = 1.00, and MRR = 0.99.
```

Bản tiếng Việt:

```text
Xây dựng chatbot RAG tra cứu luật giao thông Việt Nam bằng FastAPI, ChromaDB,
hybrid retrieval (Dense + BM25), query rewriting, metadata boosting và GPT-4o-mini.
Hệ thống trả lời có trích dẫn văn bản/điều/khoản và đạt Recall@1 = 0.98,
Recall@3 = 1.00, MRR = 0.99 trên bộ eval 41 câu hỏi.
```

---

## 20. Tóm Tắt Một Câu

Project này là một hệ thống RAG hỏi đáp luật giao thông Việt Nam, kết hợp hybrid retrieval, query rewriting và LLM answering để trả lời câu hỏi tự nhiên bằng tiếng Việt kèm citation pháp lý rõ ràng.
