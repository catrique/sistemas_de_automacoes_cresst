import pandas as pd

from config.loaders import get_workspace
from services.logger_service import logger
from services.soc.soc_services import fluxo_acesso_completo_soc
from services.soc.soc_cadastro_service import (
    acessar_area_agendamentos,
    acessar_area_funcionarios,
    agendar_admissional,
    agendar_demissional,
    agendar_periodico,
    cadastrar_funcionario,
    clicar_cancelar,
    garantir_frame_principal,
)
from services.soc.soc_validacao_service import validar_planilha

# Colunas obrigatórias por fluxo
_COLUNAS_CADASTRO     = ["Nome", "Data Nascimento", "Data Admissão", "CPF",
                          "Sexo", "Matrícula Anterior", "E-mail", "Cargo", "Lotação"]
_COLUNAS_ADMISSIONAL  = ["Nome", "Matrícula Anterior", "E-mail", "Data Exame", "Hora Exame"]
_COLUNAS_PERIODICO    = ["Nome", "Matrícula", "Exames", "Hora"]
_COLUNAS_DEMISSIONAL  = ["Nome", "Matrícula Anterior", "Data Exame"]


def _carregar_planilha(excel_path: str, colunas_req: list[str]) -> pd.DataFrame | None:
    """Carrega o Excel e valida se as colunas necessárias estão presentes."""
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        logger.error(f"Erro ao carregar planilha '{excel_path}': {e}")
        return None

    faltando = [c for c in colunas_req if c not in df.columns]
    if faltando:
        logger.error(f"Colunas faltando na planilha: {', '.join(faltando)}")
        return None

    logger.info(f"Planilha carregada: {len(df)} registros.")
    return df


def _salvar_planilha(df: pd.DataFrame, excel_path: str, nome_aba: str = None) -> None:
    """Salva o DataFrame no Excel, com suporte opcional a aba específica."""
    try:
        if nome_aba:
            with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a",
                                if_sheet_exists="replace") as writer:
                df.to_excel(writer, sheet_name=nome_aba, index=False)
        else:
            df.to_excel(excel_path, index=False)
        logger.info(f"Planilha salva: {excel_path}")
    except PermissionError:
        logger.warning("Planilha aberta por outro processo — feche-a e tente novamente.")
    except Exception as e:
        logger.error(f"Erro ao salvar planilha: {e}")


def _ja_processado(row: dict, coluna: str) -> bool:
    """Retorna True se a linha já foi processada (coluna não está vazia)."""
    val = row.get(coluna)
    return pd.notna(val) and str(val).strip() not in ("", "nan")


def executar_validacao_planilha(excel_path: str) -> None:
    """
    Valida e corrige a planilha sem abrir o navegador:
    e-mails, nomes, CPF, e-mail e matrículas via API Betha.
    """
    logger.info("=== INICIANDO: Validação de Planilha ===")
    resultado = validar_planilha(excel_path)
    if resultado is not None:
        logger.info(f"=== CONCLUÍDO: {len(resultado)} registros validados. ===")
    else:
        logger.error("=== FALHA: Validação encerrada com erro. ===")

def executar_cadastro_funcionarios(excel_path: str,
                                    diretorio_download: str = None) -> None:
    """
    Cadastra os funcionários listados na planilha no sistema SOC.
    Pula registros já cadastrados (detectados por erro no SOC) e gera
    um arquivo de erros de lotação/cargo ao final.
    """
    logger.info("=== INICIANDO: Cadastro de Funcionários ===")

    df = _carregar_planilha(excel_path, _COLUNAS_CADASTRO)
    if df is None:
        return

    driver, wait = fluxo_acesso_completo_soc(diretorio_customizado=diretorio_download)

    try:
        acessar_area_funcionarios(driver, wait)
        erros_lotacao = []

        for idx, row in df.iterrows():
            logger.info(f"[{idx + 1}/{len(df)}] Cadastrando: {row['Nome']}")
            try:
                sucesso = cadastrar_funcionario(driver, wait, row.to_dict())
                if not sucesso:
                    erros_lotacao.append({
                        "Nome":    row["Nome"],
                        "CPF":     row["CPF"],
                        "Cargo":   row.get("Cargo", ""),
                        "Lotação": row.get("Lotação", ""),
                        "Motivo":  "Cargo ou Lotação não encontrado",
                    })
            except Exception as e:
                logger.error(f"Erro crítico ao cadastrar {row['Nome']}: {e}")
                try:
                    clicar_cancelar(driver, wait)
                except Exception:
                    pass

        if erros_lotacao:
            erros_path = excel_path.replace(".xlsx", "_Erros_Lotacao.xlsx")
            pd.DataFrame(erros_lotacao).to_excel(erros_path, index=False)
            logger.warning(f"{len(erros_lotacao)} erro(s) de lotação salvos em: {erros_path}")

    finally:
        driver.quit()
        logger.info("=== CONCLUÍDO: Cadastro de Funcionários ===")


