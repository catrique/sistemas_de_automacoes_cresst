import os
import ctypes
import socket
from datetime import datetime
import pandas as pd

def obter_identificacao_usuario():
    """Retorna um dicionário com Nome/Login, IP e Horário do sistema."""
    dados = {
        "usuario": "USUARIO",
        "ip": "0.0.0.0",
        "horario": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

    try:
        buffer = ctypes.create_unicode_buffer(100)
        tamanho = ctypes.pointer(ctypes.c_uint32(100))
        
        if ctypes.windll.secur32.GetUserNameExW(3, buffer, tamanho) and buffer.value:
            dados["usuario"] = buffer.value
        else:
            dados["usuario"] = os.getlogin()
    except:
        dados["usuario"] = os.environ.get('USERNAME', 'USUARIO')

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        dados["ip"] = s.getsockname()[0]
        s.close()
    except:
        try:
            dados["ip"] = socket.gethostbyname(socket.gethostname())
        except:
            pass 

    return dados


def gerar_nome_pasta(data_inicial: str, data_final: str) -> str:
        inicial_formatada = data_inicial[:5].replace('/', '-')
        final_formatada = data_final[:5].replace('/', '-')
        return f"ASOS_{inicial_formatada}_a_{final_formatada}"

def gerar_txt_retorno_trabalho(df: pd.DataFrame, pasta_destino: str) -> None:
    """
    Recebe o DataFrame do relatório já gerado, filtra os 'Retorno ao Trabalho'
    e salva Lista_Retorno_Trabalho.txt na pasta informada.
    """
    retornos = df[df['Tipo Exame'].str.lower().str.contains('retorno', na=False)]

    if retornos.empty:
        print("ℹ️  Nenhum 'Retorno ao Trabalho' encontrado para gerar TXT.")
        return

    aptos   = sorted(retornos[~retornos['Resultado'].str.contains('INAPTO', na=False)]['Funcionário'].tolist())
    inaptos = sorted(retornos[ retornos['Resultado'].str.contains('INAPTO', na=False)]['Funcionário'].tolist())

    caminho_txt = os.path.join(pasta_destino, "Lista_Retorno_Trabalho.txt")

    with open(caminho_txt, 'w', encoding='utf-8') as f:
        f.write("Bom dia Leonardo!\n")
        f.write("Informo o retorno ao trabalho dos seguintes servidores, conforme avaliação:\n\n")

        f.write("APTOS:\n")
        f.writelines(f"- {nome}\n" for nome in aptos) if aptos else f.write("(Nenhum)\n")

        f.write("\n" + "-" * 40 + "\n\n")

        f.write("INAPTOS:\n")
        f.writelines(f"- {nome}\n" for nome in inaptos) if inaptos else f.write("(Nenhum)\n")

    print(f"✅ Lista de retorno salva em: {caminho_txt}")