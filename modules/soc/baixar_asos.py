import os
from config.loaders import get_workspace
from services.utils.utils_service import gerar_nome_pasta
from services.logger_service import logger
from services.soc.soc_services import (
    fluxo_acesso_completo_soc,
    navegar_para_socged,
    aplicar_filtro_data,
    baixar_todos_os_asos_da_pagina,
    avancar_pagina_soc,
)
from services.utils import organizar_asos


def baixar_asos_por_intervalo_data(data_inicio: str, data_fim: str):
    """Fluxo principal de extração de ASOs do SOC."""

    # 1. Monta o diretório de destino dos downloads
    nome_lote = gerar_nome_pasta(data_inicio, data_fim)
    sub_caminho = os.path.join("Asos", nome_lote)
    diretorio_final = get_workspace(sub_caminho)
    os.makedirs(diretorio_final, exist_ok=True)

    driver = None
    try:
        logger.info(f"🚀 Iniciando download de ASOs: {data_inicio} a {data_fim}")
        logger.info(f"📁 Destino dos arquivos: {diretorio_final}")

        # 2. Abre o Chrome já apontando para a pasta correta, faz login no SOC
        driver, wait = fluxo_acesso_completo_soc(diretorio_customizado=diretorio_final)

        # 3. Acessa o SOCGED e filtra pelo tipo ASO
        navegar_para_socged(driver, wait)

        # 4. Aplica o filtro de datas
        aplicar_filtro_data(driver, wait, data_inicio, data_fim)

        # 5. Percorre todas as páginas de resultados e baixa os PDFs
        pagina = 1
        while True:
            logger.info(f"📄 Processando página {pagina}...")
            baixar_todos_os_asos_da_pagina(driver, wait)

            if not avancar_pagina_soc(driver, wait):
                logger.info("✅ Última página atingida. Downloads finalizados.")
                break
            pagina += 1

    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}", exc_info=True)

    finally:
        if driver:
            driver.quit()

        # 6. Organiza e renomeia os PDFs baixados, gerando o relatório Excel
        print(f"\n🔄 Organizando arquivos em: {diretorio_final}")
        organizar_asos.executar(diretorio_especifico=diretorio_final)


if __name__ == "__main__":
    baixar_asos_por_intervalo_data("06/03/2026", "06/03/2026")