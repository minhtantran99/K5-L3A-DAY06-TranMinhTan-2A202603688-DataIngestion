"""Real multilingual ONNX embeddings on CPU. No mock fallback."""
from fastembed import TextEmbedding

class MyEmbedder:
    def __init__(self, model_name, cache_dir):
        self.model_name = model_name
        self.model = TextEmbedding(model_name=model_name, cache_dir=str(cache_dir), threads=4)
        self.dimensions = 384

    def embed_documents(self, texts):
        return [v.tolist() for v in self.model.passage_embed(texts, batch_size=16)]

    def embed_query(self, question):
        return next(iter(self.model.query_embed(question))).tolist()
