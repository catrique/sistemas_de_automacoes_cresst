import random
import re
import time
import unicodedata
from datetime import datetime

import pandas as pd
from selenium.common.exceptions import NoAlertPresentException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from services.logger_service import logger

FRAME_ID = "novosocFrame"

TIPO_ADMISSIONAL = "1"
TIPO_PERIODICO   = "2"
TIPO_DEMISSIONAL = "3"

def garantir_frame_principal(driver, wait) -> None:
    """Garante foco no frame de conteúdo principal do SOC."""
    driver.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, FRAME_ID)))


def acessar_area_funcionarios(driver, wait) -> None:
    """Navega para o card de Funcionários."""
    garantir_frame_principal(driver, wait)
    wait.until(EC.element_to_be_clickable((By.ID, "div-card-funcionario"))).click()
    logger.info("Área de funcionários acessada.")


def acessar_area_agendamentos(driver, wait) -> None:
    """Navega para o card de Cadastrar Agendamentos."""
    driver.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, FRAME_ID)))
    wait.until(EC.element_to_be_clickable((By.ID, "div-card-cadastrar-agendamentos"))).click()
    time.sleep(3)
    logger.info("Área de agendamentos acessada.")


def fechar_abas_excedentes(driver, wait) -> None:
    """Mantém apenas a aba principal aberta."""
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        garantir_frame_principal(driver, wait)


def clicar_cancelar(driver, wait) -> bool:
    """Clica no botão Cancelar do formulário ativo."""
    xpaths = [
        "//img[contains(@src, 'cancela.png')]",
        "//img[@tooltype='Cancelar']",
        "//a[contains(@href, \"doAcao('cancel')\")]//img",
    ]
    for xpath in xpaths:
        try:
            btn = driver.find_element(By.XPATH, xpath)
            if btn and btn.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.3)
                try:
                    btn.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
                logger.info("Formulário cancelado.")
                return True
        except Exception:
            continue
    logger.warning("Botão cancelar não encontrado.")
    return False


def verificar_alerta(driver) -> str | None:
    """Aceita alerta JS se presente e retorna o texto."""
    try:
        alerta = WebDriverWait(driver, 3).until(EC.alert_is_present())
        texto = alerta.text
        alerta.accept()
        logger.info(f"Alerta aceito: '{texto}'")
        return texto
    except (TimeoutException, NoAlertPresentException):
        return None


def normalizar_texto(texto: str) -> str:
    """Remove acentos e caracteres especiais, converte para maiúsculas."""
    if not texto or (isinstance(texto, float) and pd.isna(texto)):
        return ""
    texto = str(texto)
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-zA-Z0-9\s]", "", texto)
    return " ".join(texto.split()).upper()


def preencher_campo(driver, wait, identificador: str, tipo: str, valor: str,
                    descricao: str = "") -> bool:
    """Preenche campo de texto de forma robusta."""
    loc_map = {"id": (By.ID, identificador), "name": (By.NAME, identificador)}
    loc = loc_map.get(tipo, (By.XPATH, identificador))
    try:
        campo = wait.until(EC.element_to_be_clickable(loc))
        campo.clear()
        time.sleep(0.3)
        campo.send_keys(str(valor))
        if descricao:
            logger.info(f"Campo '{descricao}' preenchido: {valor}")
        return True
    except Exception as e:
        logger.error(f"Erro ao preencher '{descricao}': {e}")
        return False


def selecionar_dropdown(driver, wait, identificador: str, tipo: str,
                        valor_texto: str, descricao: str = "") -> bool:
    """Seleciona opção de dropdown pelo texto visível."""
    loc_map = {"id": (By.ID, identificador), "name": (By.NAME, identificador)}
    loc = loc_map.get(tipo, (By.XPATH, identificador))
    try:
        dropdown = wait.until(EC.element_to_be_clickable(loc))
        Select(dropdown).select_by_visible_text(valor_texto)
        if descricao:
            logger.info(f"Dropdown '{descricao}' selecionado: {valor_texto}")
        return True
    except Exception as e:
        logger.error(f"Erro ao selecionar '{descricao}': {e}")
        return False


