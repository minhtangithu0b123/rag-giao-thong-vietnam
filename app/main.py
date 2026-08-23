from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.chat_memory import ChatMemory
from app.query_rewriter import QueryRewriter
from app.rag_chain import RAGAnswerer
from app.retriever import HybridRetriever
from app.schemas import AskRequest, RetrieveRequest


load_dotenv()

app = FastAPI(title="RAG Luat Giao Thong API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = HybridRetriever()
answerer = RAGAnswerer()
rewriter = QueryRewriter()
memory = ChatMemory()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "RAG Luat Giao Thong API is running",
        "retriever": "ready",
        "llm_model": answerer.model,
        "rewrite_model": rewriter.model,
        "query_rewrite": rewriter.enabled,
    }


@app.post("/retrieve")
def retrieve(request: RetrieveRequest):
    results = retriever.retrieve(
        question=request.question,
        top_k=request.top_k,
    )
    return {
        "question": request.question,
        "results": results,
    }


@app.post("/ask")
def ask(request: AskRequest):
    history = memory.get(request.session_id)
    retrieval_question, was_rewritten = rewriter.rewrite(request.question, history)
    results = retriever.retrieve(
        question=retrieval_question,
        top_k=request.top_k,
    )

    if not results:
        answer = "Chưa tìm thấy căn cứ đủ rõ trong dữ liệu hiện có."
        memory.add_turn(request.session_id, request.question, answer)
        return {
            "answer": answer,
            "citations": [],
            "rewritten_question": retrieval_question,
            "was_rewritten": was_rewritten,
        }

    answer = answerer.answer(
        question=request.question,
        citations=results,
        history=history,
    )
    memory.add_turn(request.session_id, request.question, answer)

    return {
        "answer": answer,
        "citations": results,
        "rewritten_question": retrieval_question,
        "was_rewritten": was_rewritten,
    }
