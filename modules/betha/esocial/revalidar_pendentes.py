"""
Orquestra o fluxo completo de revalidação de pendentes no eSocial.

Fluxo:
  1. Busca todos os domínios PENDENTES
  2. Trata a lista bruta → [{id, situacao, situacaoEsocial, descricao, vigenteDesde}]
  3. Para cada pendente, busca o histórico do domínio
  4. Trata o histórico → [{id, situacaoEsocial, vigencia}]
  5. Filtra o item com a vigência mais antiga
  6. (Futuro) Envia POST de revalidação — por ora apenas imprime o resultado
"""
from services.esocial_service import (
    buscar_pendentes,
    tratar_pendentes,
    buscar_historico_dominio,
    tratar_historico,
    revalidar,
)
from services.logger_service import logger


def executar() -> None:
    logger.info("Buscando domínios pendentes no eSocial...")
    bruto    = buscar_pendentes()
    pendentes = tratar_pendentes(bruto)
    logger.info(f"{len(pendentes)} pendentes encontrados.")

    for pendente in pendentes:
        dominio_id  = pendente["id"]
        descricao   = pendente["descricao"]

        logger.info(f"Buscando histórico: {descricao} ({dominio_id})")

        try:
            historico_bruto = buscar_historico_dominio(dominio_id)
            historico       = tratar_historico(historico_bruto)
        except Exception as e:
            logger.error(f"Erro ao buscar histórico de {descricao}: {e}")
            continue

        if not historico:
            logger.warning(f"Histórico vazio para {descricao}, pulando.")
            continue

        mais_antigo = min(
            historico,
            key=lambda h: h["vigencia"] or ""
        )

        sucesso = revalidar(mais_antigo["id"])
        if sucesso:
            logger.info(f"Revalidado com sucesso: {descricao} — {mais_antigo['id']}")
        else:
            logger.warning(f"Falha ao revalidar: {descricao} — {mais_antigo['id']}")

    logger.info("Fluxo de revalidação concluído.")


if __name__ == "__main__":
    executar()