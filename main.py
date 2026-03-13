import customtkinter as ctk
import threading

from config.loaders import atualizar_token_betha_automatico
from views.home_view import HomeView
from views.settings_view import SettingsView
from views.terminal_view import TerminalView
from views.asos_view import AsosView
from views.reports.reports_view import RelatoriosView
from services.logger_service import logger


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GRS Automação - Divinópolis")
        self.geometry("1100x750")

        # Sem sidebar — layout de coluna única
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # Área de conteúdo ocupa toda a largura
        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.container.grid(row=0, column=0, padx=30, pady=20, sticky="nsew")

        # Terminal fixo na parte inferior
        self.terminal = TerminalView(self, height=180)
        self.terminal.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="nsew")

        self.mostrar_tela("home")

    # ── Roteamento ────────────────────────────────────────────────────────────

    def mostrar_tela(self, nome: str):
        for widget in self.container.winfo_children():
            widget.destroy()

        view = None

        if nome == "home":
            view = HomeView(self.container, self)

        elif nome == "asos":
            view = AsosView(self.container,
                            voltar=lambda: self.mostrar_tela("home"))

        elif nome == "relatorios":
            view = RelatoriosView(self.container, app=self)

        elif nome == "config":
            view = SettingsView(self.container,
                                voltar=lambda: self.mostrar_tela("home"))

        # ── Telas individuais de relatório ────────────────────────────────────
        elif nome == "rel_atestados":
            from views.reports.medical_certificate_view import AtestadosView
            view = AtestadosView(self.container,
                                 voltar=lambda: self.mostrar_tela("relatorios"))

        elif nome == "rel_afastamentos":
            from views.reports.remoteness_view import AfastamentosView
            view = AfastamentosView(self.container,
                                    voltar=lambda: self.mostrar_tela("relatorios"))

        elif nome == "rel_por_secretaria":
            from views.reports.secretary_view import PorSecretariaView
            view = PorSecretariaView(self.container,
                                     voltar=lambda: self.mostrar_tela("relatorios"))

        elif nome == "rel_funcionarios_soc":
            from views.reports.employees_view import FuncionariosSocView
            view = FuncionariosSocView(self.container,
                                       voltar=lambda: self.mostrar_tela("relatorios"))

        elif nome == "rel_atualizar_secretarias":
            from views.reports.update_secretary_view import AtualizarSecretariasView
            view = AtualizarSecretariasView(self.container,
                                            voltar=lambda: self.mostrar_tela("relatorios"))

        if view:
            view.pack(fill="both", expand=True)

    # ── Token Betha em background ─────────────────────────────────────────────

    def disparar_token_direto(self):
        logger.info("Iniciando atualização do token em segundo plano...")
        threading.Thread(target=self._executar_token_silencioso, daemon=True).start()

    def _executar_token_silencioso(self):
        try:
            atualizar_token_betha_automatico()
        except Exception as e:
            logger.error(f"Falha na atualização direta: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()