from fastapi import FastAPI, Request
import uvicorn

from trading_ai.services.tradingview.signal_router import process_signal_with_agents
from trading_ai.core.signal_handler import process_trading_signal
from trading_ai.services.telegram.telegram_notifier import send_telegram_message

app = FastAPI()

@app.post("/tv-webhook")
async def tv_webhook(request: Request):
    data = await request.json()

    formatted_signal = process_signal_with_agents(data)
    ai_output = process_trading_signal(data)

    send_telegram_message(formatted_signal)

    send_telegram_message(
        f"📊 *AI Analysis*\n\n{ai_output['ai_summary']}"
    )

    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765)
