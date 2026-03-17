import threading
import customtkinter as ctk
from tkinter import messagebox

from modules.betha.esocial.revalidar_pendentes import executar


class RevalidarPendentesView(ctk.CTkFrame):
    def __init__(self, master, voltar, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")

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
            text="🔄  Revalidar Pendentes",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=14)

        card = ctk.CTkFrame(self, corner_radius=15)
        card.pack(fill="x", padx=40, pady=30)

        ctk.CTkLabel(
            card,
            text="Busca todos os domínios PENDENTES, obtém o histórico de cada um\n"
                 "e revalida o item com vigência mais antiga.\n"
                 "Acompanhe o progresso no terminal abaixo.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            justify="center",
        ).pack(pady=(24, 20))

        self._btn = ctk.CTkButton(
            card,
            text="▶  Executar",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42, width=200,
            command=self._iniciar,
        )
        self._btn.pack(pady=(0, 28))

    def _iniciar(self):
        self._btn.configure(state="disabled", text="⏳ Processando...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            executar()
            self.after(0, lambda: messagebox.showinfo(
                "Concluído", "Fluxo de revalidação concluído."))
        except Exception as e:
            erro = str(e)
            self.after(0, lambda: messagebox.showerror("Erro", erro))
        finally:
            self.after(0, lambda: self._btn.configure(
                state="normal", text="▶  Executar"))