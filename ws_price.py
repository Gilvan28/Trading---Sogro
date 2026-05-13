from binance import ThreadedWebsocketManager
import time

prices = {}

twm = ThreadedWebsocketManager()
twm.start()

def handle(msg):
    try:
        if msg.get('e') != '24hrMiniTicker':
            return

        symbol = msg['s']
        price = float(msg['c'])

        prices[symbol] = price

    except Exception as e:
        print("Erro WS:", e)

# 🔥 stream global (todas moedas)
twm.start_miniticker_socket(callback=handle)

print("🔥 WebSocket rodando...")

# 🔥 SEGREDO: manter vivo
while True:
    time.sleep(1)