# RAG Luật Giao Thông Việt Nam

MVP chatbot hỏi đáp luật giao thông Việt Nam bằng RAG.

Hệ thống gồm:
- Frontend HTML/CSS/JS chạy local.
- FastAPI backend với endpoint `/retrieve` và `/ask`.
- Hybrid retrieval: Chroma dense search + BM25 sparse search + metadata boost theo loại phương tiện.
- LLM answer bằng OpenAI API, trả lời dựa trên chunk retrieved và kèm nguồn trích dẫn.

## 1. Cấu trúc chính

```text
app/
  main.py          # FastAPI endpoints
  retriever.py     # Hybrid retriever
  rag_chain.py     # Prompt + LLM answer
  embeddings.py    # SentenceTransformer embedding
  schemas.py       # Request schema
  chat_memory.py   # Memory hội thoại đơn giản
scripts/
  clean_data.py
  ingest_chroma.py
  retrieval.py
frontend/
  index.html
  app.js
  styles.css
data/
  raw/
  processed/
  chroma/
evals/
  retrieval_eval_seed.jsonl
```

## 2. Cài môi trường

```powershell
cd D:
ag_giaothong
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Nếu PowerShell chặn activate:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Set OpenAI API key

Set key trong terminal đang chạy backend:

```powershell
$env:OPENAI_API_KEY="your_openai_api_key_here"
$env:LLM_MODEL="gpt-4o-mini"
```

## 4. Chuẩn bị dữ liệu

Nếu đã có `data/chroma/chroma.sqlite3` thì có thể bỏ qua ingest.

Nếu cần build lại index:

```powershell
python scripts\clean_data.py
python scripts\ingest_chroma.py
```

## 5. Chạy backend

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Kiểm tra API:

- Health: http://127.0.0.1:8000/health
- Swagger: http://127.0.0.1:8000/docs

Ví dụ body cho `/ask`:

```json
{
  "question": "nồng độ cồn xe máy bị phạt bao nhiêu",
  "top_k": 5,
  "session_id": "demo"
}
```

## 6. Chạy frontend

Mở file:

```text
frontend/index.html
```

Hoặc dùng Live Server của VS Code. UI sẽ gọi backend tại:

```text
http://localhost:8000/ask
```

## 7. Câu hỏi test MVP

Nên test tối thiểu các câu này:

```text
nồng độ cồn xe máy bị phạt bao nhiêu
vượt đèn đỏ xe máy bị phạt bao nhiêu
ô tô vượt đèn đỏ bị phạt bao nhiêu
không đội mũ bảo hiểm bị phạt bao nhiêu
xe máy chạy quá tốc độ trên 20km/h bị phạt bao nhiêu
đi sai làn bị phạt bao nhiêu
không có giấy phép lái xe bị phạt thế nào
người đi bộ vượt đèn đỏ bị phạt không
```

Với câu thiếu thông tin như `nồng độ cồn bị phạt bao nhiêu`, bot không nên đoán một mức duy nhất. Bot nên nói mức phạt phụ thuộc loại phương tiện và ngưỡng nồng độ cồn nếu context chưa đủ.

## 8. Kết quả eval hiện tại

Retrieval eval hiện tại dùng 41 câu hỏi mẫu trong `evals/retrieval_eval_seed.jsonl`.

```text
Recall@1: 0.98
Recall@3: 1.00
MRR: 0.99
```

Xem report chi tiết tại `evals/retrieval_eval_report.md`.

## 9. Metric đánh giá

Retrieval:
- Recall@3: citation đúng có nằm trong top 3 không.
- Recall@5: citation đúng có nằm trong top 5 không.
- MRR: kết quả đúng đứng càng cao càng tốt.
- Vehicle group accuracy: câu hỏi xe máy phải ưu tiên Điều 7, ô tô Điều 6.

Answer:
- Citation accuracy: câu trả lời có trích đúng số hiệu, điều, khoản không.
- Faithfulness: câu trả lời có bám vào chunk retrieved không.
- No hallucination: không tự bịa mức phạt khi context không đủ.
- Helpfulness: câu trả lời ngắn gọn, dễ hiểu, có gợi ý hỏi thêm khi thiếu thông tin.

## 10. Docker optional

Docker dùng để đóng gói backend FastAPI và dependencies. Dữ liệu Chroma không được copy vào image; `docker-compose.yml` sẽ mount thư mục `./data` từ máy host vào container.

Chuẩn bị `.env` từ file mẫu:

```powershell
copy .env.example .env
```

Sau đó mở `.env` và điền API key:

```text
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini
ENABLE_QUERY_REWRITE=1
```

Chạy backend bằng Docker:

```powershell
docker compose up --build
```

Kiểm tra:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

Lưu ý:

- Cần có sẵn `data/chroma` đã ingest trên máy host.
- Docker image có thể build lâu vì `torch` và `sentence-transformers` khá nặng.
- Nếu chưa có Docker Desktop trên Windows thì vẫn chạy project bằng `.venv` như hướng dẫn local ở trên.

## 11. Deploy Backend Lên Render

Render free tier dễ bị hết RAM nếu cài `torch` và `sentence-transformers`. Vì vậy khi deploy dùng file dependency nhẹ hơn:

```text
requirements-render.txt
```

Trên Render tạo Web Service với cấu hình:

```text
Runtime: Python 3
Build Command: pip install -r requirements-render.txt && python scripts/ingest_chroma.py
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment Variables:

```text
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini
ENABLE_QUERY_REWRITE=1
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
PYTHONIOENCODING=utf-8
```

Khi dùng `EMBEDDING_PROVIDER=openai`, Render không cần load model embedding local nên giảm rủi ro `Exited with status 137` do thiếu RAM.

Sau khi deploy xong, kiểm tra:

```text
https://your-render-service.onrender.com/health
https://your-render-service.onrender.com/docs
```

