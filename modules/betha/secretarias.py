"""
modules/betha/secretarias.py

Busca as lotações na API Betha e salva o dicionário de secretarias
como JSON em workspace/relatorios/secretarias.json.
"""
from config.loaders import Endpoint
from services.betha_service import paginar
from services.utils.secretarias_service import montar_dicionario, salvar_secretarias
from services.logger_service import logger


def executar() -> dict:
    """
    Busca todas as lotações, monta o dicionário hierárquico e salva em JSON.
    Retorna o dicionário gerado.
    """
    logger.info("Buscando lotações na API Betha...")
    lotacoes = paginar(Endpoint.BETHA_LOTACAO_FISICA, params={
        "filter": '(numero like "%25%25" or descricao like "%25%25")'
    })

    dicionario = montar_dicionario(lotacoes)
    salvar_secretarias(dicionario)

    logger.info(f"✅ {len(dicionario)} secretarias salvas em JSON.")
    return dicionario


if __name__ == "__main__":
    executar()