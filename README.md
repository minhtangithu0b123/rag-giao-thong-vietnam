# 🇻🇳 Vietnam Traffic Law Retrieval-Augmented Generation (RAG)

A Vietnamese traffic-law question-answering system built with **Retrieval-Augmented Generation (RAG)**.

The system combines **dense semantic retrieval**, **BM25 lexical search**, and **vehicle-aware metadata boosting** to retrieve relevant legal evidence before generating grounded answers with an LLM.

The goal is to provide answers that are not only relevant, but also **grounded in retrieved legal documents with source citations**, while avoiding unsupported penalty claims when the user's question is ambiguous.

## 📊 Retrieval Performance

Evaluated on a 41-query retrieval benchmark:

| Metric       |   Result |
| ------------ | -------: |
| **Recall@1** |  **98%** |
| **Recall@3** | **100%** |
| **MRR**      | **0.99** |

Detailed evaluation results are available in:

```text
evals/retrieval_eval_report.md
```

---

## ✨ Key Features

* End-to-end **Retrieval-Augmented Generation** pipeline for Vietnamese traffic-law QA.
* **Hybrid retrieval** combining:

  * Dense semantic retrieval with **ChromaDB**
  * Sparse lexical retrieval with **BM25**
* **Vehicle-aware metadata boosting** to prioritize regulations relevant to motorcycles, cars, pedestrians, and other vehicle groups.
* Query processing and optional **query rewriting**.
* Ambiguity handling for underspecified questions.
* Grounded LLM answer generation using retrieved legal evidence.
* Source citations in generated answers.
* Conversation memory using `session_id`.
* Retrieval evaluation with **Recall@K** and **Mean Reciprocal Rank (MRR)**.
* REST API implemented with **FastAPI**.
* Containerized deployment with **Docker** and **Docker Compose**.
* Support for both local SentenceTransformer embeddings and OpenAI embeddings.

---

## 🏗️ System Architecture

```text
                         User Question
                              │
                              ▼
                      ┌───────────────┐
                      │ Query Process │
                      │ / Rewriting   │
                      └───────┬───────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
      ┌───────────────┐               ┌──────────────┐
      │ Dense Search  │               │ BM25 Search  │
      │   ChromaDB    │               │   Sparse     │
      └───────┬───────┘               └──────┬───────┘
              │                              │
              └──────────────┬───────────────┘
                             ▼
                  ┌─────────────────────┐
                  │  Hybrid Retrieval   │
                  │ + Metadata Boosting │
                  └──────────┬──────────┘
                             │
                             ▼
                    Top-K Legal Chunks
                             │
                             ▼
                  ┌────────────────────┐
                  │ Prompt Construction│
                  │ + Retrieved Context│
                  └──────────┬─────────┘
                             │
                             ▼
                         OpenAI LLM
                             │
                             ▼
                 Grounded Answer + Sources
```

---

## 🔎 Retrieval Pipeline

The retrieval system combines semantic and lexical signals instead of relying on a single retrieval strategy.

### 1. Dense Retrieval

Legal document chunks are converted into vector embeddings and stored in **ChromaDB**.

Dense retrieval is useful for questions where the wording of the user's query differs from the wording used in the legal document.

Example:

```text
User:
"xe máy uống rượu bia bị phạt thế nào?"
```

may still retrieve regulations containing terms such as:

```text
"nồng độ cồn"
```

even when the exact phrase does not appear in the query.

### 2. BM25 Sparse Retrieval

BM25 provides lexical retrieval based on exact or highly relevant terms.

This is especially useful for legal queries containing important keywords such as:

```text
nồng độ cồn
vượt đèn đỏ
giấy phép lái xe
quá tốc độ
mũ bảo hiểm
```

### 3. Hybrid Ranking

Results from dense retrieval and BM25 are combined into a hybrid ranking pipeline.

```text
Dense Retrieval
       +
BM25 Retrieval
       +
Metadata Boosting
       ↓
Final Ranked Documents
```

This allows the retriever to benefit from both:

* semantic similarity
* lexical matching
* domain-specific metadata

### 4. Vehicle-Aware Metadata Boosting

