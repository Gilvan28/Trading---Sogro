from logger import logger

def get_price(client, symbol):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        price = float(ticker["price"])
        return price

    except Exception as error:
        logger.error(f"Erro ao buscar preço de {symbol}: {error}")
        return None