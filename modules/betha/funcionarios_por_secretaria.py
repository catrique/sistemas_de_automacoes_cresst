"""
modules/betha/funcionarios_por_secretaria.py

Gera relatório Excel de funcionários filtrados por secretaria/lotação.
"""
import os
import pandas as pd
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.loaders import get_workspace, Endpoint
from services.betha_service import get, paginar
from services.utils.secretarias_service import carregar_secretarias, buscar_por_texto
from services.logger_service import logger

OUTPUT_DIR  = get_workspace(os.path.join("relatorios", "saida"))
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "funcionarios_por_secretaria.xlsx")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MAX_WORKERS = 10
HOJE = date.today()


def _calcular_idade(data_nascimento) -> int | str:
    try:
        dn = pd.to_datetime(data_nascimento).date()
        return HOJE.year - dn.year - ((HOJE.month, HOJE.day) < (dn.month, dn.day))
    except Exception:
        return ""


def _buscar_detalhe_matricula(matricula_id: int) -> dict:
    try:
        data = get(f"matricula/{matricula_id}")
        pessoa = data.get("pessoa") or {}
        return {
            "nome":  pessoa.get("nome", ""),
            "cpf":   pessoa.get("cpf", ""),
            "Sexo":  pessoa.get("sexo"),
            "idade": _calcular_idade(pessoa.get("dataNascimento")),
        }
    except Exception:
        return {"nome": "", "cpf": "", "Sexo": "", "idade": ""}


def _corresponde_lotacao(numero_mascarado: str, codigo: str) -> bool:
    if not numero_mascarado or not codigo:
        return False
    if codigo.count(".") == 1:
        return numero_mascarado == codigo or numero_mascarado.startswith(codigo + ".")
    return numero_mascarado == codigo


def _menu_secretarias() -> None:
    while True:
        termo = input("\nDigite parte do nome (ou S para sair): ").strip()
        if termo.upper() == "S":
            return
        resultados = buscar_por_texto(termo)
        if not resultados:
            print("❌ Nenhum resultado.")
            continue
        for cod, dados in resultados.items():
            print(f"\n  {dados['descricao']} ({cod})")
            for lot in dados["lotacoes"]:
                print(f"      └ {lot['descricao']} — {lot['numero']}")


def _obter_prefixo() -> str:
    while True:
        resp = input("\nVocê já possui o código? (1 = sim | 0 = não): ").strip()
        if resp == "1":
            return input("Código (ex: 02.18): ").strip()
        if resp == "0":
            _menu_secretarias()
        else:
            print("❌ Opção inválida.")


def executar(prefixo: str = None) -> None:
    if not prefixo:
        prefixo = _obter_prefixo()
    if not prefixo:
        return

    logger.info(f"Buscando matrículas ativas — prefixo: {prefixo}")
    todos = paginar(Endpoint.BETHA_LISTAGEM_MATRICULA, params={"filtroSituacao": "ATIVOS"})

    filtrados = [
        r for r in todos
        if _corresponde_lotacao(
            ((r.get("matriculaLotacaoFisica") or {}).get("lotacaoFisica") or {})
            .get("numeroMascarado", ""),
            prefixo,
        )
    ]

    logger.info(f"{len(filtrados)} matrículas encontradas para '{prefixo}'.")

    detalhes = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_buscar_detalhe_matricula, r["id"]): r["id"]
            for r in filtrados if r.get("id")
        }
        for future in as_completed(futures):
            detalhes[futures[future]] = future.result()

    linhas = []
    for r in filtrados:
        pessoa = detalhes.get(r.get("id"), {})
        lf = ((r.get("matriculaLotacaoFisica") or {}).get("lotacaoFisica") or {})
        linhas.append({
            "Nome":             pessoa.get("nome", ""),
            "CPF":              pessoa.get("cpf", ""),
            "Idade":            pessoa.get("idade", ""),
            "Sexo":             pessoa.get("Sexo", ""),
            "Cargo":            (r.get("cargo") or {}).get("descricao", ""),
            "Matrícula":        r.get("numeroCartaoPonto") or "",
            "Lotação Física":   lf.get("descricao", ""),
            "Número Mascarado": lf.get("numeroMascarado", ""),
            "Situação":         r.get("situacao", ""),
            "Data de Admissão": r.get("dataInicioContrato"),
            "Data de Saída":    r.get("dataFinal") or r.get("dataRescisao", ""),
        })

    df = pd.DataFrame(linhas)
    for col in ["Data de Admissão", "Data de Saída"]:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")

    df.to_excel(OUTPUT_PATH, index=False)
    logger.info(f"✅ Arquivo gerado: {OUTPUT_PATH}")
    print(f"\n✅ Arquivo gerado: {OUTPUT_PATH}")


if __name__ == "__main__":
    executar()