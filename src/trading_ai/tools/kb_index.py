"""
kb_index.py — построение векторного индекса по файлам проекта.
Использует OpenAI embeddings + ChromaDB.

Запуск:
  (venv) cd C:/Users/Win11/Desktop/trading_ai
  (venv) python src/trading_ai/tools/kb_index.py
"""

import os
import uuid
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
import chromadb

# ---------- Пути ----------

# Этот файл лежит здесь:
#   C:/Users/Win11/Desktop/trading_ai/src/trading_ai/tools/kb_index.py
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))      # .../src/trading_ai/tools
TRADING_AI_DIR = os.path.dirname(TOOLS_DIR)                 # .../src/trading_ai
SRC_DIR = os.path.dirname(TRADING_AI_DIR)                   # .../src
PROJECT_ROOT = os.path.dirname(SRC_DIR)                     # .../trading_ai

KNOWLEDGE_BASE_DIR = os.path.join(PROJECT_ROOT, "knowledge_base")  # 📂 корневая папка
INDEX_DIR = os.path.join(PROJECT_ROOT, "kb_index")

print("🔍 Diagnostic info:")
print("  Current working dir:", os.getcwd())
print("  TOOLS_DIR:", TOOLS_DIR)
print("  TRADING_AI_DIR:", TRADING_AI_DIR)
print("  SRC_DIR:", SRC_DIR)
print("  PROJECT_ROOT:", PROJECT_ROOT)
print("  Looking for knowledge_base in:", KNOWLEDGE_BASE_DIR)

# ---------- Настройки ----------

EMBEDDING_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "project_kb"

# ---------- Инициализация ----------

def load_env():
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ .env loaded from: {env_path}")
    else:
        print(f"⚠️ .env not found at {env_path}. Make sure OPENAI_API_KEY is set.")

def get_openai_client() -> "OpenAI":
    return OpenAI()

def get_chroma_collection():
    os.makedirs(INDEX_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=INDEX_DIR)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return client.create_collection(COLLECTION_NAME)

# ---------- Чтение и чанкинг ----------

ALLOWED_EXT = (".py", ".yaml", ".yml", ".txt", ".md", ".json")

def iter_files(base_dir: str) -> List[str]:
    paths = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.lower().endswith(ALLOWED_EXT):
                paths.append(os.path.join(root, f))
    return paths

def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ Cannot read {path}: {e}")
        return ""

def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

# ---------- Embeddings ----------

def embed_texts(client: "OpenAI", texts: List[str]) -> List[List[float]]:
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in resp.data]

# ---------- Основная логика ----------

def build_index():
    load_env()
    client = get_openai_client()
    collection = get_chroma_collection()

    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        print(f"⚠️ knowledge_base folder not found at {KNOWLEDGE_BASE_DIR}")
        print("   Создай папку knowledge_base в корне проекта и положи туда свои файлы (py/yaml/txt/md).")
        return

    files = iter_files(KNOWLEDGE_BASE_DIR)
    if not files:
        print(f"⚠️ No files found in {KNOWLEDGE_BASE_DIR}.")
        return

    print(f"📂 Found {len(files)} files in {KNOWLEDGE_BASE_DIR}. Indexing...")

    all_documents, all_ids, all_metadatas = [], [], []

    for path in files:
        rel_path = os.path.relpath(path, PROJECT_ROOT)
        text = read_file(path).strip()
        if not text:
            continue

        chunks = chunk_text(text)
        for idx, chunk in enumerate(chunks):
            all_documents.append(chunk)
            all_ids.append(str(uuid.uuid4()))
            all_metadatas.append({"file": rel_path, "chunk_index": idx})

    print(f"🧠 Total chunks to embed: {len(all_documents)}")

    batch_size = 50
    for i in range(0, len(all_documents), batch_size):
        batch_docs = all_documents[i:i+batch_size]
        batch_ids = all_ids[i:i+batch_size]
        batch_meta = all_metadatas[i:i+batch_size]

        embeddings = embed_texts(client, batch_docs)
        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            embeddings=embeddings,
            metadatas=batch_meta
        )
        print(f"   ➕ Indexed {len(batch_docs)} chunks ({i+len(batch_docs)}/{len(all_documents)})")

    print(f"\n✅ Index build complete. Stored in: {INDEX_DIR}")
    print(f"   Collection name: {COLLECTION_NAME}")

if __name__ == "__main__":
    build_index()
