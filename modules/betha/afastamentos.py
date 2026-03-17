import os
import pandas as pd
from datetime import datetime

from config.loaders import get_workspace, Endpoint
from services.betha_service import get
from services.logger_service import logger

OUTPUT_DIR = get_workspace(os.path.join("relatorios", "saida", "afastamentos"))
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _buscar_afastamentos(nome: str, limit: int = 100) -> list:
    filtro = (
        f'(matricula.pessoa.nome elike "%25{nome}%25") '
        f'or matricula.id is null '
        f'or matricula.pessoa.cpf = "{nome}" '
        f'or (matricula.numeroCartaoPonto elike "%25{nome}%25")'
    )
    data = get(Endpoint.BETHA_AFASTAMENTOS, params={"filter": filtro, "limit": limit, "offset": 0})
    return data.get("content", [])


def _formatar_data(data_iso: str | None) -> str | None:
    if not data_iso:
        return None
    return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")


def gerar_relatorio(nome: str) -> None:
    logger.info(f"Buscando afastamentos: {nome}")
    registros = _buscar_afastamentos(nome)

    if not registros:
        logger.warning(f"Nenhum afastamento encontrado para {nome}.")
        return

    linhas = []
    matricula = "-"

    for item in registros:
        cod = item["matricula"]["codigoMatricula"]
        matricula = f"{cod['numero']}/{cod['contrato']}" if cod.get("contrato") else cod["numero"]
        linhas.append({
            "Matricula":           matricula,
            "Data inicial":        _formatar_data(item.get("inicioAfastamento")),
            "Data final":          _formatar_data(item.get("fimAfastamento")) or "Em andamento",
            "Quantidade":          item.get("quantidadeDias") or "-",
            "Decorrência":         item.get("decorrente"),
            "Tipo de afastamento": item["tipoAfastamento"]["descricao"],
        })

    df = pd.DataFrame(linhas)
    nome_arquivo = f"{nome.replace(' ', '_')}_{datetime.now().strftime('%d_%m_%y')}.xlsx"
    caminho = os.path.join(OUTPUT_DIR, nome_arquivo)

    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=f"{nome} - {matricula}"[:31], index=False)

    logger.info(f"✅ Relatório salvo: {caminho}")


def executar() -> None:
    entrada = input("Nome(s) separados por vírgula: ").strip()
    if not entrada:
        print("❌ Nenhum nome informado.")
        return
    for nome in [n.strip().upper() for n in entrada.split(",") if n.strip()]:
        gerar_relatorio(nome)


if __name__ == "__main__":
    executar()