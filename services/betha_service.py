"""
services/betha_service.py

Cliente HTTP genérico para a API Betha.
Usa exclusivamente as funções do config.loaders para credenciais e endpoints.
"""
import requests
from config.loaders import get_config, get_endpoint, Endpoint
from services.logger_service import logger


def _get_headers() -> dict:
    return {
        "Authorization": get_config("betha", "api", "authorization"),
        "user-access":   get_config("betha", "api", "user_access"),
        "Accept":        "application/json",
    }


def _montar_url(endpoint: str) -> str:
    """
    Aceita tanto um valor raw (ex: 'afastamento') quanto um
    Endpoint enum (ex: Endpoint.BETHA_AFASTAMENTOS).
    """
    if isinstance(endpoint, Endpoint):
        endpoint = get_endpoint(endpoint)

    base = get_config("betha", "api", "base_url").rstrip("/")
    return f"{base}/{endpoint.lstrip('/')}"


def get(endpoint, params: dict = None, timeout: int = 30) -> dict:
    """GET autenticado na API Betha."""
    url = _montar_url(endpoint)
    response = requests.get(url=url, headers=_get_headers(), params=params, timeout=timeout)

    if response.status_code == 403:
        raise PermissionError("403 Forbidden — token/user-access inválido ou expirado.")

    response.raise_for_status()
    return response.json()


def paginar(endpoint, params: dict = None, limit: int = 1000) -> list:
    """Percorre todas as páginas e retorna a lista completa do campo 'content'."""
    params = dict(params or {})
    params["limit"] = limit
    offset = 0
    todos = []

    while True:
        params["offset"] = offset
        data = get(endpoint, params=params)
        todos.extend(data.get("content", []))
        logger.info(f"[betha_service] {offset + limit} registros acumulados...")

        if not data.get("hasNext"):
            break

        offset += limit

    return todos