from __future__ import annotations

import re
import json
import math
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .models import ManualChunk, RetrievalQuery


@dataclass(frozen=True)
class RetrievalResult:
    chunk: ManualChunk
    score: float


# Metadatos por documento del corpus: a qué equipos aplica y quién lo emite.
# Es un mapa explícito (fuente: datos/documentos/indice.json), no "general" para todo.
_DOCUMENT_METADATA: dict[str, tuple[list[str], str]] = {
    "TX350-D": (["B-101", "B-102", "B-103"], "Trimax Industrial"),
    "TX350-C": (["B-101", "B-102", "B-103"], "Trimax Industrial"),
    "FC48-3": (["F-201A", "F-201B"], "Filtrapat"),
    "MBP-4": (["B-101", "B-102", "B-103", "F-201A", "F-201B", "TK-301", "FT-401"], "operadora"),
    "CT-SVP-2025": (["B-101", "B-102", "B-103"], "Servipat"),
    "CERT-EJ": (["B-101", "B-102", "B-103"], "Servipat"),
    "historial": ([], "operadora"),
}

_TAG_RE = re.compile(r"\b(?:B-\d{3}|F-\d{3}[A-Z]?|TK-\d{3}|FT-\d{3})\b")


class ManualIndex:
    """Índice léxico pequeño y reproducible; pgvector es el backend previsto.

    El ranking actual es BM25 sobre tokens: es un fallback determinista y sin
    red, no un índice de embeddings. Cada fragmento conserva su equipo,
    fabricante, documento, sección, cita y vigencia para poder filtrar.
    """

    def __init__(self, chunks: list[ManualChunk] | None = None) -> None:
        self.chunks = chunks or []

    def add(self, chunk: ManualChunk) -> None:
        self.chunks.append(chunk)

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "ManualIndex":
        source = Path(path)
        if not source.is_file():
            raise FileNotFoundError(f"Corpus inexistente: {source}")
        chunks: list[ManualChunk] = []
        with source.open(encoding="utf-8") as handle:
            for line in handle:
                item = json.loads(line)
                citation = item["id"]
                doc = item["doc"]
                equipment_tags, manufacturer = _DOCUMENT_METADATA.get(doc, ([], "desconocido"))
                if doc == "historial":
                    # El equipo de la orden está en el título: "OT-24-0001 B-101 T-B-VAL".
                    tag = next((m for m in _TAG_RE.findall(item.get("titulo", ""))), None)
                    equipment_tags = [tag] if tag else []
                equipment_tag = equipment_tags[0] if equipment_tags else "general"
                chunks.append(
                    ManualChunk(
                        equipment_tag=equipment_tag,
                        equipment_tags=equipment_tags,
                        manufacturer=manufacturer,
                        document=doc,
                        section=citation,
                        citation=citation,
                        text=item["texto"],
                        vigente=bool(item.get("vigente", False)),
                    )
                )
        return cls(chunks)

    def _matches_equipment(self, chunk: ManualChunk, equipment_tag: str | None) -> bool:
        if equipment_tag is None:
            return True
        if chunk.equipment_tags:
            return equipment_tag in chunk.equipment_tags
        # Sin lista explícita: un fragmento "general" aplica a todo; si no, por tag.
        if chunk.equipment_tag == "general":
            return True
        return chunk.equipment_tag == equipment_tag

    def search(self, query: RetrievalQuery) -> list[RetrievalResult]:
        terms = self._tokens(query.question)
        candidates = [
            chunk
            for chunk in self.chunks
            if chunk.vigente and self._matches_equipment(chunk, query.equipment_tag)
        ]
        document_frequency: dict[str, int] = {}
        tokenized: list[tuple[ManualChunk, list[str]]] = []
        for chunk in candidates:
            tokens = self._tokens(
                f"{chunk.text} {chunk.section} {chunk.document}"
            )
            tokenized.append((chunk, tokens))
            for term in set(tokens):
                document_frequency[term] = document_frequency.get(term, 0) + 1
        ranked = []
        average_length = (
            sum(len(tokens) for _, tokens in tokenized) / len(tokenized)
            if tokenized else 1
        )
        total_documents = len(tokenized) or 1
        for chunk, tokens in tokenized:
            counts = {term: tokens.count(term) for term in set(tokens)}
            score = 0.0
            for term in terms:
                frequency = counts.get(term, 0)
                if not frequency:
                    continue
                idf = math.log(
                    1 + (total_documents - document_frequency.get(term, 0) + 0.5)
                    / (document_frequency.get(term, 0) + 0.5)
                )
                denominator = frequency + 1.4 * (
                    1 - 0.75 + 0.75 * len(tokens) / average_length
                )
                score += idf * frequency * 2.4 / denominator
            if score:
                score += self._document_priority(chunk.document) * 0.01
                ranked.append(RetrievalResult(chunk, float(score)))
        return sorted(
            ranked, key=lambda item: (-item.score, item.chunk.citation)
        )[: query.k]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        normalized = unicodedata.normalize("NFD", text.casefold())
        normalized = "".join(
            char for char in normalized
            if unicodedata.category(char) != "Mn"
        )
        return re.findall(r"[a-z0-9]+", normalized)

    @staticmethod
    def _document_priority(document: str) -> int:
        if document.endswith("-D"):
            return 1
        if document.endswith("-C"):
            return -1
        return 0

    def evaluate_official(
        self, retrieval_json: str | Path, k_values: tuple[int, ...] = (1, 3, 5, 10)
    ) -> dict[str, object]:
        source = Path(retrieval_json)
        if not source.is_file():
            raise FileNotFoundError(f"Suite de retrieval inexistente: {source}")
        suite = json.loads(source.read_text(encoding="utf-8"))
        rows: list[dict[str, float | str]] = []
        for item in suite:
            results = self.search(
                RetrievalQuery(question=item["pregunta"], k=max(max(k_values), 20))
            )
            citations = [result.chunk.citation for result in results]
            relevant = set(item["relevantes"])
            distractors = set(item["distractores"])
            row: dict[str, float | str] = {"id": item["id"]}
            for k in k_values:
                top = citations[:k]
                row[f"hit@{k}"] = float(bool(relevant.intersection(top)))
                row[f"recall@{k}"] = len(relevant.intersection(top)) / len(relevant)
                row[f"distractor@{k}"] = float(
                    any(
                        citation in distractors
                        and not any(relevant_citation in top[:index] for relevant_citation in relevant)
                        for index, citation in enumerate(top)
                    )
                )
            rows.append(row)
        total = {
            metric: round(
                sum(float(row[metric]) for row in rows) / len(rows), 3
            )
            for metric in rows[0]
            if metric != "id"
        }
        return {"n": len(rows), "total": total, "preguntas": rows}


def build_context(results: list[RetrievalResult], max_chunks: int = 5) -> str:
    return "\n\n".join(
        f"[{result.chunk.citation}] {result.chunk.text}"
        for result in results[:max_chunks]
    )
