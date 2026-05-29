from __future__ import annotations

import pickle
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.models import DialogueExample
from backend.storage import read_jsonl


class LocalVectorStore:
    def __init__(self, store_dir: Path) -> None:
        self.store_dir = store_dir
        self.store_path = store_dir / "tfidf_store.pkl"
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None
        self.examples: list[dict] = []

    def build(self, examples: list[DialogueExample]) -> None:
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.examples = [item.to_dict() for item in examples]
        corpus = [self._example_text(item) for item in self.examples]
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1)
        self.matrix = self.vectorizer.fit_transform(corpus) if corpus else None
        with self.store_path.open("wb") as handle:
            pickle.dump({"examples": self.examples, "vectorizer": self.vectorizer, "matrix": self.matrix}, handle)

    def load(self) -> bool:
        if not self.store_path.exists():
            return False
        with self.store_path.open("rb") as handle:
            data = pickle.load(handle)
        self.examples = data["examples"]
        self.vectorizer = data["vectorizer"]
        self.matrix = data["matrix"]
        return True

    def search(self, query: str, k: int = 5) -> list[dict]:
        if self.vectorizer is None or self.matrix is None or not self.examples:
            if not self.load():
                return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).ravel()
        ranked = scores.argsort()[::-1][:k]
        results = []
        for idx in ranked:
            if scores[idx] <= 0:
                continue
            item = dict(self.examples[int(idx)])
            item["score"] = float(scores[idx])
            results.append(item)
        return results

    @staticmethod
    def _example_text(item: dict) -> str:
        return "\n".join([item.get("input", ""), item.get("output", ""), "\n".join(item.get("context", []))])


def load_examples(path: Path) -> list[DialogueExample]:
    return [DialogueExample(**row) for row in read_jsonl(path)]
