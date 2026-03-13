"""
modules/betha/atestados.py

Gera relatório Excel de atestados por nome de funcionário.
"""
import os
import pandas as pd
from datetime import datetime

from config.loaders import get_workspace, Endpoint
from services.betha_service import get
from services.logger_service import logger

OUTPUT_DIR = get_workspace(os.path.join("relatorios", "saida", "atestados"))
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _buscar_atestados(nome: str, limit: int = 100) -> list:
    filtro = f'(matricula.pessoa.nome elike "%25{nome}%25") or matricula.id is null'
    data = get(Endpoint.BETHA_ATESTADO, params={"filter": filtro, "limit": limit, "offset": 0})
    return data.get("content", [])


def _formatar_data(data_iso: str | None) -> str | None:
    if not data_iso:
        return None
    return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")


def gerar_relatorio(nome: str) -> None:
    logger.info(f"Buscando atestados: {nome}")
    registros = _buscar_atestados(nome)

    if not registros:
        logger.warning(f"Nenhum atestado encontrado para {nome}.")
        return

    linhas = []
    matricula = "-"

    for item in registros:
        matricula = (item.get("matricula", {})
                        .get("codigoMatricula", {})
                        .get("numero", "-"))

        profissional = item.get("profissional", {})
        nome_prof    = profissional.get("nome", "-")
        num_conselho = profissional.get("numeroConselho")
        orgao        = profissional.get("formacao", {}).get("orgaoClasse")
        conselho     = f"{num_conselho}-{orgao}" if num_conselho and orgao else "-"

        cid = "-"
        if item.get("cidPrincipal"):
            cid = item["cidPrincipal"].get("codigo", "-")
        elif item.get("cids"):
            cid = item["cids"][0].get("codigo", "-")

        linhas.append({
            "Data inicial": _formatar_data(item.get("inicioAtestado")),
            "Data final":   _formatar_data(item.get("fimAtestado")) or "Em andamento",
            "Dias":         item.get("duracao") or "-",
            "Tipo":         item.get("tipo", {}).get("descricao", "-"),
            "Profissional": nome_prof,
            "Registro":     conselho,
            "CID":          cid,
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