Traffic penalties often depend on the type of vehicle involved.

For example:

```text
"vượt đèn đỏ xe máy"
```

and:

```text
"ô tô vượt đèn đỏ"
```

may refer to different legal provisions and penalty levels.

The retrieval pipeline therefore uses vehicle-related metadata to boost documents belonging to the appropriate regulation group.

This helps prevent a semantically similar but legally incorrect vehicle category from being ranked above the correct evidence.

### 5. Ambiguity Handling

Some traffic-law questions do not contain enough information to safely determine a single penalty.

Example:

```text
"nồng độ cồn bị phạt bao nhiêu?"
```

The penalty may depend on:

* vehicle type
* alcohol concentration
* specific violation level

When the retrieved context is insufficient to determine a unique answer, the system is designed to avoid guessing and instead request or explain the missing information.

---

## 🤖 Answer Generation

After retrieval, the top-ranked legal chunks are inserted into the LLM prompt as supporting context.

```text
Question
   │
   ▼
Retrieve Top-K Evidence
   │
   ▼
Construct Grounded Prompt
   │
   ▼
LLM
   │
   ▼
Answer + Legal Sources
```

The generation stage is designed around three principles:

**Grounding**
Answers should be based on retrieved legal evidence.

**Citation**
Relevant legal sources should be returned with the answer.

**Hallucination control**
The model should not invent a specific penalty when the retrieved evidence does not provide enough information.

---

## 📈 Evaluation

The retrieval pipeline is evaluated using 41 sample traffic-law questions stored in:

```text
evals/retrieval_eval_seed.jsonl
```

Current results:

```text
Recall@1: 0.98
Recall@3: 1.00
MRR:      0.99
```

### Retrieval Metrics

**Recall@K**

Measures whether the expected legal evidence appears within the top-K retrieved documents.

```text
Recall@1 → correct evidence appears at rank 1
Recall@3 → correct evidence appears within top 3
Recall@5 → correct evidence appears within top 5
```

**Mean Reciprocal Rank (MRR)**

Measures how highly the first relevant document is ranked.

For a query whose first correct result appears at rank `r`:

```text
RR = 1 / r
```

The final MRR is:

```text
MRR = average reciprocal rank across all evaluation queries
```

An MRR of **0.99** indicates that relevant legal evidence is usually ranked at or extremely close to the first position.

### Domain-Specific Evaluation

The system also considers whether the retrieved evidence belongs to the correct vehicle group.

For example:

```text
Motorcycle question → motorcycle regulation
Car question        → car regulation
```

This is important because semantically similar violations may have different penalties depending on vehicle type.

---

## 🧪 Answer Quality Criteria

In addition to retrieval metrics, generated answers can be evaluated using:

| Criterion               | Description                                                      |
| ----------------------- | ---------------------------------------------------------------- |
| **Citation Accuracy**   | Whether the answer cites the correct article/clause/source       |
| **Faithfulness**        | Whether the answer is supported by retrieved evidence            |
| **No Hallucination**    | Whether unsupported penalties or rules are avoided               |
| **Helpfulness**         | Whether the answer is concise and useful                         |
| **Vehicle Consistency** | Whether the answer uses regulations for the correct vehicle type |

---

## 💬 Example Queries

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

---

## 📁 Project Structure

```text
.
├── app/
│   ├── main.py
│   ├── retriever.py
│   ├── rag_chain.py
│   ├── embeddings.py
│   ├── schemas.py
│   └── chat_memory.py
│
├── scripts/
│   ├── clean_data.py
│   ├── ingest_chroma.py
│   └── retrieval.py
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── chroma/
│
├── evals/
│   ├── retrieval_eval_seed.jsonl
│   └── retrieval_eval_report.md
│
├── requirements.txt
├── requirements-render.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
```

### Main Components

| Component                  | Responsibility                             |
| -------------------------- | ------------------------------------------ |
| `app/main.py`              | FastAPI endpoints                          |
| `app/retriever.py`         | Hybrid retrieval pipeline                  |
| `app/rag_chain.py`         | Prompt construction and LLM generation     |
| `app/embeddings.py`        | Embedding provider                         |
| `app/chat_memory.py`       | Lightweight conversation memory            |
| `scripts/clean_data.py`    | Data preprocessing                         |
| `scripts/ingest_chroma.py` | ChromaDB indexing                          |
| `evals/`                   | Retrieval benchmark and evaluation reports |

