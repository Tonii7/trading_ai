from typing import Dict, Any
# TODO: сюда позже добавим вызов твоих CrewAI агентов


def process_signal_with_agents(signal: Dict[str, Any]) -> str:
    """Преобразует сигнал в финальный текст, готовый к отправке в Telegram."""
    symbol = signal.get("symbol") or "UNKNOWN"
    direction = signal.get("direction") or "UNKNOWN"
    price = signal.get("price")
    strategy = signal.get("strategy")

    lines = [
        "🔔 *TradingView Signal Received*",
        "",
        f"*Instrument:* `{symbol}`",
        f"*Direction:* `{direction}`",
    ]
    if price:
        lines.append(f"*Price:* `{price}`")
    if strategy:
        lines.append(f"*Strategy:* `{strategy}`")

    if signal.get("extra", {}).get("fallback"):
        lines.append("")
        lines.append("_⚠️ Alert was NOT JSON formatted. Please switch TV alert to JSON mode._")

    lines.append("")
    lines.append("*Raw Body:*")
    raw = signal.get("raw_body") or "(empty)"
    if len(raw) > 1500:
        raw = raw[:1500] + "\n...\n(truncated)"
    lines.append(f"```text\n{raw}\n```")

    return "\n".join(lines)