def executar_agendamento_admissional(excel_path: str,
                                      diretorio_download: str = None) -> None:
    """
    Agenda exames admissionais para os funcionários da planilha.
    Pula registros com 'Hora Agendada' já preenchida.
    Salva o horário agendado na planilha após cada registro bem-sucedido.
    """
    logger.info("=== INICIANDO: Agendamento Admissional ===")

    df = _carregar_planilha(excel_path, _COLUNAS_ADMISSIONAL)
    if df is None:
        return

    if "Hora Agendada" not in df.columns:
        df["Hora Agendada"] = None

    driver, wait = fluxo_acesso_completo_soc(diretorio_customizado=diretorio_download)

    try:
        acessar_area_agendamentos(driver, wait)
        janela_principal = driver.current_window_handle

        for idx, row in df.iterrows():
            if _ja_processado(row, "Hora Agendada"):
                logger.info(f"[{idx + 1}/{len(df)}] Pulando (já agendado): {row['Nome']}")
                continue

            logger.info(f"[{idx + 1}/{len(df)}] Agendando: {row['Nome']}")
            try:
                hora = agendar_admissional(driver, wait, row.to_dict(), janela_principal)
                if hora:
                    df.at[idx, "Hora Agendada"] = hora
                    _salvar_planilha(df, excel_path)
                else:
                    logger.warning(f"Agendamento não concluído para: {row['Nome']}")
            except Exception as e:
                logger.error(f"Erro ao agendar admissional de {row['Nome']}: {e}")
                try:
                    garantir_frame_principal(driver, wait)
                    clicar_cancelar(driver, wait)
                except Exception:
                    pass

    finally:
        driver.quit()
        logger.info("=== CONCLUÍDO: Agendamento Admissional ===")



def executar_agendamento_periodico(excel_path: str, nome_aba: str = "Sheet1",
                                    diretorio_download: str = None) -> None:
    """
    Agenda exames periódicos para os funcionários da planilha.
    Pula registros com 'Hora Agendada' já preenchida.
    Salva na aba especificada por `nome_aba`.
    """
    logger.info("=== INICIANDO: Agendamento Periódico ===")

    df = _carregar_planilha(excel_path, _COLUNAS_PERIODICO)
    if df is None:
        return

    if "Hora Agendada" not in df.columns:
        df["Hora Agendada"] = None

    driver, wait = fluxo_acesso_completo_soc(diretorio_customizado=diretorio_download)

    try:
        acessar_area_agendamentos(driver, wait)
        janela_principal = driver.current_window_handle

        for idx, row in df.iterrows():
            if _ja_processado(row, "Hora Agendada"):
                logger.info(f"[{idx + 1}/{len(df)}] Pulando (já agendado): {row['Nome']}")
                continue

            logger.info(f"[{idx + 1}/{len(df)}] Agendando periódico: {row['Nome']}")
            try:
                hora = agendar_periodico(driver, wait, row.to_dict(), janela_principal)
                if hora:
                    df.at[idx, "Hora Agendada"] = hora
                    _salvar_planilha(df, excel_path, nome_aba=nome_aba)
                else:
                    logger.warning(f"Agendamento periódico não concluído para: {row['Nome']}")
            except Exception as e:
                logger.error(f"Erro ao agendar periódico de {row['Nome']}: {e}")
                try:
                    garantir_frame_principal(driver, wait)
                    clicar_cancelar(driver, wait)
                except Exception:
                    pass

    finally:
        driver.quit()
        logger.info("=== CONCLUÍDO: Agendamento Periódico ===")


def executar_agendamento_demissional(excel_path: str,
                                      diretorio_download: str = None) -> None:
    """
    Agenda exames demissionais para os funcionários da planilha.
    Pula registros com 'Hora Demissional' já preenchida.
    Salva o horário agendado na planilha após cada registro bem-sucedido.
    """
    logger.info("=== INICIANDO: Agendamento Demissional ===")

    df = _carregar_planilha(excel_path, _COLUNAS_DEMISSIONAL)
    if df is None:
        return

    if "Hora Demissional" not in df.columns:
        df["Hora Demissional"] = None

    driver, wait = fluxo_acesso_completo_soc(diretorio_customizado=diretorio_download)

    try:
        acessar_area_agendamentos(driver, wait)
        janela_principal = driver.current_window_handle

        for idx, row in df.iterrows():
            if _ja_processado(row, "Hora Demissional"):
                logger.info(f"[{idx + 1}/{len(df)}] Pulando (já agendado): {row['Nome']}")
                continue

            logger.info(f"[{idx + 1}/{len(df)}] Agendando demissional: {row['Nome']}")
            try:
                hora = agendar_demissional(driver, wait, row.to_dict(), janela_principal)
                if hora:
                    df.at[idx, "Hora Demissional"] = hora
                    _salvar_planilha(df, excel_path)
                else:
                    logger.warning(f"Agendamento demissional não concluído para: {row['Nome']}")
            except Exception as e:
                logger.error(f"Erro ao agendar demissional de {row['Nome']}: {e}")
                try:
                    garantir_frame_principal(driver, wait)
                    clicar_cancelar(driver, wait)
                except Exception:
                    pass

    finally:
        driver.quit()
        logger.info("=== CONCLUÍDO: Agendamento Demissional ===")