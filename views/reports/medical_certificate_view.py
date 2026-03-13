import customtkinter as ctk
import threading
from tkinter import messagebox

from views.reports.base_report_view import BaseRelatorioView
from modules.betha.atestados import gerar_relatorio
from services.logger_service import logger


class AtestadosView(BaseRelatorioView):
    TITULO = "Relatório de Atestados"
    EMOJI  = "🏥"

    def _construir(self):
        ctk.CTkLabel(
            self.card,
            text="Informe um ou mais nomes separados por vírgula.",
            font=ctk.CTkFont(size=13), text_color="gray",
        ).pack(pady=(24, 8))

        self._entry = ctk.CTkEntry(
            self.card, placeholder_text="NOME COMPLETO, OUTRO NOME", width=420)
        self._entry.pack(pady=(0, 20))

        self._btn = ctk.CTkButton(
            self.card, text="Gerar Relatório",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45, width=220,
            command=self._iniciar,
        )
        self._btn.pack(pady=(0, 28))

    def _iniciar(self):
        nomes = self._entry.get().strip()
        if not nomes:
            messagebox.showwarning("Atenção", "Informe ao menos um nome.")
            return
        self._btn.configure(state="disabled", text="Processando...")
        threading.Thread(target=self._worker, args=(nomes,), daemon=True).start()

    def _worker(self, nomes: str):
        try:
            for nome in [n.strip().upper() for n in nomes.split(",") if n.strip()]:
                logger.info(f"Gerando atestados: {nome}")
                gerar_relatorio(nome)
            messagebox.showinfo("Sucesso", "Relatório(s) gerado(s) com sucesso!")
        except Exception as e:
            logger.error(f"Erro atestados: {e}")
            messagebox.showerror("Erro", str(e))
        finally:
            self._btn.configure(state="normal", text="Gerar Relatório")