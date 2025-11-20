from __future__ import annotations

from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True) or {}
    symbol = data.get("symbol")
    signal = data.get("signal")
    price = data.get("price")

    print(f"📩 Webhook received: {data}")

    # TODO: здесь ты можешь:
    # - записать сигнал в БД / файл
    # - передать в агента Signal Analyzer
    # - отправить уведомление в Telegram, и т.п.

    if not symbol or not signal:
        return jsonify({"status": "error", "message": "Missing symbol or signal"}), 400

    return jsonify({"status": "ok", "symbol": symbol, "signal": signal, "price": price}), 200


if __name__ == "__main__":
    # Запуск локального сервера на 5001
    app.run(host="0.0.0.0", port=5001)
