"""
services/utils/secretarias_service.py

Utilitários para carregar, salvar e buscar no JSON de secretarias.
O arquivo secretarias.json fica em config/secretarias.json.
"""
import json
import os
from collections import defaultdict

# Caminho fixo: config/ na raiz do projeto
_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SECRETARIAS_JSON = os.path.join(_BASE, "config", "secretarias.json")


def json_disponivel() -> bool:
    """Retorna True somente se o caminho for um arquivo (nunca uma pasta)."""
    return os.path.isfile(SECRETARIAS_JSON)


def carregar_secretarias() -> dict:
    if not json_disponivel():
        return {}
    with open(SECRETARIAS_JSON, encoding="utf-8") as f:
        return json.load(f)


def salvar_secretarias(dicionario: dict) -> None:
    pasta = os.path.dirname(SECRETARIAS_JSON)
    os.makedirs(pasta, exist_ok=True)   # garante só a pasta pai (config/)
    with open(SECRETARIAS_JSON, "w", encoding="utf-8") as f:
        json.dump(dicionario, f, ensure_ascii=False, indent=2)


def buscar_por_texto(termo: str, secretarias: dict = None) -> dict:
    if secretarias is None:
        secretarias = carregar_secretarias()

    termo = termo.upper()
    resultados = {}

    for cod, dados in secretarias.items():
        if termo in dados["descricao"].upper():
            resultados[cod] = dados
            continue
        lotacoes = [l for l in dados["lotacoes"] if termo in l["descricao"].upper()]
        if lotacoes:
            resultados[cod] = {"descricao": dados["descricao"], "lotacoes": lotacoes}

    return resultados


def montar_dicionario(lotacoes: list) -> dict:
    secretarias = {}
    filhos = defaultdict(list)

    for item in lotacoes:
        numero = item.get("numeroMascarado")
        if not numero:
            continue
        partes = numero.split(".")
        if len(partes) == 2:
            secretarias[numero] = {"descricao": item["descricao"], "lotacoes": []}
        elif len(partes) > 2:
            filhos[f"{partes[0]}.{partes[1]}"].append(item)

    for codigo, itens in filhos.items():
        if codigo not in secretarias:
            continue
        for item in sorted(itens, key=lambda x: x["numeroMascarado"]):
            secretarias[codigo]["lotacoes"].append({
                "numero":    item["numeroMascarado"],
                "descricao": item["descricao"],
            })

    return secretarias