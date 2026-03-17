"""
services/exportar_service.py

Funções genéricas de exportação: checkpoint, persistência em Excel
e extração de linhas de tabela. Sem nenhuma dependência de Selenium.
"""
import os
import pandas as pd
from services.logger_service import logger


class SessionExpired(Exception):
    """Sinaliza que a sessão do SOC expirou e é preciso refazer login."""
    pass


def load_checkpoint(checkpoint_file: str) -> tuple[int, int]:
    """Lê página e índice salvos. Retorna (1, 0) se não existir."""
    if os.path.exists(checkpoint_file):
        try:
            page, idx = open(checkpoint_file).read().split(',')
            logger.info(f"Checkpoint encontrado: Página {page}, Item {int(idx)+1}.")
            return int(page), int(idx)
        except Exception:
            logger.warning("Checkpoint corrompido. Iniciando do zero.")
    return 1, 0


def save_checkpoint(checkpoint_file: str, page: int, index: int) -> None:
    with open(checkpoint_file, 'w') as f:
        f.write(f"{page},{index}")


def clear_checkpoint(checkpoint_file: str) -> None:
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        logger.info("Checkpoint limpo.")


def save_to_excel(log_data: list, colunas: list, log_file: str) -> None:
    """Acumula dados no Excel existente (ou cria novo se não existir)."""
    if not log_data:
        return

    df_novo = pd.DataFrame(log_data, columns=colunas)

    if os.path.exists(log_file):
        try:
            df_novo = pd.concat([pd.read_excel(log_file), df_novo], ignore_index=True)
        except Exception:
            pass

    try:
        df_novo.to_excel(log_file, index=False)
        logger.info(f"Dados salvos em: {log_file}")
    except Exception as e:
        logger.error(f"Erro ao salvar Excel: {e}")


def extrair_celulas(row_element, seletores: dict) -> dict:
    """
    Extrai texto de células de uma linha de tabela.

    seletores: dict mapeando nome do campo -> XPath relativo à linha.
    Retorna dict com os valores encontrados (ou "N/A" em caso de falha).

    Exemplo:
        extrair_celulas(row, {
            "Nome":  "./td[2]//div[@class='nome-funcionario-registrado']",
            "Cargo": "./td[5]",
        })
    """
    resultado = {}
    for campo, xpath in seletores.items():
        try:
            resultado[campo] = row_element.find_element("xpath", xpath).text.strip()
        except Exception:
            resultado[campo] = "N/A"
    return resultado