import customtkinter as ctk
from config.loaders import atualizar_token_betha_automatico # Importe a função aqui
import threading

from views.home_view import HomeView
from views.report_view import RelatoriosView
from views.settings_view import SettingsView
from views.terminal_view import TerminalView
from views.asos_view import AsosView 
from services.logger_service import logger
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GRS Automação - Divinópolis")
        self.geometry("1100x750")

        # Layout Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1) # Área de conteúdo
        self.grid_rowconfigure(1, weight=0) # Área do terminal

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="MENU", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        
        ctk.CTkButton(self.sidebar, text="Início", command=lambda: self.mostrar_tela("home")).pack(pady=5, padx=10)
        ctk.CTkButton(self.sidebar, text="Baixar ASOs", command=lambda: self.mostrar_tela("asos")).pack(pady=5, padx=10)
        ctk.CTkButton(self.sidebar, text="Relatórios", command=lambda: self.mostrar_tela("relatorios")).pack(pady=5, padx=10)
        ctk.CTkButton(self.sidebar, text="Credenciais", command=lambda: self.mostrar_tela("config")).pack(pady=5, padx=10)

        # --- ÁREA DE CONTEÚDO ---
        self.container = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # --- TERMINAL (Fixo na parte inferior) ---
        self.terminal = TerminalView(self, height=200)
        self.terminal.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="nsew")

        # Dicionário de telas
        self.telas = {}
        self.mostrar_tela("home")

    def mostrar_tela(self, nome):
        for widget in self.container.winfo_children():
            widget.destroy()

        view = None 
        if nome == "home":
            view = HomeView(self.container, self)
        elif nome == "config":
            view = SettingsView(self.container)
        elif nome == "asos":
            view = AsosView(self.container)
        elif nome == "relatorios":
            view = RelatoriosView(self.container)
        
        if view:
            view.pack(fill="both", expand=True)

    def disparar_token_direto(self):
        """Executa a atualização do token sem trocar de tela"""
        logger.info("Iniciando atualização do token em segundo plano...")
        thread = threading.Thread(target=self._executar_token_silencioso, daemon=True)
        thread.start()

    def _executar_token_silencioso(self):
        try:
            atualizar_token_betha_automatico()
            # O logger.info dentro da função já vai mostrar o sucesso no terminal
        except Exception as e:
            logger.error(f"Falha na atualização direta: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()