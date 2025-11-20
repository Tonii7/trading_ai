import os
from crewai.memory.memory import Memory

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MEMORY_DIR = os.path.join(BASE_DIR, "trading_ai", "memory")

def show_memory_status():
    print("🧠 Checking memory status...\n")

    if not os.path.exists(MEMORY_DIR):
        print("❌ No memory folder found — try running the crew first.")
        return

    files = [f for f in os.listdir(MEMORY_DIR) if f.endswith(".db")]
    if not files:
        print("⚠️ No agent memory files found yet.")
        return

    for file in files:
        path = os.path.join(MEMORY_DIR, file)
        agent_name = file.replace(".db", "")
        print(f"📘 Agent: {agent_name}")

        try:
            mem = Memory(storage="chromadb", path=path)
            items = mem.list() if hasattr(mem, "list") else []
            print(f"   ├─ Total records: {len(items)}")
            if len(items) > 0:
                print(f"   └─ Last entry: {items[-1]}")
        except Exception as e:
            print(f"   ⚠️ Could not read memory: {e}")

        print("")

if __name__ == "__main__":
    show_memory_status()
