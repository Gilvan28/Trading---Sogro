from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
from config import get_client
from settings import INITIAL_CAPITAL
from scanner import get_hot_coins

app = FastAPI()
client = get_client()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "paper_data.json"

# =========================
def load_data():
    try:
        return json.load(open(DATA_FILE))
    except:
        return {
            "capital": INITIAL_CAPITAL,
            "positions": [],
            "trades": [],
            "pending_signals": [],
            "SELECTED_SYMBOLS": [],
            "POSITION_VALUE": 10,
            "BOT_PAUSED": False
        }

def save_data(data):
    json.dump(data, open(DATA_FILE, "w"), indent=4)

# =========================
# MODELS
# =========================
class ConfirmTrade(BaseModel):
    symbol: str

class ClosePosition(BaseModel):
    symbol: str

class ControlUpdate(BaseModel):
    symbols: list[str]
    position_value: float | None = None
    take_profit: float | None = None
    stop_loss: float | None = None

# =========================
@app.get("/status")
def get_status():

    data = load_data()

    total_profit = 0
    total_value = 0
    break_even_active = False

    for pos in data.get("positions", []):

        try:
            ticker = client.get_symbol_ticker(symbol=pos["symbol"])
            price = float(ticker["price"])
        except:
            print(f"⚠️ erro ao pegar preço {pos['symbol']}")
            price = pos.get("entry_price")

        entry = pos["entry_price"]
        qty = pos["quantity"]

        invested = entry * qty
        current_value = price * qty

        profit = current_value - invested
        variation = (profit / invested) * 100 if invested > 0 else 0

        pos["current_price"] = price
        pos["current_value"] = current_value
        pos["profit"] = profit
        pos["variation"] = variation

        total_profit += profit
        total_value += current_value

        if pos.get("break_even_active"):
            break_even_active = True

    return {
        "capital": data.get("capital", 0),
        "positions": data.get("positions", []),
        "total_profit": total_profit,
        "total_value": total_value,
        "break_even_active": break_even_active
    }

# =========================
@app.get("/trades")
def get_trades():
    return load_data().get("trades", [])

# =========================
from datetime import datetime, timedelta

@app.get("/signal")
def get_signal():

    data = load_data()

    valid_signals = []

    for s in data.get("pending_signals", []):

        signal_time = datetime.fromisoformat(s["time"])

        # expira em 2 minutos
        if datetime.now() - signal_time < timedelta(minutes=2):
            valid_signals.append(s)

    # salva só os válidos
    data["pending_signals"] = valid_signals
    save_data(data)

    return valid_signals

# =========================
@app.post("/confirm_trade")
def confirm_trade(payload: ConfirmTrade):

    data = load_data()

    signal = next(
        (s for s in data["pending_signals"] if s["symbol"] == payload.symbol),
        None
    )

    if not signal:
        return {"message": "Sem sinal"}

    if any(p["symbol"] == signal["symbol"] for p in data["positions"]):
        return {"message": "Já existe posição"}

    position_value = data.get("POSITION_VALUE") or 10
    quantity = position_value / signal["price"]

    data["positions"].append({
        "symbol": signal["symbol"],
        "entry_price": signal["price"],
        "quantity": quantity,
        "highest_price": signal["price"],
        "break_even_active": False
    })

    # remove só esse sinal
    data["pending_signals"] = [
        s for s in data["pending_signals"]
        if s["symbol"] != signal["symbol"]
    ]

    save_data(data)

    return {"message": "Trade confirmado"}

# =========================
@app.post("/close_position")
def close_position(payload: ClosePosition):

    data = load_data()

    pos = next((p for p in data["positions"] if p["symbol"] == payload.symbol), None)

    if not pos:
        return {"message": "Posição não encontrada"}

    ticker = client.get_symbol_ticker(symbol=pos["symbol"])
    price = float(ticker["price"])

    result = (price - pos["entry_price"]) * pos["quantity"]

    data["capital"] += result

    data["trades"].append({
        "symbol": pos["symbol"],
        "entry_price": pos["entry_price"],
        "exit_price": price,
        "result": result,
        "timestamp": str(datetime.now())
    })

    data["positions"].remove(pos)
    save_data(data)

    return {"status": f"{pos['symbol']} fechado"}

# =========================
@app.post("/update_control")
def update_control(control: ControlUpdate):

    data = load_data()

    data["SELECTED_SYMBOLS"] = control.symbols

    if control.position_value is not None:
        data["POSITION_VALUE"] = control.position_value

    # 🔥 NOVO
    if control.take_profit is not None:
        data["TAKE_PROFIT"] = control.take_profit

    if control.stop_loss is not None:
        data["STOP_LOSS"] = control.stop_loss

    print("📥 RECEBIDO:", control)

    save_data(data)

    return {"status": "ok"}

# =========================
@app.get("/all_coins")
def all_coins():
    try:
        tickers = client.get_ticker()

        if isinstance(tickers, dict):
            tickers = [tickers]

        usdt_pairs = [
            t for t in tickers
            if t.get("symbol", "").endswith("USDT")
        ]

        sorted_pairs = sorted(
            usdt_pairs,
            key=lambda x: float(x.get("quoteVolume", 0)),
            reverse=True
        )

        return sorted_pairs

    except Exception as e:
        print("Erro all_coins:", e)
        return []

# =========================
@app.get("/hot_coins")
def hot_coins():
    try:
        coins = get_hot_coins()
        return coins if coins else []
    except Exception as e:
        print("Erro hot_coins:", e)
        return []
    

    from fastapi.responses import FileResponse

    @app.get("/")
    def home():
        return FileResponse("Tela-principal.html")