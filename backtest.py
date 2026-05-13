from config import get_client
from settings import (
    SYMBOL,
    STOP_LOSS,
    TAKE_PROFIT,
    POSITION_PERCENT,
    BUY_FEE,
    SELL_FEE,
)

import matplotlib.pyplot as plt
import sys

print("Iniciando Backtest com múltiplos MA...")

client = get_client()

klines = client.get_historical_klines(
    SYMBOL,
    "5m",
    "5 days ago UTC"
)

prices = [float(kline[4]) for kline in klines]

# =========================
# FUNÇÃO DE BACKTEST
# =========================
def run_backtest(MA_PERIOD, save_history=False):

    capital = 1000
    capital_history = [capital]
    max_capital = capital
    max_drawdown = 0

    in_position = False
    entry_price = 0
    quantity = 0
    trades = []
    wins = 0
    losses = 0
    price_history = []

    for current_price in prices:

        price_history.append(current_price)

        if len(price_history) > MA_PERIOD:
            price_history.pop(0)

        if len(price_history) < MA_PERIOD:
            continue

        moving_average = sum(price_history) / MA_PERIOD

        # SAÍDA
        if in_position:

            gross_value = quantity * current_price
            sell_fee = gross_value * SELL_FEE
            net_value = gross_value - sell_fee

            invested = entry_price * quantity
            result = net_value - invested

            variation = (result / invested) * 100

            if variation >= TAKE_PROFIT or variation <= STOP_LOSS:

                capital += result

                if save_history:
                    capital_history.append(capital)

                if capital > max_capital:
                    max_capital = capital

                drawdown = (max_capital - capital) / max_capital * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

                trades.append(result)

                if result > 0:
                    wins += 1
                else:
                    losses += 1

                in_position = False

        # ENTRADA
        if not in_position and current_price > moving_average:

            position_value = capital * POSITION_PERCENT
            buy_fee = position_value * BUY_FEE
            net_investment = position_value - buy_fee

            quantity = net_investment / current_price
            entry_price = current_price
            in_position = True

    total_trades = len(trades)
    total_profit = sum(trades)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    return {
        "MA": MA_PERIOD,
        "Capital_Final": capital,
        "Lucro": total_profit,
        "WinRate": win_rate,
        "Drawdown": max_drawdown,
        "Trades": total_trades,
        "History": capital_history
    }

# =========================
# TESTAR VÁRIOS MA
# =========================
ma_values = [5, 10, 15, 20, 30, 50]
results = []

for ma in ma_values:
    result = run_backtest(ma)
    results.append(result)

# Ordenar do melhor para o pior
results.sort(key=lambda x: x["Capital_Final"], reverse=True)

print("\n========== RANKING DE MÉDIAS ==========\n")

for r in results:
    print(
        f"MA {r['MA']} | "
        f"Capital: {r['Capital_Final']:.2f} | "
        f"Lucro: {r['Lucro']:.2f} | "
        f"WinRate: {r['WinRate']:.2f}% | "
        f"Drawdown: {r['Drawdown']:.2f}% | "
        f"Trades: {r['Trades']}"
    )

best_ma = results[0]["MA"]

print(f"\n🏆 Melhor MA encontrado: {best_ma}\n")

# =========================
# RODAR NOVAMENTE O MELHOR MA (COM HISTÓRICO)
# =========================
best_result = run_backtest(best_ma, save_history=True)
capital_history = best_result["History"]

# =========================
# GRÁFICO BONITO
# =========================
plt.style.use("dark_background")
plt.figure(figsize=(12, 6))

# Área verde/vermelha
for i in range(1, len(capital_history)):
    if capital_history[i] >= capital_history[i - 1]:
        plt.fill_between(
            [i - 1, i],
            [capital_history[i - 1], capital_history[i]],
            color="green",
            alpha=0.3
        )
    else:
        plt.fill_between(
            [i - 1, i],
            [capital_history[i - 1], capital_history[i]],
            color="red",
            alpha=0.3
        )

plt.plot(capital_history, color="cyan", linewidth=2, label="Capital")

plt.title("Evolucao do Capital - Melhor MA", fontsize=14)
plt.xlabel("Trades")
plt.ylabel("Capital (R$)")
plt.grid(True, linestyle="--", alpha=0.3)
plt.legend()

plt.tight_layout()
plt.savefig("resultado.png", dpi=300)
plt.close()

print("Grafico salvo como resultado.png")