def selecionar_dropdown_normalizado(driver, wait, select_id: str, texto_busca: str,
                                    nome_campo: str = "campo",
                                    fallback_texto: str = None) -> bool:
    """Seleciona dropdown comparando textos normalizados (ignora acentos/case)."""
    try:
        dropdown = wait.until(EC.element_to_be_clickable((By.ID, select_id)))
        select = Select(dropdown)
        busca_norm = normalizar_texto(texto_busca)

        for opt in select.options:
            if normalizar_texto(opt.text) == busca_norm:
                select.select_by_visible_text(opt.text)
                logger.info(f"Dropdown '{nome_campo}' selecionado: {opt.text}")
                return True

        logger.warning(f"Opção não encontrada em '{nome_campo}': '{texto_busca}'")

        if fallback_texto:
            fb_norm = normalizar_texto(fallback_texto)
            for opt in select.options:
                if normalizar_texto(opt.text) == fb_norm:
                    select.select_by_visible_text(opt.text)
                    logger.info(f"Dropdown '{nome_campo}' usando fallback: {opt.text}")
                    return True
            logger.warning(f"Fallback também não encontrado em '{nome_campo}'.")

        return False
    except Exception as e:
        logger.error(f"Erro ao selecionar dropdown '{nome_campo}': {e}")
        return False



def extrair_matricula_da_tabela(html_tabela: str) -> str | None:
    """Extrai matrícula iniciada com '990' da tabela HTML."""
    linhas = re.findall(r"<tr[^>]*>(.*?)</tr>", html_tabela, re.DOTALL)
    for linha in linhas:
        match = re.search(r"<td[^>]*>(\d{8,9}(?:/\d)?)</td>", linha)
        if match and match.group(1).startswith("990"):
            return match.group(1)
    return None


def buscar_cpf_e_extrair_matricula(driver, wait, cpf: str) -> str | None:
    """Busca funcionário por CPF e retorna a próxima matrícula disponível."""
    try:
        radio = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//input[@name='codigoPesquisaFuncionario'][@value='3']")
        ))
        radio.click()
        time.sleep(0.5)

        campo = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='socContent']/form[1]/fieldset/p[1]/input")
        ))
        campo.clear()
        campo.send_keys(re.sub(r"\D", "", str(cpf)))
        campo.send_keys(Keys.ENTER)
        time.sleep(2)

        try:
            tabela = driver.find_element(By.CLASS_NAME, "resultados")
            mat_orig = extrair_matricula_da_tabela(tabela.get_attribute("outerHTML"))
            if not mat_orig:
                return None
            if "/" in mat_orig:
                base, num = mat_orig.split("/")
                return f"{base}/{int(num) + 1}"
            return f"{mat_orig}/1"
        except NoSuchElementException:
            return None
    except Exception as e:
        logger.error(f"Erro na busca de CPF: {e}")
        return None


def selecionar_categoria_esocial_306(driver, wait) -> bool:
    """Abre o modal de categoria eSocial e seleciona a opção 306."""
    try:
        logger.info("Abrindo modal de categoria eSocial...")
        time.sleep(2)

        try:
            icone = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//img[@id='iconeAbrirFiltroCategoria' or contains(@src,'procura.png')]")
            ))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", icone)
            time.sleep(0.5)
            icone.click()
        except Exception:
            driver.execute_script(
                "arguments[0].click();",
                driver.find_element(By.ID, "iconeAbrirFiltroCategoria")
            )

        time.sleep(1)
        campo_filtro = wait.until(EC.element_to_be_clickable((By.ID, "inputFiltroCategoria")))
        campo_filtro.clear()
        campo_filtro.send_keys("306")
        time.sleep(0.5)
        campo_filtro.send_keys(Keys.ENTER)
        time.sleep(2)

        xpaths_tentativa = [
            "//tr[@id='rowCategoriaESocial']",
            "//td[@id='codigoCategoriaESocialLinha' and @data-codigo='306']/..",
            "//tr[.//td[@data-codigo='306']]",
            "//tr[.//td[normalize-space(text())='306']]",
            "//table//tr[td[normalize-space(text())='306']]",
        ]
        linha = None
        for xpath in xpaths_tentativa:
            try:
                el = driver.find_element(By.XPATH, xpath)
                if el.is_displayed():
                    linha = el
                    break
            except Exception:
                continue

        if not linha:
            linha = driver.execute_script("""
                var rows = document.querySelectorAll('tr');
                for (var i = 0; i < rows.length; i++) {
                    var cells = rows[i].querySelectorAll('td');
                    for (var j = 0; j < cells.length; j++) {
                        if (cells[j].textContent.trim() === '306' ||
                            cells[j].getAttribute('data-codigo') === '306')
                            return rows[i];
                    }
                }
                return null;
            """)

        if not linha:
            raise Exception("Linha da categoria 306 não encontrada.")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", linha)
        time.sleep(0.3)
        try:
            linha.click()
        except Exception:
            driver.execute_script("arguments[0].click();", linha)

        time.sleep(0.5)
        logger.info("Categoria eSocial 306 selecionada.")
        return True

    except Exception as e:
        logger.error(f"Erro ao selecionar categoria eSocial 306: {e}")
        return False


