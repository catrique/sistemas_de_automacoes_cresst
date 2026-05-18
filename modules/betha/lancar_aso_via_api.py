import os
import time
import unicodedata
import requests
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from config.loaders import get_endpoint, get_config, Endpoint
from services.logger_service import logger

ID_INSTITUICAO_MEDICA = 19571408
ID_FORMULARIO_ASO = 200
TIPO_CAMPO_FORMULARIO = "6556208eaefc8c0001528199"


class IntegracaoBethaRH:
    def __init__(self):
        self.base_url = get_endpoint(Endpoint.BETHA_BASE)
        self.headers = {
            "Authorization": get_config("betha", "api", "authorization"),
            "User-Access": get_config("betha", "api", "user_access"),
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Origin": "https://rh.betha.cloud"
        }

    def _montar_url(self, endpoint: Endpoint) -> str:
        """Monta a URL completa a partir de um Endpoint."""
        return f"{self.base_url}{get_endpoint(endpoint)}"

    def buscar_registros(self, endpoint: Endpoint, filtro_str: str) -> list:
        """Faz a requisição GET genérica usando os filtros informados."""
        url = self._montar_url(endpoint)
        params = {"filter": filtro_str, "limit": 50, "offset": 0}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get("content", [])

    def buscar_pessoa_fisica(self, nome: str, cpf_excel: str) -> dict | None:
        """Busca pessoa pelo nome e filtra o resultado pelo CPF exato."""
        filtro = f'(nome like "%25{nome.strip()}%25")'
        resultados = self.buscar_registros(Endpoint.BETHA_PESSOA_FISICA, filtro)
        for p in resultados:
            if p.get("cpf") == str(cpf_excel).strip():
                return p
        return None

    def buscar_matricula(self, pessoa_id: int, nome: str, matricula_excel: str) -> tuple:
        """Busca matrícula pelo pessoa_id e filtra pela descrição exata."""
        filtro = f'pessoaNome like "%25%25" and pessoa = {pessoa_id}'
        resultados = self.buscar_registros(Endpoint.BETHA_MATRICULA, filtro)
        for m in resultados:
            if m.get("descricao") == str(matricula_excel).strip():
                return m, m.get("dataInicioContrato")
        return None, None

    def buscar_medico(self, nome_medico: str) -> dict | None:
        """Busca o profissional médico pelo nome e retorna o primeiro resultado."""
        filtro = f'(nome like "%25{nome_medico}%25" and profissao = "MEDICO")'
        resultados = self.buscar_registros(Endpoint.BETHA_PROFISSIONAL, filtro)
        return resultados[0] if resultados else None

    def verificar_aso_existente(
        self,
        nome_funcionario: str,
        matricula_excel: str,
        tipo_exame_excel: str,
        resultado_excel: str,
        data_exame_excel: str,
    ) -> bool:
        """
        Verifica se o ASO já existe no sistema para evitar duplicidade.
        Retorna True se encontrar um registro idêntico.
        """
        dt_exame_api = datetime.strptime(data_exame_excel, "%d/%m/%Y").strftime("%Y-%m-%d")
        nome_busca = nome_funcionario.strip().upper()

        url = self._montar_url(Endpoint.BETHA_ASO)
        params = {
            "filter": (
                f"((pessoa.nome elike '%25{nome_busca}%25')) and "
                f"(conclusaoAso in ('APTO','APTO_COM_RESTRICOES','INAPTO','INCONCLUSIVO'))"
            ),
            "limit": 20,
            "offset": 0,
            "situacao": ["VALIDO", "PROXIMO_DO_VENCIMENTO", "VENCIDO"],
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            conteudo = response.json().get("content", [])

            for aso in conteudo:
                if (
                    str(aso.get("matricula", {}).get("descricao")) == str(matricula_excel).strip()
                    and str(aso.get("tipoExameAso")) == str(tipo_exame_excel.replace(" AO ", "_").upper()).strip().upper()
                    and str(aso.get("conclusaoAso")) == str(resultado_excel).strip().upper()
                    and str(aso.get("data")) == dt_exame_api
                ):
                    logger.info(f"ASO já encontrado no sistema (ID: {aso.get('id')})")
                    return True

            return False

        except Exception as e:
            logger.error(f"Erro ao verificar existência do ASO: {e}")
            return False

    def calcular_datas(
        self,
        data_str: str,
        resultado: str,
        tipo_exame: str,
        data_admissao: str,
    ) -> tuple:
        """Calcula as datas de exame, início de atividades e validade do ASO."""
        dt_exame = datetime.strptime(data_str, "%d/%m/%Y")
        data_formatada = dt_exame.strftime("%Y-%m-%d")

        tipo_exame_limpo = str(tipo_exame).strip().upper().replace(" ", "_")
        resultado_limpo = str(resultado).strip().upper()

        if tipo_exame_limpo == "DEMISSIONAL":
            data_inicio_atv = data_admissao
        else:
            dias_offset = 3 if dt_exame.weekday() == 4 else 1
            data_inicio_atv = (dt_exame + timedelta(days=dias_offset)).strftime("%Y-%m-%d")

        if tipo_exame_limpo == "DEMISSIONAL":
            dt_validade = dt_exame + relativedelta(months=3)
        elif resultado_limpo == "APTO":
            dt_validade = dt_exame + relativedelta(years=1)
        else:
            dt_validade = dt_exame + relativedelta(months=3)

        data_validade_aso = dt_validade.strftime("%Y-%m-%d")

        return data_formatada, data_inicio_atv, data_validade_aso

    def criar_aso_parcial(self, dados_base: dict) -> dict:
        """Cria o ASO com dados obrigatórios (parcial)."""
        url = self._montar_url(Endpoint.BETHA_ASO)
        time.sleep(3)  
        response = requests.post(url, headers=self.headers, json=dados_base)
        response.raise_for_status()
        return response.json()

    def atualizar_aso_completo(self, aso_id: int, dados_completos: dict) -> dict:
        """Atualiza o ASO com todas as informações finais via PUT."""
        url = f"{self._montar_url(Endpoint.BETHA_ASO)}/{aso_id}"
        time.sleep(3)  
        response = requests.put(url, headers=self.headers, json=dados_completos)
        response.raise_for_status()
        return response.json()

    def enviar_anexo(self, pdf_path: str) -> dict:
        """Envia o arquivo PDF e retorna o objeto do anexo."""
        url = self._montar_url(Endpoint.BETHA_ANEXO)
        headers_file = {k: v for k, v in self.headers.items() if k != "Content-Type"}
        nome_arquivo = os.path.basename(pdf_path)

        with open(pdf_path, "rb") as f:
            time.sleep(3) 
            response = requests.post(
                url,
                headers=headers_file,
                files={"arquivo": (nome_arquivo, f, "application/pdf")},
            )

        if response.status_code != 200:
            logger.error(f"Erro no envio do anexo: {response.text}")

        response.raise_for_status()
        dados = response.json()
        return dados[0] if isinstance(dados, list) and dados else dados

    def vincular_formulario_aso(self, aso_id: int) -> bool:
        """Vincula o formulário ASO-EXTERNO ao ASO criado."""
        url = self._montar_url(Endpoint.BETHA_ASO_FORMULARIO)
        payload = {
            "id": None,
            "aso": {"id": aso_id},
            "formulario": {
                "id": ID_FORMULARIO_ASO,
                "descricao": "ASO-EXTERNO",
                "desabilitado": False,
                "tipoCampo": TIPO_CAMPO_FORMULARIO,
            },
            "campoAdicional": [],
            "version": None,
        }
        time.sleep(3) 
        # print(f"URL: {url}, headers: {self.headers}, payload: {payload}")
        response = requests.post(url, headers=self.headers, json=payload)
        return response.status_code == 200


def remover_acentos(texto: str) -> str:
    """Remove acentos de uma string usando normalização Unicode."""
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def normalizar_tipo_exame(tipo_exame_raw) -> str:
    """
    Converte o tipo de exame da planilha para o formato aceito pela API.

    Regras:
    - Converte para string, remove espaços e coloca em MAIÚSCULO
    - Remove acentos
    - Apenas dois valores sofrem transformação:
        RETORNO AO TRABALHO -> RETORNO_TRABALHO
        MUDANÇA DE FUNÇÃO   -> MUDANCA_FUNCAO
    - Demais valores retornam apenas normalizados
    """
    if tipo_exame_raw is None:
        return ""

    s = str(tipo_exame_raw).strip().upper()
    s = remover_acentos(s)

    if s == "RETORNO AO TRABALHO":
        return "RETORNO_TRABALHO"

    if s == "MUDANCA DE FUNCAO":
        return "MUDANCA_FUNCAO"

    return s


def carregar_planilha(caminho_planilha: str) -> pd.DataFrame | None:
    """Carrega a planilha e garante as colunas de controle."""
    try:
        df = pd.read_excel(caminho_planilha)
        for coluna in ("Status", "Detalhes_Erro"):
            if coluna not in df.columns:
                df[coluna] = ""
        return df
    except Exception as e:
        logger.error(f"Erro ao abrir planilha: {e}")
        return None


def salvar_progresso(df: pd.DataFrame, index: int, caminho_planilha: str) -> None:
    """Salva o DataFrame no Excel e informa o resultado."""
    try:
        df.to_excel(caminho_planilha, index=False)
        logger.info(f"Linha {index} salva no Excel.")
    except PermissionError:
        logger.warning(f"Não foi possível salvar a linha {index} — feche o Excel e tente novamente.")
    except Exception as e:
        logger.error(f"Erro ao salvar progresso: {e}")


def registrar_status(df: pd.DataFrame, index: int, status: str, detalhe: str) -> None:
    """Atualiza as colunas de status no DataFrame."""
    df.at[index, "Status"] = status
    df.at[index, "Detalhes_Erro"] = detalhe


def processar_lote(api: IntegracaoBethaRH, df: pd.DataFrame, tipo_selecionado: str, caminho_planilha: str) -> None:
    """Filtra e processa os registros conforme o tipo de exame escolhido."""
    if tipo_selecionado != "TODOS":
        df_filtrado = df[df["Tipo Exame"].str.upper() == tipo_selecionado]
        logger.info(f"Filtrado: {len(df_filtrado)} registros de '{tipo_selecionado}'.")
    else:
        df_filtrado = df
        logger.info(f"Processando TODOS os tipos ({len(df_filtrado)} registros).")

    if df_filtrado.empty:
        logger.warning("Nenhum registro encontrado para a opção selecionada.")
        return

    for index, row in df_filtrado.iterrows():
        if row["Status"] == "SUCESSO":
            continue
        if row["Status"] == "ERRO":
            continue

        try:
            logger.info(f"[{index}] Analisando: {row['Funcionário']}")

            ja_existe = api.verificar_aso_existente(
                nome_funcionario=row["Funcionário"],
                matricula_excel=row["Matrícula"],
                tipo_exame_excel=row["Tipo Exame"].replace("_AO_", "_").upper(),
                resultado_excel=row["Resultado"],
                data_exame_excel=row["Data Exame"],
            )
            if ja_existe:
                registrar_status(df, index, "SUCESSO", "Registro já existente no sistema (Ignorado)")
                salvar_progresso(df, index, caminho_planilha)
                continue

            tipo_exame_api = normalizar_tipo_exame(row["Tipo Exame"])
            logger.info(f"Tipo de exame: {tipo_exame_api}")

            cpf_limpo = str(row["CPF"]).replace(".", "").replace("-", "")
            pessoa = api.buscar_pessoa_fisica(row["Funcionário"], cpf_limpo)
            if not pessoa:
                registrar_status(df, index, "ERRO", "Pessoa não encontrada ou CPF não bate")
                salvar_progresso(df, index, caminho_planilha)
                logger.warning(f"Pessoa não encontrada ou CPF não bate para {row['Funcionário']}. Pulando...")
                continue

            matricula, data_inicio_contrato = api.buscar_matricula(
                pessoa["id"], row["Funcionário"], row["Matrícula"]
            )
            if not matricula:
                registrar_status(df, index, "ERRO", "Matrícula não encontrada")
                salvar_progresso(df, index, caminho_planilha)
                logger.warning(f"Matrícula não encontrada para {row['Funcionário']}. Pulando...")
                continue

            logger.info(f"Data de início do contrato: {data_inicio_contrato}")

            data_formatada, inicio_atv, validade_aso = api.calcular_datas(
                row["Data Exame"],
                row["Resultado"],
                row["Tipo Exame"],
                data_inicio_contrato,
            )

            dados_parciais = {
                "data": data_formatada,
                "encaminhamentoAso": "NENHUMA",
                "conclusaoAso": "INCONCLUSIVO",
                "dataValidadeAso": data_formatada,
                "tipoExameAso": tipo_exame_api,
                "reabilitado": False,
                "matricula": {"id": matricula["id"]},
                "pessoaFisica": {"id": pessoa["id"]},
                "isSaveParcial": True,
            }
            logger.info(f"Criando ASO parcial para {row['Funcionário']}...")
            aso_criado = api.criar_aso_parcial(dados_parciais)
            aso_id = aso_criado["id"]

            med_examinador = api.buscar_medico(row["Médico Examinador"])
            if not med_examinador:
                registrar_status(df, index, "ERRO", "Médico Examinador não encontrado")
                salvar_progresso(df, index, caminho_planilha)
                logger.warning(f"Médico Examinador não encontrado. Pulando {row['Funcionário']}...")
                continue

            med_pcmso = api.buscar_medico(row["Médico PCMSO"])
            if not med_pcmso:
                registrar_status(df, index, "ERRO", "Médico PCMSO não encontrado")
                salvar_progresso(df, index, caminho_planilha)
                logger.warning(f"Médico PCMSO não encontrado. Pulando {row['Funcionário']}...")
                continue

            anexo_info = api.enviar_anexo(row["pdf_path"])

            resultado_limpo = str(row["Resultado"]).strip().upper()
            dados_completos = {
                **dados_parciais,
                "id": aso_id,
                "conclusaoAso": resultado_limpo,
                "dataValidadeAso": validade_aso,
                "dataInicioAtividades": inicio_atv,
                "isSaveParcial": False,
                "medicoResponsavel": {"id": med_examinador["id"]},
                "medicoResponsavelPcmso": {"id": med_pcmso["id"]},
                "instituicaoMedica": {"id": ID_INSTITUICAO_MEDICA},
                "anexos": [
                    {
                        "data": data_formatada,
                        "tipoDocumento": {"id": 1780},
                        "arquivos": [
                            {
                                "id": anexo_info["id"],
                                "name": anexo_info["name"],
                                "key": anexo_info["key"],
                            }
                        ],
                    }
                ],
                "formulario": {
                    "aso": {"id": aso_id},
                    "formulario": {"id": ID_FORMULARIO_ASO},
                    "campoAdicional": [],
                },
            }

            logger.info(f"Atualizando ASO com dados completos (ID: {aso_id})...")
            api.atualizar_aso_completo(aso_id, dados_completos)

            sucesso_form = api.vincular_formulario_aso(aso_id)
            if sucesso_form:
                registrar_status(df, index, "SUCESSO", f"ASO ID: {aso_id}")
                salvar_progresso(df, index, caminho_planilha)
                logger.info(f"✅ {row['Funcionário']} finalizado com sucesso.")
            else:
                raise Exception("Falha ao vincular formulário (status != 200).")

        except requests.exceptions.HTTPError as e:
            corpo_erro = e.response.text
            logger.error(f"ERRO DA API para {row['Funcionário']}: {corpo_erro}")
            registrar_status(df, index, "ERRO", f"API: {corpo_erro}")


def executar(caminho_planilha: str, tipo_selecionado: str = "TODOS") -> None:
    """
    Ponto de entrada chamado pela interface gráfica.

    Args:
        caminho_planilha: Caminho absoluto para o arquivo .xlsx de entrada.
        tipo_selecionado: Tipo de exame a processar (ex: 'ADMISSIONAL', 'TODOS').
    """
    logger.info(f"Iniciando lançamento de ASOs — tipo: {tipo_selecionado} | planilha: {caminho_planilha}")

    df = carregar_planilha(caminho_planilha)
    if df is None:
        logger.error("Planilha não pôde ser carregada. Encerrando.")
        return

    api = IntegracaoBethaRH()
    processar_lote(api, df, tipo_selecionado, caminho_planilha)

    logger.info("✅ Processamento concluído.")