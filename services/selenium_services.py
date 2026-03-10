import os
import time
import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from config.loaders import login_proxy
except ImportError:
    def login_proxy():
        return {"host": "", "port": "", "user": "", "password": ""}


def iniciar_driver(diretorio_customizado: str = None):
    """
    Inicializa o Chrome com a pasta de download configurada de forma absoluta.
    Se nenhum diretório for passado, usa a pasta padrão do sistema.
    """
    options = Options()

    if diretorio_customizado:
        caminho_abs = os.path.abspath(diretorio_customizado)
        os.makedirs(caminho_abs, exist_ok=True)
        prefs = {
            "download.default_directory": caminho_abs,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True,  # Força download em vez de abrir no browser
        }
        options.add_experimental_option("prefs", prefs)

    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")

    # Se precisar de proxy, descomente a linha abaixo:
    # configurar_proxy_options(options)

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def buscar_elementos(driver, xpath: str):
    """Retorna uma lista de elementos pelo XPath."""
    return driver.find_elements(By.XPATH, xpath)


def buscar_elemento_filho(elemento_pai, xpath: str):
    """Busca um elemento dentro de outro (ex: nome na linha da tabela)."""
    return elemento_pai.find_element(By.XPATH, xpath)


def esperar_carregamento(segundos: float = 1.0):
    """Pausa controlada para processos assíncronos."""
    time.sleep(segundos)


def clicar_no_pdf(driver, timeout: int = 20):
    """Aguarda o ícone de visualização de PDF aparecer e clica nele."""
    wait = WebDriverWait(driver, timeout)
    xpath_pdf = "//span[@class='icone-visualizar-arquivo icones']"
    wait.until(EC.element_to_be_clickable((By.XPATH, xpath_pdf))).click()


def fechar_janelas_excedentes(driver):
    """Garante que apenas a aba principal do SOC permaneça aberta."""
    if len(driver.window_handles) > 1:
        principal = driver.window_handles[0]
        for handle in driver.window_handles[1:]:
            driver.switch_to.window(handle)
            driver.close()
        driver.switch_to.window(principal)


def autenticar_proxy_pyautogui():
    """Conclui a autenticação de rede se o popup do Windows aparecer."""
    proxy_data = login_proxy()
    if not proxy_data.get("user"):
        return

    try:
        time.sleep(2)
        pyautogui.write(proxy_data["user"], interval=0.1)
        pyautogui.press("tab")
        pyautogui.write(proxy_data["password"], interval=0.1)
        pyautogui.press("enter")
    except Exception as e:
        print(f"Erro no PyAutoGUI: {e}")