import os
import sys
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials 
from google.auth.transport.requests import Request
from config.loaders import get_config
from config_network import sessao_limpa
from services.logger_service import logger

class SheetsService:
    def __init__(self, nome_planilha=None):
        if nome_planilha is None:
            nome_planilha = get_config("google_sheets", "planilha")
        
        self.nome_da_planilha_drive = nome_planilha

        if getattr(sys, 'frozen', False):
            self.RAIZ_PROJETO = sys._MEIPASS
        else:
            diretorio_atual = os.path.dirname(os.path.abspath(__file__))
            self.RAIZ_PROJETO = os.path.dirname(diretorio_atual)

        self.PATH_TO_JSON = os.path.join(self.RAIZ_PROJETO, "config", "credentials.json")
        
        logger.info(f"🔍 Conectando à planilha via: {self.PATH_TO_JSON}")
        self.planilha = self._conectar(self.nome_da_planilha_drive)

    def _conectar(self, nome_planilha):
        creds = Credentials.from_service_account_file(
            self.PATH_TO_JSON, 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        
        try:
            client.session = sessao_limpa
        except Exception:
            pass 
        
        return client.open(nome_planilha)

    def atualizar_planilha_mestra(self, caminho_excel_local):
        """Lê o Excel local e sobrescreve a aba no Google Sheets."""
        try:
            nome_aba = get_config("google_sheets", "aba")
            
            logger.info(f"📂 Lendo arquivo local: {caminho_excel_local}")
            df = pd.read_excel(caminho_excel_local).fillna('')
            dados_envio = [df.columns.values.tolist()] + df.values.tolist()

            logger.info(f"🌐 Acessando aba: {nome_aba}")
            aba_destino = self.planilha.worksheet(nome_aba)
            
            logger.info(f"🧹 Limpando dados e enviando {len(df)} linhas...")
            aba_destino.clear()
            aba_destino.update('A1', dados_envio)
            
            return True, "✅ Sincronização concluída com sucesso!"
            
        except Exception as e:
            msg_erro = f"Falha no SheetsService: {str(e)}"
            return False, msg_erro