# src/trading_ai/agents/manager.py

from src.trading_ai.agents.research_agent import ResearchAgent
from src.trading_ai.agents.cfa_agent import CFAAgent
from src.trading_ai.agents.macro_agent import MacroAgent  # если есть
from src.trading_ai.agents.analytics_agent import AnalyticsAgent
from src.trading_ai.agents.fred_agent import FredAgent


class AgentManager:
    def __init__(self):
        self.agents = {
            "research": ResearchAgent(),
            "cfa": CFAAgent(),
            "macro": MacroAgent(),        # можешь убрать, если лишний
            "analytics": AnalyticsAgent(),
            "fred": FredAgent(),          # ✅ подключаем твой FRED-агент
        }

    def run_all(self):
        print("🤖 Launching all agents...\n")
        for name, agent in self.agents.items():
            print(f"⚙️ Running {name} agent...")
            agent.run()
            print("")  # пустая строка для читаемости
        print("✅ All agents completed.\n")
