import os
import argparse
from datetime import date

from config.loaders import get_workspace
from services.logger_service import logger
from services.sheets_service import SheetsService
from services.soc.relatorios_service import save_to_excel
from services.soc.soc_services import fluxo_acesso_completo_soc
from services.soc.soc_retorno_ao_trabalho_service import (
    navegar_para_consultar_agendamentos,
    abrir_modal_filtro,
    selecionar_tipo_retorno_ao_trabalho,
    aplicar_filtro_modal,
    preencher_data_pesquisa,
    executar_pesquisa,
    extrair_linhas_tabela,
)

COLUNAS = [
    "Data",
    "Hora",
    "Tipo de Compromisso",
    "Nome",
    "CPF",
    "Unidade",
    "Setor",
    "Cargo",
    "Atendido",
]

SUBPASTA_RELATORIO = os.path.join("relatorios", "retorno_ao_trabalho")

def gerar_relatorio_retorno_ao_trabalho(data_pesquisa: str = None) -> None:
    """
    Executa o fluxo completo de extração e salva o resultado em Excel.

    Args:
        data_pesquisa: Data no formato 'DD/MM/AAAA'. Se None, usa hoje.
    """
    if data_pesquisa is None:
        data_pesquisa = date.today().strftime("%d/%m/%Y")

    diretorio_saida = get_workspace(SUBPASTA_RELATORIO)
    os.makedirs(diretorio_saida, exist_ok=True)

    data_arquivo = data_pesquisa.replace("/", "-")
    nome_arquivo = f"retorno_ao_trabalho_{data_arquivo}.xlsx"
    caminho_excel = os.path.join(diretorio_saida, nome_arquivo)

    driver = None
    try:
        logger.info(f"🚀 Iniciando relatório de Retorno ao Trabalho — {data_pesquisa}")
        logger.info(f"📁 Destino: {caminho_excel}")

        driver, wait = fluxo_acesso_completo_soc()

        navegar_para_consultar_agendamentos(driver, wait)

        abrir_modal_filtro(driver, wait)
        selecionar_tipo_retorno_ao_trabalho(driver, wait)
        aplicar_filtro_modal(driver, wait)

        preencher_data_pesquisa(driver, wait, data=data_pesquisa)
        executar_pesquisa(driver, wait)

        registros = extrair_linhas_tabela(driver, wait)

        if not registros:
            logger.warning("⚠️  Nenhum registro encontrado para a data informada.")
        else:
            service = SheetsService()
            save_to_excel(registros, COLUNAS, caminho_excel)
            logger.info(
                f"✅ Relatório gerado com {len(registros)} registro(s): {caminho_excel}"
            )

            service.atualizar_planilha_mestra(caminho_excel);

    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}", exc_info=True)

    finally:
        if driver:
            driver.quit()
            logger.info("Driver encerrado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gera relatório de Retorno ao Trabalho do SOC."
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Data de pesquisa no formato DD/MM/AAAA (padrão: hoje)",
    )
    args = parser.parse_args()

    gerar_relatorio_retorno_ao_trabalho(data_pesquisa=args.data)