import os
import sys
import shutil
import re
import unicodedata
import pandas as pd
from datetime import datetime

from services.utils.utils_service import gerar_txt_retorno_trabalho

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

try:
    from .leitor_pdf import extrair_dados_pdf
except ImportError:
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from services.utils.leitor_pdf import extrair_dados_pdf
    except ImportError:
        print("Erro critico: Nao foi possivel importar leitor_pdf.py")
        sys.exit(1)

DOWNLOADS_ROOT = os.path.join(BASE_DIR, "workspace", "downloads", "Asos") # Adicionado "Asos"

MAPEAMENTO_TIPO_EXAME = {
    "admissional": "Admissional",
    "periódico": "Periódico",
    "periodico": "Periódico",
    "retorno": "Retorno ao Trabalho",
    "mudança": "Mudança de Função",
    "mudanca": "Mudança de Função",
    "demissional": "Demissional"
}

COLUNAS_RELATORIO = [
    "Funcionário", "CPF", "Matrícula", "Cargo", "Tipo Exame", 
    "Resultado", "Data Exame", "Data de Início", 
    "Médico Examinador", "Médico PCMSO", "pdf_path"
]


def formatar_nome_arquivo(nome):
    """
    Transforma 'José Augusto' em 'jose_augusto'.
    Remove acentos, coloca em minúsculo e substitui espaços por underline.
    """
    if not nome: return "desconhecido"
    
    nfkd_form = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    nome_limpo = re.sub(r'[^a-zA-Z0-9\s]', '', nome_sem_acento)
    
    return nome_limpo.lower().strip().replace(' ', '_')

def formatar_data_arquivo(data_str):
    """
    Transforma '21/09/2025' em '21-09-25'.
    """
    if not data_str:
        return datetime.now().strftime("%d-%m-%y")
    
    try:
        dt = datetime.strptime(data_str, "%d/%m/%Y")
        return dt.strftime("%d-%m-%y")
    except ValueError:
        return datetime.now().strftime("%d-%m-%y")

def mapear_tipo_exame(tipo_exame_pdf):
    if not tipo_exame_pdf: return "Outros"
    tipo_lower = tipo_exame_pdf.lower()
    for chave, valor in MAPEAMENTO_TIPO_EXAME.items():
        if chave in tipo_lower:
            return valor
    return "Outros"

def selecionar_pasta_download():
    if not os.path.exists(DOWNLOADS_ROOT):
        return None
    
    subdirs = [d for d in os.listdir(DOWNLOADS_ROOT) if os.path.isdir(os.path.join(DOWNLOADS_ROOT, d))]
    
    if not subdirs:
        return None
        
    subdirs.sort(key=lambda x: os.path.getmtime(os.path.join(DOWNLOADS_ROOT, x)), reverse=True)
    
    print("\nPastas encontradas:")
    for i, folder in enumerate(subdirs):
        print(f"{i + 1} - {folder}")
            
    return os.path.join(DOWNLOADS_ROOT, subdirs[0])

