import base64
import getpass
import hashlib
import json
import os
import time
from services.logger_service import logger
import platform 
import sys
from cryptography.fernet import Fernet
from enum import Enum

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import tempfile

__all__ = ['Endpoint', 'reload_settings', 'update_settings', 'get_endpoint', 'login_betha', 'login_soc', 'login_proxy', 'get_workspace']


settings = {}
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    SETTINGS_PATH = os.path.join(BASE_DIR, "config", "settings.json")
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SETTINGS_PATH = os.path.join(BASE_DIR, "config", "settings.json")

def _gerar_chave_unica():
    semente = f"{platform.node()}_{getpass.getuser()}"
    hash_obj = hashlib.sha256(semente.encode()).digest()
    return base64.urlsafe_b64encode(hash_obj)

_cipher = Fernet(_gerar_chave_unica())

class ConfigLoader:
    @staticmethod
    def load_settings():
        """Lê o arquivo JSON do disco e retorna os dados."""
        if not os.path.exists(SETTINGS_PATH):
            print(f"📂 Arquivo não encontrado: {SETTINGS_PATH}")
            return None

        try:
            with open(SETTINGS_PATH, "r", encoding="utf8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erro ao carregar JSON: {e}")
            return None

class Endpoint(Enum):
    # Betha - URLs Principais
    BETHA_BASE = ("betha", "api", "base_url")
    BETHA_LOGIN = ("betha", "api", "url_login")
    
    # Betha - Lista de Endpoints Específicos
    BETHA_ATESTADOS = ("betha", "api", "endpoints", "atestados")
    BETHA_MATRICULA_ESOCIAL = ("betha", "api", "endpoints", "matricula_esocial")
    BETHA_LISTAGEM_MATRICULA = ("betha", "api", "endpoints", "listagem_matricula")
    BETHA_LISTAGEM_MATRICULA_AVANCADA = ("betha", "api", "endpoints", "listagem_matricula_avancado")
    BETHA_ASO2 = ("betha", "api", "endpoints", "aso2")
    BETHA_AFASTAMENTOS = ("betha", "api", "endpoints", "afastamentos")
    BETHA_ATESTADO = ("betha", "api", "endpoints", "atestado")
    BETHA_LOTACAO_FISICA = ("betha", "api", "endpoints", "lotacao_fisica")
    BETHA_TRANSPARENCIA = ("betha", "api", "endpoints", "transparencia")
    BETHA_PESSOA_FISICA = ("betha", "api", "endpoints", "pessoa_fisica")
    BETHA_MATRICULA = ("betha", "api", "endpoints", "matricula")
    BETHA_PROFISSIONAL = ("betha", "api", "endpoints", "profissional")
    BETHA_ASO = ("betha", "api", "endpoints", "aso")
    BETHA_ANEXO = ("betha", "api", "endpoints", "anexo")
    BETHA_ASO_FORMULARIO = ("betha", "api", "endpoints", "aso_formulario")

    # SOC
    SOC_URL = ("soc", "URL_SOC")

def get_workspace(subpasta: str = None) -> str:
    """
    Retorna o caminho da pasta workspace na raiz do projeto.
    Se uma subpasta for passada, ela será criada dentro do workspace.
    """
    workspace = os.path.join(BASE_DIR, "workspace")
    
    if subpasta:
        workspace = os.path.join(workspace, subpasta)

    if not os.path.exists(workspace):
        os.makedirs(workspace)
        
    return workspace


def get_endpoint(servico: Endpoint) -> str:
    """
    Retorna o endpoint em texto buscando dinamicamente no dicionário settings.
    Exemplo: get_endpoint(Endpoint.BETHA_ATESTADOS)
    """
    return get_config(*servico.value)

def reload_settings():
    """Atualiza a memória mantendo a mesma referência de objeto."""
    global settings

    if not os.path.exists(SETTINGS_PATH):
        return

    try:
        with open(SETTINGS_PATH, "r", encoding="utf8") as f:
            dados = json.load(f)
            settings.clear()
            settings.update(dados)
    except Exception as e:
        print(f"❌ Erro ao carregar JSON: {e}")


def get_config(*keys, default=None):
    """
    Busca valores aninhados no dicionário de settings.
    Recarrega se settings estiver vazio ou se for uma busca de credenciais.
    """
    global settings
    
    if not settings:
        reload_settings()

    val = settings
    try:
        for key in keys:
            if not isinstance(val, dict):
                return default
            val = val.get(key)
        
        return val if val is not None else default
    except Exception:
        return default


def update_settings(path_string, novo_valor, salvar_no_disco=True):
    """
    Atualiza um valor no dicionário global e opcionalmente salva no JSON.
    Uso: update_settings("betha,user,admin,LOGIN", "novo_usuario")
    """
    global settings

    keys = [k.strip() for k in path_string.split(",")]

    ptr = settings
    try:
        for key in keys[:-1]:
            if key not in ptr:
                ptr[key] = {}
            ptr = ptr[key]

        ptr[keys[-1]] = novo_valor

        if salvar_no_disco:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        reload_settings()
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar configuração: {e}")
        return False

def criptografar(texto: str) -> str:
    if not texto: return ""
    return _cipher.encrypt(str(texto).strip().encode()).decode()

def _descriptografar(texto_cripto: str) -> str:
    if not texto_cripto: return ""
    try:
        return _cipher.decrypt(str(texto_cripto).encode()).decode()
    except Exception:
        return ""

