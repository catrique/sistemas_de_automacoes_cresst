"""
services/esocial_service.py

Cliente HTTP para a API eSocial Betha.
Todas as funções são independentes — a orquestração fica em revalidar_pendentes.py.
"""
import requests
from config.loaders import get_config
from services.logger_service import logger



def _get_headers() -> dict:
    return {
        "Authorization": get_config("betha", "api", "authorization"),
        "user-access":   get_config("betha", "api", "esocial", "user_access"),
        "Accept":        "application/json",
        "Content-Type":  "application/json",
    }


def _get_base_url() -> str:
    return get_config("betha", "api", "esocial", "base_url").rstrip("/")


def _get_endpoint(chave: str) -> str:
    return get_config("betha", "api", "esocial", "endpoints", chave)



def buscar_pendentes(limit: int = 1000) -> list:
    """
    Busca todos os registros PENDENTES dos domínios configurados, paginando
    automaticamente até esgotar os resultados.

    Retorna a lista bruta de objetos da API.
    """
    endpoint  = _get_endpoint("pendentes")
    url       = f"{_get_base_url()}/{endpoint.lstrip('/')}"
    filtro    = (
        '(configuracaoDominio in ("655225c404c3c5000181bbb8") '
        'or configuracaoDominio in ("655225c404c3c5000181bbae") '
        'or configuracaoDominio in ("655225c404c3c5000181bbb6") '
        'or configuracaoDominio in ("655225c404c3c5000181bbba")) '
        'and situacao="PENDENTE"'
    )

    todos  = []
    offset = 0

    while True:
        params = {
            "filter": filtro,
            "limit":  limit,
            "offset": offset,
            "sort":   "codigo asc",
        }

        response = requests.get(url=url, headers=_get_headers(), params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        conteudo = data.get("content", [])
        todos.extend(conteudo)

        logger.info(f"[esocial_service] buscar_pendentes — {len(todos)} registros acumulados...")

        if not data.get("hasNext"):
            break

        offset += limit

    return todos



def tratar_pendentes(lista_bruta: list) -> list:
    """
    Recebe a lista bruta de buscar_pendentes() e retorna uma lista simplificada.

    Cada item: { id, situacao, situacaoEsocial, descricao, vigenteDesde }
    """
    return [
        {
            "id":              item["id"],
            "situacao":        item.get("situacao"),
            "situacaoEsocial": item.get("situacaoEsocial"),
            "descricao":       item.get("descricao"),
            "vigenteDesde":    item.get("vigenteDesde"),
        }
        for item in lista_bruta
    ]



def buscar_historico_dominio(dominio_id: str, limit: int = 100) -> list:
    """
    Busca o histórico de versões de um domínio específico pelo seu id.

    Retorna a lista bruta de objetos do histórico.
    """
    endpoint = _get_endpoint("historico_dominio")
    url      = f"{_get_base_url()}/{endpoint.lstrip('/')}"

    params = {
        "filter":  f'dominio="{dominio_id}"',
        "hasNext": "true",
        "limit":   limit,
        "offset":  0,
        "sort":    "vigencia desc",
    }

    response = requests.get(url=url, headers=_get_headers(), params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if isinstance(data, list):
        return data
    return data.get("content", [])



def tratar_historico(lista_bruta: list) -> list:
    """
    Recebe a lista bruta de buscar_historico_dominio() e retorna uma lista simplificada.

    Cada item: { id, situacaoEsocial, vigencia }
    """
    return [
        {
            "id":              item["id"],
            "situacaoEsocial": item.get("situacaoEsocial"),
            "vigencia":        item.get("vigencia"),
        }
        for item in lista_bruta
    ]



def revalidar(historico_id: str) -> bool:
    """
    Envia uma requisição POST para revalidar um item do histórico pelo seu id.

    Retorna True se a API respondeu com 200, False caso contrário.
    """
    endpoint = _get_endpoint("revalidar")
    url      = f"{_get_base_url()}/{endpoint.lstrip('/')}"

    params   = {"id": historico_id}

    response = requests.post(
        url=url, headers=_get_headers(), params=params, timeout=30)

    if response.status_code == 200:
        logger.info(f"[esocial_service] revalidar — OK: {historico_id}")
        return True

    logger.warning(
        f"[esocial_service] revalidar — status {response.status_code}: {historico_id}")
    return False