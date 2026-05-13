import time
import csv
from datetime import datetime
from logger import logger
from config import get_client
from market import get_price
from settings import (
    SYMBOL,
    INTERVAL,
    STOP_LOSS,
    TAKE_PROFIT,
    INITIAL_CAPITAL,
    POSITION_PERCENT,
    COOLDOWN_CYCLES,
    MA_PERIOD,
    EXIT_CONFIRMATION_CYCLES,
    BUY_FEE,
    SELL_FEE,
)

logger.info("Bot iniciado (VERSÃO COMPLETA PROFISSIONAL)")

# =========================
# CRIA ARQUIVO CSV
# =========================
with open("trades.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "Data",
        "Tipo",
        "Entrada",
        "Saida",
        "Resultado_R$",
        "Capital_Apos"
    ])

def save_trade(trade_type, entry, exit_price, result, capital):
    with open("trades.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            trade_type,
            entry,
            exit_price,
            result,
            capital
        ])

client = get_client()

if client is None:
    logger.error("Não foi possível conectar à Binance.")
    exit()

# =========================
# ESTADO DO BOT
# =========================
capital = INITIAL_CAPITAL
in_position = False
entry_price = None
quantity = 0.0
cooldown = 0
below_ma_counter = 0
prices = []

trades = []
wins = 0
losses = 0

try:
    while True:

        if cooldown > 0:
            cooldown -= 1
            logger.info(f"Cooldown: {cooldown}")

        current_price = get_price(client, SYMBOL)
        

        if current_price is None:
            time.sleep(INTERVAL)
            continue

        prices.append(current_price)

        if len(prices) > MA_PERIOD:
            prices.pop(0)

        if len(prices) < MA_PERIOD:
            logger.info("Aguardando dados da média...")
            time.sleep(INTERVAL)
            continue

        moving_average = sum(prices) / MA_PERIOD

        logger.info(
            f"Preço: {current_price:.4f} | Média ({MA_PERIOD}): {moving_average:.4f}"
        )

        # =========================
        # SE ESTIVER EM POSIÇÃO
        # =========================
        if in_position:

            gross_value = quantity * current_price
            sell_fee_value = gross_value * SELL_FEE
            net_value = gross_value - sell_fee_value

            invested_value = entry_price * quantity
            result = net_value - invested_value

            if invested_value != 0:
                position_variation = (result / invested_value) * 100
            else:
                position_variation = 0

            logger.info(
                f"Resultado real: {position_variation:.2f}% | R$ {result:.2f}"
            )

            # TAKE PROFIT
            if position_variation >= TAKE_PROFIT:
                capital += result
                trades.append(result)
                wins += 1
                in_position = False
                cooldown = COOLDOWN_CYCLES
                below_ma_counter = 0

                save_trade(
                    "TAKE_PROFIT",
                    entry_price,
                    current_price,
                    result,
                    capital
                )

                logger.warning(
                    f"🟢 TAKE PROFIT | Capital: R$ {capital:.2f}"
                )

            # STOP LOSS
            elif position_variation <= STOP_LOSS:
                capital += result
                trades.append(result)
                losses += 1
                in_position = False
                cooldown = COOLDOWN_CYCLES
                below_ma_counter = 0

                save_trade(
                    "STOP_LOSS",
                    entry_price,
                    current_price,
                    result,
                    capital
                )

                logger.warning(
                    f"🔴 STOP LOSS | Capital: R$ {capital:.2f}"
                )

            else:
                # CONFIRMAÇÃO DE SAÍDA POR MÉDIA
                if current_price < moving_average:
                    below_ma_counter += 1
                    logger.info(
                        f"Abaixo da média ({below_ma_counter}/{EXIT_CONFIRMATION_CYCLES})"
                    )
                else:
                    below_ma_counter = 0

                if below_ma_counter >= EXIT_CONFIRMATION_CYCLES:
                    capital += result
                    trades.append(result)
                    in_position = False
                    cooldown = COOLDOWN_CYCLES
                    below_ma_counter = 0

                    save_trade(
                        "MEDIA_EXIT",
                        entry_price,
                        current_price,
                        result,
                        capital
                    )

                    logger.warning(
                        f"🔴 SAÍDA CONFIRMADA POR MÉDIA | Capital: R$ {capital:.2f}"
                    )

        # =========================
        # ENTRADA
        # =========================
        if (
            not in_position
            and cooldown == 0
            and current_price > moving_average
        ):
            position_value = capital * POSITION_PERCENT

            buy_fee_value = position_value * BUY_FEE
            net_investment = position_value - buy_fee_value

            quantity = net_investment / current_price
            entry_price = current_price
            in_position = True

            logger.warning(
                f"🟢 ENTRADA | Preço: {entry_price:.4f} | Investido: R$ {net_investment:.2f}"
            )

        time.sleep(INTERVAL)

except KeyboardInterrupt:

    total_trades = len(trades)
    total_profit = sum(trades)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    logger.info("========== RELATÓRIO FINAL ==========")
    logger.info(f"Capital final: R$ {capital:.2f}")
    logger.info(f"Trades: {total_trades}")
    logger.info(f"Vitórias: {wins}")
    logger.info(f"Derrotas: {losses}")
    logger.info(f"Win rate: {win_rate:.2f}%")
    logger.info(f"Lucro total: R$ {total_profit:.2f}")