def login_betha() -> dict:
    """
    Retorna o objeto de login para o sistema Betha descriptografado.
    """
    # Busca os valores criptografados no caminho: betha -> user -> admin
    user_hash = get_config("betha", "user", "admin", "LOGIN")
    pass_hash = get_config("betha", "user", "admin", "PASSWORD")
    
    return {
        "login": _descriptografar(user_hash),
        "password": _descriptografar(pass_hash)
    }

def login_soc() -> dict:
    """
    Retorna o objeto de login para o sistema SOC descriptografado.
    """
    # Busca os valores criptografados no caminho: soc -> user -> admin
    user_hash = get_config("soc", "user", "admin", "LOGIN")
    pass_hash = get_config("soc", "user", "admin", "PASSWORD")
    senha_hash = get_config("soc", "user", "admin", "SENHA_VIRTUAL")
    
    return {
        "login": _descriptografar(user_hash),
        "password": _descriptografar(pass_hash),
        "senha": _descriptografar(senha_hash)
    }

def login_proxy() -> dict:
    """
    Retorna as configurações e credenciais do Proxy descriptografadas.
    """
    return {
        "host": get_config("proxy", "PROXY_HOST"),
        "port": get_config("proxy", "PROXY_PORT"),
        "user": _descriptografar(get_config("proxy", "PROXY_USER")),
        "password": _descriptografar(get_config("proxy", "PROXY_PASS"))
    }

def salvar_credenciais_criptografadas(dados_credenciais: dict):
    """
    Criptografa e guarda as credenciais. 
    Lança uma exceção em caso de erro.
    """
    mapeamento = {
        "betha_login": "betha,user,admin,LOGIN",
        "betha_senha": "betha,user,admin,PASSWORD",
        "soc_email": "soc,user,admin,LOGIN",
        "soc_senha": "soc,user,admin,PASSWORD",
        "soc_virtual": "soc,user,admin,SENHA_VIRTUAL",
        "proxy_user": "proxy,PROXY_USER",
        "proxy_senha": "proxy,PROXY_PASS"
    }

    for chave_interface, path in mapeamento.items():
        valor = dados_credenciais.get(chave_interface)
        if valor:
            logger.info(f"Criptografando e salvando: {chave_interface}")
            valor_cripto = criptografar(valor)
            update_settings(path, valor_cripto)
    
    logger.info("✅ Todas as credenciais foram atualizadas com sucesso.")

def atualizar_token_betha_automatico():
    """
    Faz o login no portal Betha e captura o token de autorização.
    """
    logger.info("🚀 Iniciando captura de Token Betha...")
    reload_settings()

    login_cripto = get_config('betha', 'user', 'admin', 'LOGIN')
    senha_cripto = get_config('betha', 'user', 'admin', 'PASSWORD')

    if not login_cripto or not senha_cripto:
        raise ValueError("Credenciais Betha não configuradas.")

    login_real = _descriptografar(login_cripto)
    senha_real = _descriptografar(senha_cripto)

    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    pasta_temp = os.path.join(tempfile.gettempdir(), "chromedriver_data")
    os.makedirs(pasta_temp, exist_ok=True)
    os.environ['WDM_PATH'] = pasta_temp

    driver = None
    try:
        driver_path = ChromeDriverManager().install()
        driver = webdriver.Chrome(service=Service(driver_path), options=options)
        
        driver.execute_cdp_cmd('Network.enable', {})
        wait = WebDriverWait(driver, 35)
        url_aso = "https://rh.betha.cloud/#/entidades/ZGF0YWJhc2U6MTE5NyxlbnRpdHk6MTAwNjU=/modulos/sst/executando/processos/aso"
        
        driver.get(url_aso)

        if "login" in driver.current_url:
            logger.info("🔑 Realizando login automático...")
            wait.until(EC.presence_of_element_located((By.ID, "login:btAcessar")))
            driver.find_element(By.ID, "login:iUsuarios").send_keys(login_real)
            driver.find_element(By.ID, "login:senha").send_keys(senha_real)
            driver.find_element(By.ID, "login:btAcessar").click()
            wait.until(lambda d: "login" not in d.current_url)
            driver.get(url_aso)

        token_capturado = None
        user_access_capturado = None

        # Tenta capturar o token nos logs de rede (4 tentativas)
        for i in range(4):
            logger.info(f"Buscando token na rede... tentativa {i+1}")
            time.sleep(5)
            logs = driver.get_log('performance')
            for entry in logs:
                log_data = json.loads(entry['message'])['message']
                if log_data['method'] == 'Network.requestWillBeSent':
                    headers = log_data.get('params', {}).get('request', {}).get('headers', {})
                    auth = headers.get('Authorization') or headers.get('authorization')
                    u_acc = headers.get('User-Access') or headers.get('user-access')

                    if auth and "Bearer" in auth and u_acc:
                        token_capturado = auth
                        user_access_capturado = u_acc
                        break
            if token_capturado: break

        if not token_capturado:
            raise Exception("Não foi possível interceptar o token de autorização.")

        # Salva os dados capturados
        update_settings("betha,api,authorization", str(token_capturado).strip())
        update_settings("betha,api,user_access", str(user_access_capturado).strip())
        logger.info("✅ Token Betha atualizado com sucesso!")

    finally:
        if driver:
            driver.quit()
reload_settings()
