import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from config.loaders import get_workspace
from services.logger_service import logger
from services.soc.soc_services import fluxo_acesso_completo_soc, avancar_pagina_soc
from services.soc.relatorios_service import (
    SessionExpired,
    load_checkpoint,
    save_checkpoint,
    clear_checkpoint,
    save_to_excel,
    extrair_celulas,
)
from services.utils.utils_service import data_hoje_formatada


OUTPUT_DIR = get_workspace(os.path.join("relatorios", "saida"))
LOG_FILE = os.path.join(OUTPUT_DIR, f"funcionarios_soc_{data_hoje_formatada()}.xlsx")
CHECKPOINT_FILE = os.path.join(
    OUTPUT_DIR, f"checkpoint_rel_funcionarios_{data_hoje_formatada()}  .txt"
)
os.makedirs(OUTPUT_DIR, exist_ok=True)

COLUNAS = [
    "Página",
    "Índice",
    "Código",
    "Nome",
    "Unidade",
    "Setor",
    "Cargo",
    "Matrícula",
    "Situação",
    "Detalhe do Erro",
]

SELETORES_FUNCIONARIO = {
    "Código": "./td[1]//a",
    "Nome": "./td[2]//div[@class='nome-funcionario-registrado']",
    "Unidade": "./td[3]",
    "Setor": "./td[4]",
    "Cargo": "./td[5]",
    "Matrícula": "./td[6]",
    "Situação": "./td[7]",
}

ROWS_XPATH = "//tr[contains(@class, 'cor') and ./td[2]//div[@class='nome-funcionario-registrado']]"


def _navegar_para_funcionarios(driver, wait):
    """Acessa o card de funcionários e dispara a busca sem inativos."""
    driver.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "novosocFrame")))

    card = wait.until(EC.element_to_be_clickable((By.ID, "div-card-funcionario")))
    driver.execute_script("arguments[0].scrollIntoView(true);", card)
    time.sleep(1)
    ActionChains(driver).move_to_element(card).click().perform()

    xpath_inativo = (
        "//fieldset[@class='col1']"
        "//p[./label[normalize-space()='Inativos']]/input[@type='checkbox']"
    )
    try:
        cb = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_inativo)))
        if cb.is_selected():
            cb.click()
    except Exception:
        pass

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='socContent']/form[1]/fieldset/p[1]/a/img")
        )
    ).click()
    logger.info("Busca de funcionários iniciada.")
    time.sleep(3)


def _processar_pagina(driver, wait, current_page: int, start_index: int) -> list:
    """Extrai todos os funcionários da página atual. Retorna lista de linhas."""
    driver.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "novosocFrame")))

    try:
        wait.until(EC.presence_of_all_elements_located((By.XPATH, ROWS_XPATH)))
        rows = driver.find_elements(By.XPATH, ROWS_XPATH)
    except TimeoutException:
        rows = []

    total = len(rows)
    logger.info(f"Página {current_page}: {total} funcionários.")
    dados_pagina = []

    for index, row in enumerate(rows):
        if index < start_index:
            continue

        detalhe_erro = ""
        try:
            campos = extrair_celulas(row, SELETORES_FUNCIONARIO)
            print(f"  [{index+1}/{total}] {campos.get('Nome', '')}", end="\r")
        except StaleElementReferenceException:
            raise SessionExpired("Elemento obsoleto detectado.")
        except Exception as e:
            campos = {k: "N/A" for k in SELETORES_FUNCIONARIO}
            detalhe_erro = str(e).splitlines()[0][:80]
        finally:
            dados_pagina.append(
                [
                    current_page,
                    index + 1,
                    campos.get("Código", "N/A"),
                    campos.get("Nome", "N/A"),
                    campos.get("Unidade", "N/A"),
                    campos.get("Setor", "N/A"),
                    campos.get("Cargo", "N/A"),
                    campos.get("Matrícula", "N/A"),
                    campos.get("Situação", "N/A"),
                    detalhe_erro,
                ]
            )
            save_checkpoint(CHECKPOINT_FILE, current_page, index + 1)
    return dados_pagina


def executar():
    current_page, start_index = load_checkpoint(CHECKPOINT_FILE)
    driver = None

    try:
        driver, wait = fluxo_acesso_completo_soc()
        _navegar_para_funcionarios(driver, wait)

        if current_page > 1:
            logger.info(f"Retomando a partir da Página {current_page}...")
            for _ in range(1, current_page):
                avancar_pagina_soc(driver, wait)

        while True:
            dados = _processar_pagina(driver, wait, current_page, start_index)
            save_to_excel(dados, COLUNAS, LOG_FILE)
            start_index = 0

            if not avancar_pagina_soc(driver, wait):
                break
            current_page += 1
            save_checkpoint(CHECKPOINT_FILE, current_page, 0)

        clear_checkpoint(CHECKPOINT_FILE)
        logger.info("✅ Exportação de funcionários concluída.")
        print(f"\n✅ Arquivo gerado: {LOG_FILE}")

    except SessionExpired:
        logger.warning("Sessão expirada. Salve o checkpoint e reinicie.")
    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    executar()
