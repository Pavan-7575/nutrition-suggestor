from __future__ import annotations

import json
import math
import re
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9'-]{1,}")


@dataclass(frozen=True)
class RetrievedDocument:
    id: str
    title: str
    text: str
    source_url: str
    score: float

    def citation(self) -> dict[str, str]:
        return {"id": self.id, "title": self.title, "url": self.source_url}


class BM25Retriever:
    """Okapi BM25 implementation for lexical keyword search."""

    def __init__(self, corpus: list[dict], k1: float = 1.5, b: float = 0.75):
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.doc_lens = []
        self.doc_term_freqs = []
        self.df = Counter()
        self.n_docs = len(corpus)

        for doc in corpus:
            tokens = [t.lower() for t in TOKEN_PATTERN.findall(f"{doc['title']} {doc['text']}")]
            self.doc_lens.append(len(tokens))
            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)
            for token in tf:
                self.df[token] += 1

        self.avg_dl = sum(self.doc_lens) / max(self.n_docs, 1)

    def _idf(self, term: str) -> float:
        n_q = self.df.get(term, 0)
        return math.log(max(0.0, (self.n_docs - n_q + 0.5) / (n_q + 0.5)) + 1.0)

    def score(self, query: str) -> list[float]:
        q_tokens = [t.lower() for t in TOKEN_PATTERN.findall(query)]
        scores = [0.0] * self.n_docs
        for term in q_tokens:
            idf = self._idf(term)
            for i, tf in enumerate(self.doc_term_freqs):
                freq = tf.get(term, 0)
                if freq > 0:
                    numerator = freq * (self.k1 + 1)
                    denominator = freq + self.k1 * (1 - self.b + self.b * (self.doc_lens[i] / max(self.avg_dl, 1)))
                    scores[i] += idf * (numerator / denominator)
        return scores


class BGEEmbeddingRetriever:
    """Semantic vector retriever using BGE embeddings via Ollama API."""

    def __init__(self, corpus: list[dict], model: str = "bge-m3", host: str = "http://localhost:11434"):
        self.corpus = corpus
        self.model = model
        self.host = host.rstrip("/")
        self.doc_embeddings: list[list[float]] = []
        self._precompute_doc_embeddings()

    def _get_embedding(self, text: str) -> list[float] | None:
        endpoint = f"{self.host}/api/embeddings"
        payload = json.dumps({"model": self.model, "prompt": text}).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("embedding")
        except Exception:  # noqa: BLE001
            return None

    def _precompute_doc_embeddings(self) -> None:
        for doc in self.corpus:
            emb = self._get_embedding(f"{doc['title']}: {doc['text']}")
            if emb:
                self.doc_embeddings.append(emb)

    @staticmethod
    def _cosine_sim(v1: list[float], v2: list[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        return dot / (norm1 * norm2) if (norm1 and norm2) else 0.0

    def score(self, query: str) -> list[float] | None:
        if len(self.doc_embeddings) != len(self.corpus):
            # Try to fetch once if not populated
            self._precompute_doc_embeddings()
            if len(self.doc_embeddings) != len(self.corpus):
                return None

        q_emb = self._get_embedding(query)
        if not q_emb:
            return None

        return [self._cosine_sim(q_emb, d_emb) for d_emb in self.doc_embeddings]


class LocalKnowledgeBase:
    """Hybrid Retriever combining BM25 (lexical) and BGE Dense Embeddings."""

    def __init__(self, corpus_path: Path | None = None, host: str = "http://localhost:11434"):
        path = corpus_path or Path(__file__).parents[1] / "data" / "knowledge_base.json"
        self.documents = json.loads(path.read_text(encoding="utf-8"))
        self.bm25 = BM25Retriever(self.documents)
        self.bge = BGEEmbeddingRetriever(self.documents, model="bge-m3", host=host)

    def search(self, query: str, limit: int = 3) -> list[RetrievedDocument]:
        bm25_scores = self.bm25.score(query)
        bge_scores = self.bge.score(query)

        final_ranked: list[tuple[float, int]] = []
        n_docs = len(self.documents)

        if bge_scores:
            # Reciprocal Rank Fusion (RRF)
            # Rank documents in both algorithms
            bm25_ranked = [idx for _, idx in sorted(zip(bm25_scores, range(n_docs)), reverse=True)]
            bge_ranked = [idx for _, idx in sorted(zip(bge_scores, range(n_docs)), reverse=True)]

            k = 60  # standard RRF constant
            rrf_scores = [0.0] * n_docs

            for rank, idx in enumerate(bm25_ranked):
                if bm25_scores[idx] > 0:
                    rrf_scores[idx] += 1.0 / (k + rank + 1)

            for rank, idx in enumerate(bge_ranked):
                if bge_scores[idx] > 0:
                    rrf_scores[idx] += 1.0 / (k + rank + 1)

            for idx, score in enumerate(rrf_scores):
                if score > 0:
                    final_ranked.append((score, idx))
        else:
            # Graceful fallback to pure BM25 if BGE model is pulling or unavailable
            for idx, score in enumerate(bm25_scores):
                if score > 0:
                    final_ranked.append((score, idx))

        final_ranked.sort(key=lambda x: x[0], reverse=True)

        return [
            RetrievedDocument(
                id=self.documents[index]["id"],
                title=self.documents[index]["title"],
                text=self.documents[index]["text"],
                source_url=self.documents[index]["source_url"],
                score=round(score, 3),
            )
            for score, index in final_ranked[:limit]
        ]