def formatar_data_excel(valor) -> str:
    """Converte datas vindas do Excel para o formato dd/mm/yyyy."""
    if pd.isna(valor):
        return ""
    if isinstance(valor, (datetime, pd.Timestamp)):
        return valor.strftime("%d/%m/%Y")
    try:
        return datetime.strptime(str(valor), "%d/%m/%y").strftime("%d/%m/%Y")
    except ValueError:
        return str(valor)


def cadastrar_funcionario(driver, wait, row: dict,
                           nome_empresa: str = "PREFEITURA MUNICIPAL DE DIVINÓPOLIS") -> bool:
    """
    Preenche e salva o formulário de cadastro de um funcionário.

    Parâmetros esperados em `row`:
        Nome, Data Nascimento, Data Admissão, CPF, Sexo,
        Matrícula Anterior, E-mail, Cargo, Lotação

    Retorna True se cadastrado com sucesso, False em caso de erro recuperável.
    Levanta exceção em erros críticos.
    """
    garantir_frame_principal(driver, wait)

    btn_incluir = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//*[@id='botoes']/table/tbody/tr/td[2]/a[1]")
    ))
    btn_incluir.click()
    time.sleep(2)

    selecionar_dropdown(driver, wait, "csitefiltrado", "id", nome_empresa, "CSite Filtrado")
    time.sleep(1)

    cargo_upper = str(row.get("Cargo", "")).strip().upper()
    cargos_adm = {"ASSISTENTE EDUCACIONAL", "TECNICO ESCOLAR",
                  "TÉCNICO ESCOLAR", "SUPERVISOR ORIENTADOR DE ENSINO"}
    setor = "ADMINISTRATIVO" if cargo_upper in cargos_adm else "EDUCAÇÃO"

    selecionar_dropdown(driver, wait, "codigoSetorAjax", "id", setor, "Setor")
    time.sleep(2)

    if not selecionar_dropdown_normalizado(driver, wait, "codigoCargoAjax",
                                           row.get("Cargo", ""), "Cargo"):
        logger.warning(f"Cargo não encontrado: {row.get('Cargo')}")
        clicar_cancelar(driver, wait)
        return False

    time.sleep(1)

    if not selecionar_dropdown_normalizado(
            driver, wait, "codigoSiteAjax", row.get("Lotação", ""), "Lotação",
            fallback_texto="SEMED - SECRETARIA MUNICIPAL DE EDUCAÇÃO"):
        logger.warning(f"Lotação não encontrada: {row.get('Lotação')}")
        clicar_cancelar(driver, wait)
        return False

    time.sleep(1)

    preencher_campo(driver, wait, "nomeFuncionario",        "id", row["Nome"],                           "Nome")
    preencher_campo(driver, wait, "dataNascimentoFormatada","id", formatar_data_excel(row["Data Nascimento"]), "Data Nascimento")
    preencher_campo(driver, wait, "dataAdmissao",           "id", formatar_data_excel(row["Data Admissão"]),   "Data Admissão")
    preencher_campo(driver, wait, "cpf",                    "id", row["CPF"],                            "CPF")

    selecionar_dropdown(driver, wait, "situacao",          "id", "Ativo",    "Situação")

    sexo_map = {"MASCULINO": "Masculino", "FEMININO": "Feminino"}
    selecionar_dropdown(driver, wait, "sexoFuncionario",   "id",
                        sexo_map.get(str(row.get("Sexo", "")).upper(), "Masculino"), "Sexo")

    preencher_campo(driver, wait, "matriculaFuncionario",  "id", row["Matrícula Anterior"], "Matrícula")

    email = str(row.get("E-mail", "")).lower().strip()
    if email and email != "nan":
        preencher_campo(driver, wait, "emailPessoal",      "id", email, "E-mail Pessoal")
        preencher_campo(driver, wait, "emailCorporativo",  "id", email, "E-mail Corporativo")

    selecionar_categoria_esocial_306(driver, wait)

    btn_salvar = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//a[contains(@href,\"doAcao('save')\")]//img | //img[contains(@src,'confirma.png')]")
    ))
    btn_salvar.click()
    verificar_alerta(driver)
    time.sleep(2)
    verificar_alerta(driver)

    logger.info(f"Funcionário cadastrado: {row['Nome']}")
    return True



