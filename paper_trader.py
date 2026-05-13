import time
import json
from datetime import datetime
from config import get_client
from settings import *
from scanner import get_hot_coins

print("🚀 Bot iniciado...")

client = get_client()
DATA_FILE = "paper_data.json"

def load():
    try:
        return json.load(open(DATA_FILE))
    except:
        return {
            "capital": INITIAL_CAPITAL,
            "positions": [],
            "pending_signals": [],
            "SELECTED_SYMBOLS": [],
            "trades": [],
            "BOT_PAUSED": False
        }

def save(d):
    json.dump(d, open(DATA_FILE, "w"), indent=4)

# =========================
def should_enter(symbol):

    try:
        klines = client.get_klines(symbol=symbol, interval="1m", limit=50)
        closes = [float(k[4]) for k in klines]

        last = closes[-1]

        ema9 = sum(closes[-9:]) / 9
        ema21 = sum(closes[-21:]) / 21

        tendencia = ema9 > ema21
        variacao = ((last - closes[-3]) / closes[-3]) * 100

        if variacao > 6:
            return False

        if tendencia and variacao > 0.2:
            print(f"✅ SINAL {symbol} | {variacao:.2f}%")
            return True

        return False

    except Exception as e:
        print("Erro:", e)
        return False

# =========================
while True:

    try:
        print("🔄 LOOP RODANDO...")

        data = load()

        # 🔥 GARANTE LISTA
        if "pending_signals" not in data:
            data["pending_signals"] = []

        if data.get("BOT_PAUSED"):
            print("⏸ BOT PAUSADO")
            time.sleep(INTERVAL)
            continue

        selected = data.get("SELECTED_SYMBOLS", [])

        # =========================
        # 🔥 GERAR SINAIS
        # =========================
        # 🔥 GERAR SINAL CONTROLADO
        if not data.get("pending_signals") and not data.get("positions"):

            for symbol in selected:

                print(f"🔍 analisando {symbol}")

                if should_enter(symbol):

                    price = float(client.get_symbol_ticker(symbol=symbol)["price"])

                    data["pending_signals"] = [{
                        "symbol": symbol,
                        "price": price,
                        "time": str(datetime.now())
                    }]

                    print(f"🔥 SINAL GERADO: {symbol}")
                    save(data)

                    break

        # =========================
        # 💰 GERENCIAR POSIÇÕES
        # =========================
        for pos in data.get("positions", [])[:]:

            symbol = pos["symbol"]
            entry = pos["entry_price"]
            qty = pos["quantity"]

            try:
                price = float(client.get_symbol_ticker(symbol=symbol)["price"])
            except:
                print(f"⚠️ erro ao pegar preço {symbol}")
                continue

            variation = ((price - entry) / entry) * 100

            pos["current_price"] = price
            pos["variation"] = variation
            pos["profit"] = (price - entry) * qty

            print(f"📊 {symbol} | {variation:.2f}%")

            pos.setdefault("highest_price", entry)
            pos.setdefault("break_even_active", False)

            if price > pos["highest_price"]:
                pos["highest_price"] = price

            trailing_percent = 0.5
            trail_price = pos["highest_price"] * (1 - trailing_percent / 100)

            # BREAK EVEN
            if variation >= BREAK_EVEN_TRIGGER:
                pos["break_even_active"] = True

            if pos["break_even_active"] and variation <= 0:
                print("🛡️ BREAK EVEN")

                result = (price - entry) * qty
                data["capital"] += result

                data["trades"].append({
                    "symbol": symbol,
                    "entry_price": entry,
                    "exit_price": price,
                    "result": result,
                    "type": "BREAK_EVEN",
                    "timestamp": str(datetime.now())
                })

                data["positions"].remove(pos)
                continue

            # TRAILING STOP
            if price <= trail_price:
                print("🔥 TRAILING STOP")

                result = (price - entry) * qty
                data["capital"] += result

                data["trades"].append({
                    "symbol": symbol,
                    "entry_price": entry,
                    "exit_price": price,
                    "result": result,
                    "type": "TRAILING_STOP",
                    "timestamp": str(datetime.now())
                })

                data["positions"].remove(pos)
                continue

            # TAKE / STOP
            if variation >= TAKE_PROFIT or variation <= STOP_LOSS:
                print("💰 SAÍDA")

                result = (price - entry) * qty
                data["capital"] += result

                data["trades"].append({
                    "symbol": symbol,
                    "entry_price": entry,
                    "exit_price": price,
                    "result": result,
                    "type": "DEFAULT_EXIT",
                    "timestamp": str(datetime.now())
                })

                data["positions"].remove(pos)
                continue

        save(data)

    except Exception as e:
        print("❌ ERRO:", e)

    time.sleep(INTERVAL)