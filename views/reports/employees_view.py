import customtkinter as ctk
import threading
from tkinter import messagebox

from views.reports.base_report_view import BaseRelatorioView
from modules.soc.exportar_relatorio_funcionarios import executar
from services.logger_service import logger


class FuncionariosSocView(BaseRelatorioView):
    TITULO = "Funcionários SOC"
    EMOJI  = "📋"

    def _construir(self):
        ctk.CTkLabel(
            self.card,
            text="Acessa o SOC e exporta a lista completa de funcionários\n"
                 "para um arquivo Excel em workspace/relatorios/saida.",
            font=ctk.CTkFont(size=13), text_color="gray",
            justify="center",
        ).pack(pady=(30, 20))

        self._btn = ctk.CTkButton(
            self.card, text="Exportar Lista de Funcionários",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45, width=280,
            command=self._iniciar,
        )
        self._btn.pack(pady=(0, 30))

    def _iniciar(self):
        self._btn.configure(state="disabled", text="Processando...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            logger.info("Exportando lista de funcionários SOC...")
            executar()
            messagebox.showinfo("Sucesso", "Lista exportada com sucesso!")
        except Exception as e:
            logger.error(f"Erro: {e}")
            messagebox.showerror("Erro", str(e))
        finally:
            self._btn.configure(state="normal", text="Exportar Lista de Funcionários")