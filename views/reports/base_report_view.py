import customtkinter as ctk
import threading
from tkinter import messagebox
from services.logger_service import logger


class BaseRelatorioView(ctk.CTkFrame):
    """
    Classe base para todas as views de relatório.
    Fornece cabeçalho com botão voltar, título, área de conteúdo e padrão de worker.
    """

    TITULO = ""
    EMOJI  = ""

    def __init__(self, master, voltar, **kwargs):
        super().__init__(master, **kwargs)
        self._voltar = voltar
        self.configure(fg_color="transparent")

        # ── Cabeçalho ─────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0), padx=20)

        ctk.CTkButton(
            header, text="← Voltar",
            width=90, height=32,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=voltar,
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"{self.EMOJI}  {self.TITULO}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=14)

        # ── Card central ──────────────────────────────────────────────────────
        self.card = ctk.CTkFrame(self, corner_radius=15)
        self.card.pack(fill="x", padx=60, pady=30)

        self._construir()

    def _construir(self):
        """Subclasses implementam aqui os widgets do card."""
        raise NotImplementedError

    # ── Helpers para subclasses ───────────────────────────────────────────────

    def _rodar_em_thread(self, btn, texto_processando: str, fn, *args):
        btn.configure(state="disabled", text=texto_processando)
        texto_original = btn.cget("text") if not texto_processando else btn._text_label.cget("text")
        threading.Thread(
            target=self._worker, args=(btn, texto_original, fn, args), daemon=True
        ).start()

    def _worker(self, btn, texto_original, fn, args):
        try:
            fn(*args)
            messagebox.showinfo("Sucesso", "Relatório gerado com sucesso!")
        except Exception as e:
            logger.error(f"Erro: {e}")
            messagebox.showerror("Erro", str(e))
        finally:
            btn.configure(state="normal", text=texto_original)