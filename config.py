import os
from dotenv import load_dotenv
from binance.client import Client
from logger import logger

load_dotenv()

def get_client():
    try:
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")

        if not api_key or not api_secret:
            logger.error("API KEY ou SECRET não encontrados no .env")
            return None

        logger.info("Cliente Binance criado com sucesso")

        return Client(api_key, api_secret)

    except Exception as error:
        logger.error(f"Erro ao criar cliente: {error}")
        return None