"""
views/reports/retorno_ao_trabalho_view.py

View do relatório de Retorno ao Trabalho.
Segue o padrão de BaseRelatorioView + entrada de data única (igual à _BaixarAsosFrame).
"""
import threading
from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from modules.soc.relatorio_retorno_ao_trabalho import gerar_relatorio_retorno_ao_trabalho
from services.logger_service import logger


class RetornoAoTrabalhoView(ctk.CTkFrame):
    """
    View do relatório de Retorno ao Trabalho.
    Recebe `voltar` (callable) do RelatoriosView.
    """

    TITULO = "Retorno ao Trabalho"

    def __init__(self, master, voltar, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._voltar = voltar

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0), padx=4)

        ctk.CTkButton(
            header,
            text="← Voltar",
            width=90,
            height=32,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=voltar,
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            header,
            text=self.TITULO,
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=14)

        card = ctk.CTkFrame(self, corner_radius=15)
        card.pack(fill="x", padx=60, pady=30)

        ctk.CTkLabel(
            card,
            text="Data da pesquisa:",
            font=ctk.CTkFont(size=14),
        ).pack(pady=(20, 5))

        hoje = date.today().strftime("%d/%m/%Y")
        self.entry_data = ctk.CTkEntry(
            card,
            placeholder_text=hoje,
            width=250,
        )
        self.entry_data.insert(0, hoje)
        self.entry_data.pack(pady=5)

        ctk.CTkLabel(
            card,
            text="O robô irá acessar o SOC, filtrar os agendamentos\n"
                 "de Retorno ao Trabalho e exportar a lista em Excel.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="center",
        ).pack(pady=(15, 20))

        self.btn_gerar = ctk.CTkButton(
            self,
            text="Gerar Relatório",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=48,
            width=260,
            command=self._executar,
        )
        self.btn_gerar.pack(pady=10)


    def _executar(self):
        data = self.entry_data.get().strip()
        if not data:
            messagebox.showwarning("Atenção", "Por favor, informe a data de pesquisa.")
            return

        self.btn_gerar.configure(state="disabled", text="Processando...")
        threading.Thread(target=self._worker, args=(data,), daemon=True).start()

    def _worker(self, data: str):
        try:
            logger.info(f"Gerando relatório de Retorno ao Trabalho para {data}...")
            gerar_relatorio_retorno_ao_trabalho(data_pesquisa=data)
            messagebox.showinfo("Sucesso", "Relatório gerado com sucesso!")
        except Exception as e:
            logger.error(f"Erro no relatório de Retorno ao Trabalho: {e}")
            messagebox.showerror("Erro", f"Ocorreu uma falha:\n{e}")
        finally:
            self.btn_gerar.configure(state="normal", text="Gerar Relatório")