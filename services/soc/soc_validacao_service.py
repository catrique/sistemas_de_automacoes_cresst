import random
import re

import pandas as pd
import requests

from config.loaders import get_config, reload_settings
from services.logger_service import logger

def validar_cpf_4devs(cpf) -> str:
    """
    Valida CPF via API 4devs.
    Retorna 'Verdadeiro', 'Falso', 'Inválido' ou 'Erro'.
    """
    if not cpf or (isinstance(cpf, float) and pd.isna(cpf)):
        return "Inválido"
    try:
        url = "https://www.4devs.com.br/ferramentas_online.php"
        payload = {"acao": "validar_cpf", "txt_cpf": re.sub(r"\D", "", str(cpf))}
        resp = requests.post(url, data=payload, timeout=10)
        return "Verdadeiro" if "Verdadeiro" in resp.text else "Falso"
    except Exception as e:
        logger.warning(f"Erro ao validar CPF: {e}")
        return "Erro"


def validar_email(email) -> str:
    """
    Valida o formato do e-mail por expressão regular.
    Retorna 'Válido' ou 'Inválido'.
    """
    if not email or (isinstance(email, float) and pd.isna(email)):
        return "Inválido"
    padrao = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return "Válido" if re.match(padrao, str(email).strip()) else "Inválido"


def matricula_eh_valida(matricula) -> bool:
    """Verifica se a matrícula tem formato numérico válido (ex.: 99001234 ou 99001234/1)."""
    if not matricula:
        return False
    return bool(re.match(r"^\d{5,10}(/\d+)?$", str(matricula).strip()))


def incrementar_matricula(matricula) -> str | None:
    """
    Incrementa o sufixo após '/' em uma matrícula.
    Se não houver '/', adiciona '/1'.
    Retorna None para matrículas vazias ou inválidas.
    """
    if not matricula or (isinstance(matricula, float) and pd.isna(matricula)):
        return None
    m = str(matricula).strip()
    if m in ("-", ""):
        return None
    if "/" in m:
        partes = m.split("/")
        try:
            return f"{partes[0]}/{int(partes[1]) + 1}"
        except Exception:
            return f"{m}/1"
    return f"{m}/1"


def formatar_matricula_invalida(cpf) -> str:
    """
    Gera uma matrícula temporária no formato 'CPF:XXXXXX' para linhas sem matrícula válida.
    """
    cpf_limpo = re.sub(r"\D", "", str(cpf))
    sufixo = f"{random.randint(0, 999):03d}"
    return f"CPF:{cpf_limpo[:6]}{sufixo}"


def _get_betha_headers() -> dict:
    """Monta os headers de autenticação lendo do settings via loaders."""
    reload_settings()
    return {
        "Authorization": get_config("betha", "api", "authorization") or "",
        "Content-Type":  "application/json",
        "User-Access":   get_config("betha", "api", "user_access") or "",
    }


def _get_betha_base_url() -> str:
    return get_config("betha", "api", "base_url")


def _get_endpoint_listagem() -> str:
    return get_config("betha", "api", "endpoints", "listagem_matricula")

def verificar_existencia_betha(termo: str) -> bool:
    """
    Retorna True se a matrícula já existe no sistema Betha.
    Monta a query a partir do formato 'numero' ou 'numero/contrato'.
    """
    url = f"{_get_betha_base_url()}{_get_endpoint_listagem()}"

    if "/" in str(termo):
        numero, contrato = str(termo).split("/", 1)
        filtro = f'codigo.numero = "{numero}" and codigo.contrato = "{contrato}"'
    else:
        filtro = f'codigo.numero = "{termo}"'

    params = {"filter": filtro, "filtroSituacao": "TODOS", "limit": 1}

    try:
        resp = requests.get(url, headers=_get_betha_headers(), params=params, timeout=20)
        if resp.status_code == 200:
            return len(resp.json().get("content", [])) > 0
        logger.warning(f"Betha retornou status {resp.status_code} para matrícula '{termo}'.")
        return False
    except Exception as e:
        logger.error(f"Erro ao consultar Betha para matrícula '{termo}': {e}")
        return False


def validar_planilha(excel_path: str) -> pd.DataFrame | None:
    """
    Valida e corrige a planilha de funcionários:
        - E-mails  → minúsculo
        - Nomes    → CAIXA ALTA
        - CPF      → validado via 4devs
        - E-mail   → validado por regex
        - Matrícula → verificada/incrementada via API Betha

    Salva o progresso a cada 5 registros e grava o resultado final.
    Retorna o DataFrame corrigido ou None em caso de erro de leitura.
    """
    try:
        df = pd.read_excel(excel_path)
        logger.info(f"Planilha carregada: {len(df)} registros.")
    except Exception as e:
        logger.error(f"Erro ao ler planilha: {e}")
        return None

    if "E-mail" in df.columns:
        df["E-mail"] = df["E-mail"].astype(str).str.lower().str.strip().replace("nan", "")
        logger.info("E-mails convertidos para minúsculo.")

    if "Nome" in df.columns:
        df["Nome"] = df["Nome"].astype(str).str.upper().str.strip().replace("NAN", "")
        logger.info("Nomes convertidos para CAIXA ALTA.")

    for col in ("CPF Válido", "Email Válido"):
        if col not in df.columns:
            df[col] = ""

    for idx, row in df.iterrows():
        cpf            = row.get("CPF")
        email          = row.get("E-mail")
        matricula_orig = row.get("Matrícula Anterior", "")

        logger.info(f"[{idx + 1}/{len(df)}] Processando: {row.get('Nome', cpf)}")

        df.at[idx, "CPF Válido"]   = validar_cpf_4devs(cpf)
        df.at[idx, "Email Válido"] = validar_email(email)

        if not matricula_eh_valida(matricula_orig):
            nova = formatar_matricula_invalida(cpf)
            logger.warning(f"Matrícula inválida — ajustada para: {nova}")
        else:
            tentativa = incrementar_matricula(matricula_orig)
            while True:
                logger.info(f"Verificando matrícula: {tentativa}")
                if verificar_existencia_betha(tentativa):
                    logger.info(f"Matrícula {tentativa} já existe. Incrementando...")
                    tentativa = incrementar_matricula(tentativa)
                else:
                    nova = tentativa
                    logger.info(f"Matrícula disponível: {nova}")
                    break

        df.at[idx, "Matrícula Anterior"] = nova

        if (idx + 1) % 5 == 0:
            try:
                df.to_excel(excel_path, index=False, engine="openpyxl")
                logger.info("Progresso salvo.")
            except PermissionError:
                logger.warning("Planilha aberta — não foi possível salvar progresso.")
            except Exception as e:
                logger.warning(f"Erro ao salvar progresso: {e}")

    try:
        df.to_excel(excel_path, index=False, engine="openpyxl")
        logger.info("Validação concluída e planilha salva.")
    except Exception as e:
        logger.error(f"Erro ao salvar planilha final: {e}")

    return df