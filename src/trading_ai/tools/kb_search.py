# -*- coding: utf-8 -*-
r"""
kb_search.py — поиск по векторному индексу проектной "памяти".

Запуск (пример):
  (venv) cd C:/Users/Win11/Desktop/trading_ai
  (venv) python src/trading_ai/tools/kb_search.py "risk management strategy"
"""

import os
import sys
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
import chromadb

# ---------- Пути ----------

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))      # .../src/trading_ai/tools
TRADING_AI_DIR = os.path.dirname(TOOLS_DIR)                 # .../src/trading_ai
SRC_DIR = os.path.dirname(TRADING_AI_DIR)                   # .../src
PROJECT_ROOT = os.path.dirname(SRC_DIR)                     # .../trading_ai

INDEX_DIR = os.path.join(PROJECT_ROOT, "kb_index")
COLLECTION_NAME = "project_kb"
EMBEDDING_MODEL = "text-embedding-3-small"

# ---------- Инициализация ----------

def load_env():
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ .env loaded from: {env_path}")
    else:
        print("⚠️ .env not found at project root. Make sure OPENAI_API_KEY is set.")

def get_openai_client() -> "OpenAI":
    return OpenAI()

def get_collection():
    client = chromadb.PersistentClient(path=INDEX_DIR)
    return client.get_collection(COLLECTION_NAME)

def embed_query(client: "OpenAI", query: str) -> List[float]:
    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query]
    )
    return resp.data[0].embedding

# ---------- Поиск ----------

def search(query: str, top_k: int = 5):
    load_env()
    if not os.path.exists(INDEX_DIR):
        print(f"❌ Index folder {INDEX_DIR} not found. Run kb_index.py first.")
        return

    client = get_openai_client()
    collection = get_collection()

    q_emb = embed_query(client, query)

    result = collection.query(
        query_embeddings=[q_emb],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0]

    if not docs:
        print("⚠️ No results found.")
        return

    print(f"\n🔎 Query: {query}")
    print(f"Top-{top_k} matches:\n")

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists), start=1):
        file_path = meta.get("file", "unknown")
        chunk_idx = meta.get("chunk_index", -1)
        print(f"#{i}  (distance={dist:.4f})")
        print(f"📄 File: {file_path}  | chunk: {chunk_idx}")
        print("────────────────────────────────────────────────────────")
        print(doc.strip()[:1000])
        print("────────────────────────────────────────────────────────\n")

# ---------- CLI ----------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python kb_search.py \"your question or query here\"")
    else:
        query = " ".join(sys.argv[1:])
        search(query)
