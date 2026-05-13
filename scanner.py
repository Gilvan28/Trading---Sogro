from config import get_client
import statistics

client = get_client()

MA_PERIOD = 20
INTERVAL = "5m"
CANDLE_LIMIT = 50


def get_hot_coins():

    try:
        tickers = client.get_ticker()

        if isinstance(tickers, dict):
            tickers = [tickers]

        usdt = [t for t in tickers if t["symbol"].endswith("USDT")]

        top = sorted(
            usdt,
            key=lambda x: float(x.get("quoteVolume", 0)),
            reverse=True
        )[:20]

        signals = []

        for t in top:

            symbol = t["symbol"]

            try:
                klines = client.get_klines(symbol=symbol, interval=INTERVAL, limit=CANDLE_LIMIT)
                closes = [float(k[4]) for k in klines]

                if len(closes) < MA_PERIOD:
                    continue

                ma = sum(closes[-MA_PERIOD:]) / MA_PERIOD
                price = closes[-1]
                variation = ((price - closes[-5]) / closes[-5]) * 100
                vol = statistics.stdev(closes[-MA_PERIOD:])

                if price > ma and variation > 0.5:

                    score = (variation * 0.8) - (vol * 0.2)

                    signals.append({
                        "symbol": symbol,
                        "price": price,
                        "variation": variation,
                        "score": score
                    })

            except:
                continue

        signals.sort(key=lambda x: x["score"], reverse=True)

        return signals[:10]

    except Exception as e:
        print("Erro scanner:", e)
        return []
    