from logger import logger

def get_balances(client):
    try:
        logger.info("Buscando saldos da conta")

        account = client.get_account()
        balances = []

        for asset in account["balances"]:
            if float(asset["free"]) > 0:
                balances.append(asset)

        return balances

    except Exception as error:
        logger.error(f"Erro ao buscar saldos: {error}")
        return []