def _parsear_data_exame(valor) -> tuple[str, str, str]:
    """Retorna (dia, mes, ano) a partir de string 'dd/mm/yyyy' ou datetime."""
    if isinstance(valor, str):
        dia, mes, ano = valor.split("/")
    else:
        dia = str(valor.day).zfill(2)
        mes = str(valor.month).zfill(2)
        ano = str(valor.year)
    return dia, mes, ano


def _navegar_calendario(driver, wait, dia: str, mes: str, ano: str) -> None:
    """Seleciona mês/ano no calendário e clica no dia."""
    Select(wait.until(EC.presence_of_element_located((By.NAME, "mes")))).select_by_value(mes)
    time.sleep(1)
    Select(wait.until(EC.presence_of_element_located((By.NAME, "ano")))).select_by_value(ano)
    time.sleep(2)

    btn_dia = wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//td[contains(@onclick,'altdata') and contains(@onclick,'{dia}')]")
    ))
    try:
        btn_dia.click()
    except Exception:
        driver.execute_script("arguments[0].click();", btn_dia)
    time.sleep(2)


def _buscar_funcionario_popup(driver, wait, janela_principal: str,
                               nome: str, matricula: str) -> bool:
    """
    Abre o popup de busca de funcionário, seleciona pela matrícula e
    volta para a janela principal.

    Retorna True se encontrado, False caso contrário.
    """
    input_busca = wait.until(EC.presence_of_element_located((By.NAME, "textoProcuraFuncionario")))
    input_busca.clear()
    input_busca.send_keys(nome)
    driver.execute_script(
        "arguments[0].click();",
        wait.until(EC.element_to_be_clickable((By.ID, "buscaFuncionario")))
    )

    wait.until(EC.number_of_windows_to_be(2))
    for janela in driver.window_handles:
        if janela != janela_principal:
            driver.switch_to.window(janela)
            break

    time.sleep(3)

    try:
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//tr[contains(.,'{matricula}')]//a")
        )).click()
        logger.info(f"Funcionário selecionado pela matrícula: {matricula}")
        encontrado = True
    except Exception:
        encontrado = False
        for linha in driver.find_elements(
                By.XPATH, "//table[@class='resultados']//tr[contains(@class,'cor')]"):
            if matricula.replace(" ", "") in linha.text.replace(" ", ""):
                linha.find_element(By.TAG_NAME, "a").click()
                encontrado = True
                break

    if not encontrado:
        logger.warning(f"Matrícula '{matricula}' não encontrada no popup.")
        if len(driver.window_handles) > 1:
            driver.close()
        driver.switch_to.window(janela_principal)
        return False

    driver.switch_to.window(janela_principal)
    driver.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, FRAME_ID)))
    time.sleep(3)
    return True


def _escolher_horario(driver, wait, hora_preferida: str | None) -> str | None:
    """
    Seleciona slot de horário disponível na agenda.
    Se `hora_preferida` for fornecida, tenta usá-la; senão escolhe aleatoriamente.
    Retorna o horário escolhido ou None se não houver slots disponíveis.
    """
    xpath_slots = (
        "//td[@class='agenda2'][@title='Clique para preencher o compromisso']"
        "//a[@class='linklnb']"
    )

    if hora_preferida and hora_preferida.lower() not in ("nan", ""):
        try:
            slot = wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//td[@class='agenda2']//a[contains(text(),'{hora_preferida}')]")
            ))
            slot.click()
            return hora_preferida
        except Exception:
            logger.warning(f"Slot '{hora_preferida}' não disponível, buscando aleatório.")

    disponiveis = driver.find_elements(By.XPATH, xpath_slots)
    if not disponiveis:
        logger.warning("Nenhum horário disponível na agenda.")
        return None

    escolhido = random.choice(disponiveis)
    hora = escolhido.text.strip()
    escolhido.click()
    logger.info(f"Horário aleatório selecionado: {hora}")
    return hora


