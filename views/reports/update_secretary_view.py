import customtkinter as ctk
import threading
from tkinter import messagebox

from views.reports.base_report_view import BaseRelatorioView
from modules.betha.secretarias import executar
from services.logger_service import logger


class AtualizarSecretariasView(BaseRelatorioView):
    TITULO = "Atualizar Secretarias"
    EMOJI  = "🔄"

    def _construir(self):
        ctk.CTkLabel(
            self.card,
            text="Busca a estrutura de lotações na API Betha e salva\n"
                 "o arquivo secretarias.json atualizado em config/.",
            font=ctk.CTkFont(size=13), text_color="gray",
            justify="center",
        ).pack(pady=(30, 20))

        self._label_resultado = ctk.CTkLabel(
            self.card, text="", font=ctk.CTkFont(size=12))
        self._label_resultado.pack(pady=(0, 10))

        self._btn = ctk.CTkButton(
            self.card, text="Atualizar Agora",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45, width=220,
            command=self._iniciar,
        )
        self._btn.pack(pady=(0, 30))

    def _iniciar(self):
        self._btn.configure(state="disabled", text="Atualizando...")
        self._label_resultado.configure(text="")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            logger.info("Atualizando mapa de secretarias...")
            dicionario = executar()
            total = len(dicionario)
            self.after(0, lambda: self._label_resultado.configure(
                text=f"✅ {total} secretarias atualizadas.", text_color="green"))
            messagebox.showinfo("Sucesso", f"{total} secretarias salvas em config/secretarias.json")
        except Exception as e:
            erro = str(e)
            logger.error(f"Erro: {erro}")
            self.after(0, lambda: self._label_resultado.configure(
                text=f"❌ {erro}", text_color="red"))
            messagebox.showerror("Erro", erro)
        finally:
            self._btn.configure(state="normal", text="Atualizar Agora")