"""
kb_agent.py — вспомогательный модуль для интеграции CrewAI с векторной Knowledge Base.

Этот модуль позволяет агентам CrewAI использовать поиск по базе знаний (kb_index)
в реальном времени, чтобы расширять контекст анализа и строить решения на основе
текущих стратегий, кода и отчётов.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb

# Пути
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
TRADING_AI_DIR = os.path.dirname(TOOLS_DIR)
PROJECT_ROOT = os.path.dirname(TRADING_AI_DIR)
INDEX_DIR = os.path.join(PROJECT_ROOT, "kb_index")

COLLECTION_NAME = "project_kb"
EMBEDDING_MODEL = "text-embedding-3-small"

# === ENV загрузка ===
env_path = os.path.join(PROJECT_ROOT, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    print("⚠️ .env not found in project root — make sure OPENAI_API_KEY exists.")


def _get_openai_client() -> "OpenAI":
    return OpenAI()


def _get_collection():
    client = chromadb.PersistentClient(path=INDEX_DIR)
    return client.get_collection(COLLECTION_NAME)


def _embed_query(client: "OpenAI", query: str):
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
    return resp.data[0].embedding


def query_kb(query: str, top_k: int = 3) -> str:
    """
    Возвращает короткий текстовый ответ из Knowledge Base (для агентов CrewAI).
    """
    if not os.path.exists(INDEX_DIR):
        return "❌ KB index not found. Run kb_index.py first."

    try:
        client = _get_openai_client()
        collection = _get_collection()

        q_emb = _embed_query(client, query)
        result = collection.query(
            query_embeddings=[q_emb],
            n_results=top_k,
            include=["documents", "metadatas"]
        )

        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]

        summary = []
        for doc, meta in zip(docs, metas):
            file_path = meta.get("file", "unknown")
            text = doc.strip().replace("\n", " ")[:400]
            summary.append(f"📄 {file_path}: {text}")

        return "\n".join(summary) if summary else "⚠️ No relevant context found."

    except Exception as e:
        return f"⚠️ KB query failed: {e}"


if __name__ == "__main__":
    print("🔍 Testing KB Agent Integration:")
    q = "Explain the logic of macro formulas or CPI impact"
    print(query_kb(q))