def _confirmar_agendamento(driver, wait, hora_exame: str, tipo_compromisso: str,
                            email: str = None) -> None:
    """
    Preenche os campos finais do formulário de agendamento e confirma.
    `tipo_compromisso`: "1" = Admissional, "2" = Periódico, "3" = Demissional
    """
    time.sleep(3)
    Select(wait.until(EC.presence_of_element_located((By.ID, "horaInicialCombo")))).select_by_value(hora_exame)
    Select(wait.until(EC.presence_of_element_located((By.ID, "codigoCompromisso")))).select_by_value("1")
    Select(wait.until(EC.presence_of_element_located((By.ID, "tipoCompromisso")))).select_by_value(tipo_compromisso)

    if email:
        checkbox = wait.until(EC.presence_of_element_located((By.ID, "usaEmail")))
        if not checkbox.is_selected():
            checkbox.click()
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(@href,\"jemail('limpa')\")]")
        )).click()
        email_input = wait.until(EC.presence_of_element_located((By.ID, "destinoEmail")))
        email_input.clear()
        email_input.send_keys(email.lower().strip())

    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//a[contains(@href,\"doAcao('save')\")]//img | //img[contains(@src,'confirma.png')]")
    )).click()


def agendar_admissional(driver, wait, row: dict, janela_principal: str) -> str | None:
    """
    Executa o fluxo de agendamento admissional para um único funcionário.

    Parâmetros esperados em `row`:
        Nome, Matrícula Anterior, E-mail, Data Exame, Hora Exame (opcional)

    Retorna o horário agendado (str) ou None em caso de falha.
    """
    garantir_frame_principal(driver, wait)

    dia, mes, ano = _parsear_data_exame(row["Data Exame"])
    logger.info(f"Agendando admissional: {row['Nome']} — {dia}/{mes}/{ano}")

    _navegar_calendario(driver, wait, dia, mes, ano)

    matricula = str(row["Matrícula Anterior"]).strip()
    if not _buscar_funcionario_popup(driver, wait, janela_principal, row["Nome"], matricula):
        return None

    hora_pref = str(row.get("Hora Exame", "")).strip()[:5] if pd.notna(row.get("Hora Exame")) else None
    hora = _escolher_horario(driver, wait, hora_pref)
    if not hora:
        return None

    email = str(row.get("E-mail", "")).lower().strip()
    _confirmar_agendamento(driver, wait, hora, TIPO_ADMISSIONAL, email=email if email != "nan" else None)

    logger.info(f"Admissional agendado: {row['Nome']} — {hora}")
    return hora

def agendar_periodico(driver, wait, row: dict, janela_principal: str) -> str | None:
    """
    Executa o fluxo de agendamento periódico para um único funcionário.

    Parâmetros esperados em `row`:
        Nome, Matrícula, Exames (data), Hora (opcional)

    Retorna o horário agendado (str) ou None em caso de falha.
    """
    garantir_frame_principal(driver, wait)

    dia, mes, ano = _parsear_data_exame(row["Exames"])
    logger.info(f"Agendando periódico: {row['Nome']} — {dia}/{mes}/{ano}")

    _navegar_calendario(driver, wait, dia, mes, ano)

    matricula = str(row["Matrícula"]).strip().replace("/0", "")
    if not _buscar_funcionario_popup(driver, wait, janela_principal, row["Nome"], matricula):
        return None

    hora_pref = str(row.get("Hora", "")).strip()[:5] if pd.notna(row.get("Hora")) else None
    hora = _escolher_horario(driver, wait, hora_pref)
    if not hora:
        return None

    _confirmar_agendamento(driver, wait, hora, TIPO_PERIODICO)

    logger.info(f"Periódico agendado: {row['Nome']} — {hora}")
    return hora


def agendar_demissional(driver, wait, row: dict, janela_principal: str) -> str | None:
    """
    Executa o fluxo de agendamento demissional para um único funcionário.

    Parâmetros esperados em `row`:
        Nome, Matrícula Anterior, Data Exame

    Retorna o horário agendado (str) ou None em caso de falha.
    """
    garantir_frame_principal(driver, wait)

    dia, mes, ano = _parsear_data_exame(row["Data Exame"])
    logger.info(f"Agendando demissional: {row['Nome']} — {dia}/{mes}/{ano}")

    _navegar_calendario(driver, wait, dia, mes, ano)

    matricula = str(row["Matrícula Anterior"]).strip()
    if not _buscar_funcionario_popup(driver, wait, janela_principal, row["Nome"], matricula):
        return None

    hora = _escolher_horario(driver, wait, hora_preferida=None)
    if not hora:
        return None

    _confirmar_agendamento(driver, wait, hora, TIPO_DEMISSIONAL)

    logger.info(f"Demissional agendado: {row['Nome']} — {hora}")
    return hora