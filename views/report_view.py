import customtkinter as ctk
from tkinter import messagebox
import threading

from modules.soc.exportar_relatorio_funcionarios import executar as exportar_funcionarios
from services.logger_service import logger


class RelatoriosView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        # Título
        ctk.CTkLabel(self, text="Relatórios",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 10))

        # ── Card: Lista de Funcionários ───────────────────────────────────────
        card_func = ctk.CTkFrame(self, corner_radius=15)
        card_func.pack(pady=10, padx=40, fill="x")

        ctk.CTkLabel(card_func, text="Lista de Funcionários",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 5))

        ctk.CTkLabel(card_func,
                     text="Acessa o SOC e exporta a lista completa de funcionários\n"
                          "para um arquivo Excel em workspace/relatorios/saida.",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(5, 20))

        self.btn_funcionarios = ctk.CTkButton(
            card_func,
            text="📋 Exportar Lista de Funcionários",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            width=300,
            command=self._iniciar_exportar_funcionarios,
        )
        self.btn_funcionarios.pack(pady=(0, 20))

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _iniciar_exportar_funcionarios(self):
        self.btn_funcionarios.configure(state="disabled", text="Processando...")
        threading.Thread(target=self._worker_funcionarios, daemon=True).start()

    def _worker_funcionarios(self):
        try:
            logger.info("Iniciando exportação da lista de funcionários...")
            exportar_funcionarios()
            messagebox.showinfo("Sucesso", "Lista de funcionários exportada com sucesso!")
        except Exception as e:
            logger.error(f"Erro na exportação: {e}")
            messagebox.showerror("Erro", f"Ocorreu uma falha: {e}")
        finally:
            self.btn_funcionarios.configure(state="normal",
                                            text="📋 Exportar Lista de Funcionários")