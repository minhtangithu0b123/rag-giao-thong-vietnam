from sentence_transformers import SentenceTransformer

model_name = "BAAI/bge-m3"

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text):
        return self.model.encode(
            text,
            normalize_embeddings=True,
        ).tolist()
    def embed_batch(self, texts: list[str]):
        return self.model.encode(
            texts,
            batch_size=16,
            show_progress_bar=True,
            normalize_embeddings=True,
        ).tolist()