---

# 🚀 Getting Started

## 1. Clone Repository

```bash
git clone https://github.com/minhtangithu0b123/rag-giao-thong-vietnam.git
cd rag-giao-thong-vietnam
```

## 2. Create Environment

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

---

## 3. Configure Environment Variables

```powershell
$env:OPENAI_API_KEY="your_openai_api_key_here"
$env:LLM_MODEL="gpt-4o-mini"
```

Never commit your real API key to the repository.

---

## 4. Prepare Data

If the ChromaDB index already exists at:

```text
data/chroma/chroma.sqlite3
```

you can skip this step.

Otherwise:

```powershell
python scripts\clean_data.py
python scripts\ingest_chroma.py
```

---

## 5. Run Backend

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API endpoints:

```text
GET  /health
POST /retrieve
POST /ask
```

Local Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Example `/ask` request:

```json
{
  "question": "nồng độ cồn xe máy bị phạt bao nhiêu",
  "top_k": 5,
  "session_id": "demo"
}
```

---

## 6. Run Frontend

Open:

```text
frontend/index.html
```

or serve the directory using VS Code Live Server.

The frontend communicates with:

```text
http://localhost:8000/ask
```

---

# 🐳 Docker

Create `.env` from the example file:

```powershell
copy .env.example .env
```

Configure:

```text
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini
ENABLE_QUERY_REWRITE=1
```

Start the application:

```powershell
docker compose up --build
```

Then access:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

The Chroma database is not copied directly into the Docker image. `docker-compose.yml` mounts the local `./data` directory into the container.

---

# ☁️ Deployment with Render

The standard local configuration uses `sentence-transformers`, which requires PyTorch and can consume significant memory.

For memory-constrained deployment environments, the project provides:

```text
requirements-render.txt
```

Recommended Render configuration:

```text
Runtime:
Python 3

Build Command:
pip install -r requirements-render.txt && python scripts/ingest_chroma.py

Start Command:
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```text
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini
ENABLE_QUERY_REWRITE=1
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
PYTHONIOENCODING=utf-8
```

With:

```text
EMBEDDING_PROVIDER=openai
```

the deployment does not need to load a local SentenceTransformer model, reducing memory usage and the risk of out-of-memory termination.

---

# 🛠️ Tech Stack

**Backend**

```text
Python
FastAPI
```

**Retrieval**

```text
ChromaDB
BM25
Sentence Transformers
OpenAI Embeddings
```

**Generation**

```text
OpenAI API
```

**Deployment**

```text
Docker
Docker Compose
Render
```

**Frontend**

```text
HTML
CSS
JavaScript
```

---

# ⚠️ Limitations

The current project is an MVP and has several limitations:

* The evaluation benchmark currently contains only **41 queries**.
* Retrieval quality depends on the coverage and quality of the indexed legal documents.
* Ambiguous questions may require additional information such as vehicle type or violation level.
* Generated answers should not be treated as professional legal advice.
* Retrieval metrics evaluate document retrieval quality but do not fully measure end-to-end answer correctness.

---

# 🔮 Future Work

Potential improvements include:

* Expand the retrieval evaluation dataset.
* Add automated **faithfulness and citation accuracy evaluation**.
* Introduce a reranking model after hybrid retrieval.
* Improve query classification and metadata filtering.
* Add more robust conversational context handling.
* Improve document ingestion and automatic legal-document updates.
* Evaluate different embedding models and retrieval fusion strategies.
* Add end-to-end RAG evaluation benchmarks.

---

## 📌 Project Goal

This project explores how **hybrid information retrieval, domain-specific metadata, and LLM-based generation** can be combined to build a more reliable question-answering system for Vietnamese traffic regulations.

Rather than relying solely on an LLM's internal knowledge, the system retrieves relevant legal evidence first and uses that evidence to generate grounded, source-aware answers.
