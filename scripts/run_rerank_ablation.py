#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_REPO_ROOT))

from src.core.query_engine.dense_retriever import create_dense_retriever
from src.core.query_engine.hybrid_search import create_hybrid_search
from src.core.query_engine.query_processor import QueryProcessor
from src.core.query_engine.reranker import create_core_reranker
from src.core.query_engine.sparse_retriever import create_sparse_retriever
from src.core.settings import load_settings
from src.ingestion.storage.bm25_indexer import BM25Indexer
from src.libs.embedding.embedding_factory import EmbeddingFactory
from src.libs.vector_store.vector_store_factory import VectorStoreFactory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run retrieval rerank ablation.")
    parser.add_argument("--test-set", default="eval/ophthalmology_retrieval_hard.json")
    parser.add_argument("--config", default="config/settings.yaml")
    parser.add_argument("--collection", default="ophthalmology_base")
    parser.add_argument("--retrieval-mode", choices=["hybrid", "dense", "sparse"], default="dense")
    parser.add_argument("--candidate-k", type=int, default=50)
    parser.add_argument("--final-k", type=int, default=10)
    parser.add_argument("--use-rerank", action="store_true")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def load_cases(path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):
        for key in ("test_cases", "cases", "samples", "data"):
            if key in data:
                return list(data[key])
    if isinstance(data, list):
        return data
    raise ValueError(f"Unsupported test set format: {path}")


def normalize_source(source: Any) -> str:
    return str(source).replace("\\", "/").rstrip("/").split("/")[-1]


def result_source(result: Any) -> str:
    metadata = getattr(result, "metadata", {}) or {}
    return normalize_source(metadata.get("source_path") or metadata.get("source") or "")


def source_metrics(retrieved_sources: list[str], expected_sources: list[str]) -> dict[str, float]:
    expected = {normalize_source(x) for x in expected_sources}
    if not expected:
        return {"source_hit@k": 0.0, "source_mrr@k": 0.0, "source_coverage@k": 0.0}

    hit = 0.0
    mrr = 0.0
    covered = set()

    for rank, source in enumerate(retrieved_sources, start=1):
        if source in expected:
            covered.add(source)
            if hit == 0.0:
                hit = 1.0
                mrr = 1.0 / rank

    return {
        "source_hit@k": hit,
        "source_mrr@k": mrr,
        "source_coverage@k": len(covered) / len(expected),
    }


def build_search(settings: Any, collection: str, retrieval_mode: str) -> Any:
    vector_store = VectorStoreFactory.create(settings, collection_name=collection)
    embedding_client = EmbeddingFactory.create(settings)

    dense_retriever = create_dense_retriever(
        settings=settings,
        embedding_client=embedding_client,
        vector_store=vector_store,
    )

    bm25_indexer = BM25Indexer(index_dir=f"data/db/bm25/{collection}")
    sparse_retriever = create_sparse_retriever(
        settings=settings,
        bm25_indexer=bm25_indexer,
        vector_store=vector_store,
    )
    sparse_retriever.default_collection = collection

    search = create_hybrid_search(
        settings=settings,
        query_processor=QueryProcessor(),
        dense_retriever=dense_retriever,
        sparse_retriever=sparse_retriever,
    )

    if retrieval_mode == "dense":
        search.config.enable_sparse = False
    elif retrieval_mode == "sparse":
        search.config.enable_dense = False

    return search


def avg(rows: list[float]) -> float:
    return sum(rows) / len(rows) if rows else 0.0


def main() -> int:
    args = parse_args()
    settings = load_settings(args.config)
    search = build_search(settings, args.collection, args.retrieval_mode)
    reranker = create_core_reranker(settings=settings)

    cases = load_cases(args.test_set)
    rows = []

    for idx, case in enumerate(cases, start=1):
        query = case.get("query") or case.get("question")
        expected_sources = case.get("expected_sources", [])
        print(f"[{idx}/{len(cases)}] {query}", file=sys.stderr)

        t0 = time.monotonic()
        search_result = search.search(query=query, top_k=args.candidate_k)
        candidates = search_result if isinstance(search_result, list) else search_result.results
        rerank_used = False
        rerank_fallback = False
        reranker_type = "none"

        if args.use_rerank:
            rerank_result = reranker.rerank(query=query, results=candidates, top_k=args.final_k)
            results = rerank_result.results
            rerank_used = True
            rerank_fallback = bool(rerank_result.used_fallback)
            reranker_type = rerank_result.reranker_type
        else:
            results = candidates[: args.final_k]

        elapsed_ms = (time.monotonic() - t0) * 1000.0
        retrieved_sources = [result_source(x) for x in results]
        metrics = source_metrics(retrieved_sources, expected_sources)

        rows.append({
            "query": query,
            "expected_sources": [normalize_source(x) for x in expected_sources],
            "retrieved_sources": retrieved_sources,
            "retrieved_chunk_ids": [getattr(x, "id", "") for x in results],
            "metrics": metrics,
            "elapsed_ms": elapsed_ms,
            "rerank_used": rerank_used,
            "rerank_fallback": rerank_fallback,
            "reranker_type": reranker_type,
        })

    aggregate = {
        "query_count": len(rows),
        "source_hit@k": avg([r["metrics"]["source_hit@k"] for r in rows]),
        "source_mrr@k": avg([r["metrics"]["source_mrr@k"] for r in rows]),
        "source_coverage@k": avg([r["metrics"]["source_coverage@k"] for r in rows]),
        "avg_query_ms": avg([r["elapsed_ms"] for r in rows]),
        "fallback_count": sum(1 for r in rows if r["rerank_fallback"]),
    }

    report = {
        "test_set": args.test_set,
        "config": args.config,
        "collection": args.collection,
        "retrieval_mode": args.retrieval_mode,
        "candidate_k": args.candidate_k,
        "final_k": args.final_k,
        "use_rerank": args.use_rerank,
        "aggregate": aggregate,
        "results": rows,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {output}", file=sys.stderr)
    print(json.dumps(aggregate, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())