def executar(diretorio_especifico=None):
    if diretorio_especifico:
        pasta_alvo = diretorio_especifico
    else:
        pasta_alvo = selecionar_pasta_download()
    
    if not pasta_alvo:
        print("Nenhuma pasta selecionada ou encontrada.")
        return

    print(f"\n📂 [ORGANIZADOR] Processando pasta: {os.path.basename(pasta_alvo)}")

    subpastas = {
        "Retorno ao Trabalho": os.path.join(pasta_alvo, "Retorno ao Trabalho"),
        "Admissional": os.path.join(pasta_alvo, "Admissional"),
        "Demissional": os.path.join(pasta_alvo, "Demissional"),
        "Periódico": os.path.join(pasta_alvo, "Periódico"),
        "Mudança de Função": os.path.join(pasta_alvo, "Mudança de Função"),
        "Outros": os.path.join(pasta_alvo, "Outros"),
        "Erro": os.path.join(pasta_alvo, "Erro")
    }

    arquivos = [f for f in os.listdir(pasta_alvo) if f.lower().endswith('.pdf')]
    print(f"📄 Total de arquivos PDF na raiz: {len(arquivos)}")

    count_sucesso = 0
    count_erro = 0
    dados_para_excel = []
    
    for i, arquivo in enumerate(arquivos):
        caminho_origem = os.path.join(pasta_alvo, arquivo)
        print(f"[{i+1}/{len(arquivos)}] {arquivo}...", end="")

        dados_arquivo = {col: "" for col in COLUNAS_RELATORIO}
        
        try:
            dados = extrair_dados_pdf(caminho_origem, debug=False)
            
            if not dados or not dados.get('Funcionario'):
                destino = subpastas["Erro"]
                count_erro += 1
                print(" -> ❌ Ilegivel")
                
                dados_arquivo["Funcionário"] = f"ERRO LEITURA - {arquivo}"
                if not os.path.exists(destino): os.makedirs(destino)
                caminho_final = os.path.join(destino, arquivo)
                shutil.move(caminho_origem, caminho_final)
                dados_arquivo["pdf_path"] = caminho_final
            else:
                nome_bruto = dados.get('Funcionario', '')
                tipo_raw = dados.get('Tipo_Exame', '')
                data_bruta = dados.get('Data_Exame_Clinico', '')
                
                tipo_identificado = mapear_tipo_exame(tipo_raw)
                
                if tipo_identificado in subpastas:
                    destino = subpastas[tipo_identificado]
                else:
                    destino = subpastas["Outros"]
                
                if not os.path.exists(destino):
                    os.makedirs(destino)

                nome_fmt = formatar_nome_arquivo(nome_bruto).upper()
                data_fmt = formatar_data_arquivo(data_bruta)
                
                novo_nome_arquivo = f"{nome_fmt}_{data_fmt}.pdf"
                caminho_final = os.path.join(destino, novo_nome_arquivo)
                
                contador = 1
                while os.path.exists(caminho_final):
                    novo_nome_arquivo = f"{nome_fmt}_{data_fmt}_{contador}.pdf"
                    caminho_final = os.path.join(destino, novo_nome_arquivo)
                    contador += 1

                shutil.move(caminho_origem, caminho_final)
                
                count_sucesso += 1
                print(f" -> ✅ {novo_nome_arquivo}")

                dados_arquivo["Funcionário"] = nome_bruto.upper()
                dados_arquivo["CPF"] = dados.get('CPF', '')
                dados_arquivo["Matrícula"] = dados.get('Matricula', '')
                dados_arquivo["Cargo"] = dados.get('Cargo', '')
                dados_arquivo["Tipo Exame"] = tipo_identificado
                dados_arquivo["Resultado"] = (dados.get('Resultado_Exame') or 'APTO').upper()
                dados_arquivo["Data Exame"] = data_bruta
                dados_arquivo["Data de Início"] = ""
                dados_arquivo["Médico Examinador"] = dados.get('Medico_Examinador_ASO', '')
                dados_arquivo["Médico PCMSO"] = dados.get('Medico_PCMSO', '')
                dados_arquivo["pdf_path"] = caminho_final

            dados_para_excel.append(dados_arquivo)

        except Exception as e:
            print(f" -> ❌ Erro: {e}")
            count_erro += 1
            try:
                if not os.path.exists(subpastas["Erro"]): os.makedirs(subpastas["Erro"])
                shutil.move(caminho_origem, os.path.join(subpastas["Erro"], arquivo))
            except: pass

    for pasta in subpastas.values():
        if os.path.exists(pasta) and not os.listdir(pasta):
            try:
                os.rmdir(pasta)
            except: pass

    if dados_para_excel:
        print("\n📊 Gerando Relatório_Completo.xlsx...")
        try:
            df = pd.DataFrame(dados_para_excel)
            df = df.reindex(columns=COLUNAS_RELATORIO)
            
            caminho_excel = os.path.join(pasta_alvo, "Relatorio_Completo.xlsx")
            df.to_excel(caminho_excel, index=False)
            print(f"✅ Arquivo salvo em: {caminho_excel}")
            gerar_txt_retorno_trabalho(df, pasta_alvo)
        except Exception as e:
            print(f"❌ Erro ao salvar Excel: {e}")
    else:
        print("⚠️ Nenhum dado para gerar relatório.")

    print("\n" + "="*50)
    print("RESUMO DA ORGANIZACAO")
    print("="*50)
    print(f"Arquivos processados/renomeados: {count_sucesso}")
    if count_erro > 0:
        print(f"⚠️  ALERTA: {count_erro} arquivos com erro (ver pasta 'Erro').")
    else:
        print("Sucesso total! Nenhum erro encontrado.")
    print("="*50)

if __name__ == "__main__":
    executar()