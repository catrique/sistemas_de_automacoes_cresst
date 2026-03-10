import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from config.loaders import get_endpoint, Endpoint, login_soc
from services.selenium_services import iniciar_driver, autenticar_proxy_pyautogui
from services.logger_service import logger

FRAME_ID = "novosocFrame"
MODAL_ID = "arquivosModal"
TIPO_GED_ASO = "7"


def fluxo_acesso_completo_soc(diretorio_customizado: str = None):
    """
    Faz o setup inicial: Driver (com pasta de download) -> URL -> Proxy -> Login.
    Retorna (driver, wait) prontos para uso.
    """
    driver = iniciar_driver(diretorio_customizado=diretorio_customizado)
    wait = WebDriverWait(driver, 30)

    try:
        url_soc = get_endpoint(Endpoint.SOC_URL)
        driver.get(url_soc)
        autenticar_proxy_pyautogui()
        executar_login_soc(driver, wait)
        return driver, wait
    except Exception as e:
        logger.error(f"Erro no acesso inicial SOC: {e}")
        driver.quit()
        raise


def executar_login_soc(driver, wait):
    """Preenche usuário, senha e teclado virtual."""
    credenciais = login_soc()

    wait.until(EC.presence_of_element_located((By.ID, "bt_entrar")))
    driver.find_element(By.ID, "usu").send_keys(credenciais["login"])
    driver.find_element(By.ID, "senha").send_keys(credenciais["password"])
    driver.find_element(By.ID, "empsoc").click()

    senha_bruta = credenciais.get("senha", "")
    cliques = (
        [c.strip() for c in senha_bruta.split(",")]
        if isinstance(senha_bruta, str)
        else senha_bruta
    )
    wait.until(EC.visibility_of_element_located((By.ID, "teclado")))

    for valor in cliques:
        if valor:
            xpath = f"//div[@id='teclado']//input[@value='{valor}']"
            driver.find_element(By.XPATH, xpath).click()
            time.sleep(0.3)

    logger.info("Sequência da senha virtual finalizada.")

    driver.find_element(By.ID, "bt_entrar").click()
    wait.until(EC.url_changes(get_endpoint(Endpoint.SOC_URL)))
    logger.info("Login SOC efetuado com sucesso.")


def voltar_para_frame_principal(driver, wait):
    """Garante que o Selenium está focado no frame de conteúdo do SOC."""
    driver.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, FRAME_ID)))


def navegar_para_socged(driver, wait):
    """Acessa o card SOCGED e filtra por ASO."""
    voltar_para_frame_principal(driver, wait)

    socged_card = wait.until(EC.element_to_be_clickable((By.ID, "div-card-socged")))
    driver.execute_script("arguments[0].scrollIntoView(true);", socged_card)
    time.sleep(1)
    socged_card.click()

    wait.until(EC.presence_of_element_located((By.ID, "codigoTipoGed")))
    select = Select(driver.find_element(By.ID, "codigoTipoGed"))
    select.select_by_value(TIPO_GED_ASO)


def aplicar_filtro_data(driver, wait, data_inicial: str, data_final: str):
    """Preenche as datas de busca e submete o filtro."""
    voltar_para_frame_principal(driver, wait)

    for campo_id, valor in [("dataInicial", data_inicial), ("dataFinal", data_final)]:
        campo = wait.until(EC.element_to_be_clickable((By.ID, campo_id)))
        driver.execute_script("arguments[0].value = '';", campo)
        campo.send_keys(Keys.CONTROL + "a")
        campo.send_keys(Keys.DELETE)
        campo.send_keys(valor)

    campo_buscar = driver.find_element(By.ID, "nomeSeach")
    campo_buscar.click()
    campo_buscar.send_keys(Keys.ENTER)
    time.sleep(3)


def fechar_modal_arquivos(driver):
    """Fecha o modal de visualização via JS para não travar o fluxo."""
    try:
        driver.execute_script(f"$('#{MODAL_ID}').modal('hide');")
        time.sleep(0.5)
    except Exception:
        pass


def baixar_todos_os_asos_da_pagina(driver, wait):
    """Varre a tabela atual e baixa todos os documentos encontrados."""
    voltar_para_frame_principal(driver, wait)

    driver.execute_script("document.body.style.paddingBottom = '300px';")

    botoes_detalhes = driver.find_elements(By.XPATH, "//a[img[@id='det']]")
    total = len(botoes_detalhes)
    logger.info(f"Encontrados {total} itens para baixar nesta página.")

    for i in range(total):
        progresso = f"{i + 1:02d}/{total:02d}"

        try:
            fechar_modal_arquivos(driver)
            voltar_para_frame_principal(driver, wait)

            # Re-localiza o botão para evitar StaleElementReferenceException
            botoes = driver.find_elements(By.XPATH, "//a[img[@id='det']]")
            botao = botoes[i]

            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", botao
            )
            time.sleep(0.5)

            try:
                nome_func = botao.find_element(
                    By.XPATH, "./ancestor::tr[1]/td[2]"
                ).text.strip()
            except Exception:
                nome_func = "NOME_NAO_IDENTIFICADO"

            logger.info(f"[{progresso}] Processando: {nome_func}")

            driver.execute_script("arguments[0].click();", botao)
            time.sleep(3)

            xpath_visualizar = "//span[@class='icone-visualizar-arquivo icones']"
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath_visualizar))).click()

            time.sleep(2)

            fechar_abas_excedentes(driver, wait)

        except Exception as e:
            logger.error(f"[{progresso}] Erro ao processar item: {e}")
        finally:
            fechar_modal_arquivos(driver)


def fechar_abas_excedentes(driver, wait):
    """Mantém apenas a aba principal aberta."""
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        voltar_para_frame_principal(driver, wait)


def avancar_pagina_soc(driver, wait) -> bool:
    """Clica no botão 'Próximo' e retorna False se não houver mais páginas."""
    voltar_para_frame_principal(driver, wait)
    xpath_proximo = "//div[@id='barraInferior']//a[@id='btn_proximo']"

    try:
        botoes = driver.find_elements(By.XPATH, xpath_proximo)
        if not botoes:
            return False

        btn = botoes[0]
        if "disabled" in (btn.get_attribute("class") or ""):
            return False

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", btn
        )
        btn.click()
        time.sleep(4)
        return True
    except Exception:
        return False