from __future__ import annotations

from pathlib import Path

import numpy as np

from turboagents.rag import TurboLanceDB


def main() -> None:
    demo_dir = Path(__file__).resolve().parent
    db_dir = demo_dir / "data" / "lancedb"
    db_dir.mkdir(parents=True, exist_ok=True)

    dim = 64
    index = TurboLanceDB(uri=str(db_dir), dim=dim, bits=3.5, metric="dot")

    vectors = np.zeros((3, dim), dtype=np.float32)
    vectors[0, :4] = [0.98, 0.02, 0.00, 0.00]
    vectors[1, :4] = [0.82, 0.18, 0.02, 0.00]
    vectors[2, :4] = [0.05, 0.88, 0.07, 0.00]
    metadata = [
        {
            "title": "LanceDB Integration",
            "summary": "TurboAgents reranks LanceDB candidates in a local user project.",
            "token": "LANCE-TURBO-314",
        },
        {
            "title": "Compression Layer",
            "summary": "TurboAgents adds compressed retrieval on top of an existing vector store.",
            "token": "COMPRESS-2026",
        },
        {
            "title": "SurrealDB Path",
            "summary": "A separate SurrealDB demo validates the database-backed adapter.",
            "token": "SURREAL-2026",
        },
    ]

    index.create_table("turboagents_demo", vectors, metadata=metadata, mode="overwrite")

    query = np.zeros(dim, dtype=np.float32)
    query[:4] = [1.0, 0.0, 0.0, 0.0]
    results = index.search(query, k=2, rerank_top=3)

    print("TurboAgents standalone LanceDB demo")
    for i, result in enumerate(results, start=1):
        meta = result["metadata"]
        print(
            f"{i}. {meta['title']} | score={result['score']:.4f} | token={meta['token']}"
        )


if __name__ == "__main__":
    main()
