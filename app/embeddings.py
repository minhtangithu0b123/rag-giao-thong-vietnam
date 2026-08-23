import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

LOCAL_MODEL_NAME = os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-m3")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local").lower()


class EmbeddingService:
    def __init__(self):
        self.provider = EMBEDDING_PROVIDER

        if self.provider == "openai":
            self.client = OpenAI()
            self.local_model = None
        else:
            from sentence_transformers import SentenceTransformer

            self.client = None
            self.local_model = SentenceTransformer(LOCAL_MODEL_NAME)

    def embed_text(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self.provider == "openai":
            response = self.client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL,
                input=texts,
            )
            return [item.embedding for item in response.data]

        return self.local_model.encode(
            texts,
            batch_size=16,
            show_progress_bar=True,
            normalize_embeddings=True,
        ).tolist()
