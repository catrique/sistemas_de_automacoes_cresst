"""
services/soc/soc_retorno_ao_trabalho_service.py

Funções Selenium para o fluxo de Consultar Agendamentos → Retorno ao Trabalho.
"""
import time
from datetime import date
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from services.logger_service import logger

FRAME_ID = "novosocFrame"
VALOR_RETORNO_AO_TRABALHO = "3"

def navegar_para_consultar_agendamentos(driver, wait: WebDriverWait) -> None:
    """Clica no card 'Consultar agendamentos' na tela inicial do SOC."""
    driver.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, FRAME_ID)))

    card = wait.until(
        EC.element_to_be_clickable((By.ID, "div-card-consultar-agendamentos"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", card)
    time.sleep(0.5)
    card.click()
    logger.info("Card 'Consultar agendamentos' clicado.")

    wait.until(EC.presence_of_element_located((By.ID, "btn-filtro")))

def abrir_modal_filtro(driver, wait: WebDriverWait) -> None:
    """Abre o modal de filtro clicando no ícone de filtrar."""
    driver.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, FRAME_ID)))

    btn_filtro = wait.until(EC.element_to_be_clickable((By.ID, "btn-filtro")))
    btn_filtro.click()
    logger.info("Modal de filtro aberto.")

    wait.until(EC.visibility_of_element_located(
        (By.ID, "ipt-text-campo-seleciona-tipo-compromisso")
    ))


def selecionar_tipo_retorno_ao_trabalho(driver, wait: WebDriverWait) -> None:
    """
    Clica no campo de 'Tipo de compromisso' e seleciona 'Retorno ao Trabalho'
    (data-valor="3") na lista de opções.
    """
    campo_tipo = wait.until(
        EC.element_to_be_clickable((By.ID, "ipt-text-campo-seleciona-tipo-compromisso"))
    )
    campo_tipo.click()
    time.sleep(0.5)

    xpath_opcao = (
        f"//ul[@id='seleciona-tipo-compromisso']"
        f"//li[@data-valor='{VALOR_RETORNO_AO_TRABALHO}']"
    )
    opcao = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_opcao)))
    opcao.click()
    logger.info("Tipo de compromisso 'Retorno ao Trabalho' selecionado.")


def aplicar_filtro_modal(driver, wait: WebDriverWait) -> None:
    """Clica em 'Aplicar' para fechar o modal e confirmar o filtro."""
    btn_aplicar = wait.until(EC.element_to_be_clickable((By.ID, "btn-filtrar")))
    btn_aplicar.click()
    logger.info("Filtro aplicado.")
    time.sleep(1)


def preencher_data_pesquisa(driver, wait: WebDriverWait, data: str = None) -> None:
    """
    Preenche o campo de período com a data informada (formato DD/MM/AAAA).
    Se nenhuma data for passada, usa a data de hoje.
    """
    if data is None:
        hoje = date.today()
        data = hoje.strftime("%d/%m/%Y")

    driver.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, FRAME_ID)))

    campo_data = wait.until(
        EC.element_to_be_clickable((By.ID, "ipt-data-pesquisa"))
    )
    driver.execute_script("arguments[0].value = '';", campo_data)
    campo_data.click()
    time.sleep(0.3)
    campo_data.send_keys(data)
    time.sleep(0.5)
    logger.info(f"Data de pesquisa preenchida: {data}")


def executar_pesquisa(driver, wait: WebDriverWait) -> None:
    """Clica no botão de busca para carregar os resultados."""
    btn_pesquisa = wait.until(EC.element_to_be_clickable((By.ID, "btn-pesquisa")))
    btn_pesquisa.click()
    logger.info("Pesquisa executada.")
    time.sleep(3)


def extrair_linhas_tabela(driver, wait: WebDriverWait) -> list[dict]:
    """
    Lê todas as linhas do tbody da tabela de resultados e retorna uma lista
    de dicionários com as colunas:
        Data, Hora, Tipo de Compromisso, Nome, CPF, Unidade, Setor, Cargo, Atendido
    """
    driver.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, FRAME_ID)))

    wait.until(EC.presence_of_element_located((By.ID, "corpo-tabela-resultados")))
    linhas = driver.find_elements(
        By.CSS_SELECTOR, "#corpo-tabela-resultados tr"
    )

    registros = []
    for linha in linhas:
        celulas = linha.find_elements(By.TAG_NAME, "td")
        if len(celulas) < 8:
            continue

        td_nome = celulas[3]
        try:
            nome = td_nome.find_element(By.XPATH, "./text()[1]").text.strip()
        except Exception:
            nome = td_nome.text.split("\n")[0].strip()

        try:
            cpf = td_nome.find_element(By.TAG_NAME, "span").text.strip()
            cpf = cpf.replace("CPF ", "").strip()
        except Exception:
            cpf = "N/A"

        registros.append({
            "Data":               celulas[0].text.strip(),
            "Hora":               celulas[1].text.strip(),
            "Tipo de Compromisso": celulas[2].text.strip(),
            "Nome":               nome,
            "CPF":                cpf,
            "Unidade":            celulas[4].text.strip(),
            "Setor":              celulas[5].text.strip(),
            "Cargo":              celulas[6].text.strip(),
            "Atendido":           celulas[7].text.strip(),
        })

    logger.info(f"{len(registros)} registro(s) extraído(s) da tabela.")
    return registros