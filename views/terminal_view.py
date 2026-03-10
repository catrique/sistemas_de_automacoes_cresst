import customtkinter as ctk
from services.logger_service import configurar_log_gui

class TerminalView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Cabeçalho do Terminal
        self.header = ctk.CTkLabel(self, text="CONSOLE DE EXECUÇÃO", font=ctk.CTkFont(size=12, weight="bold"))
        self.header.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Campo de Texto (Onde os logs aparecem)
        self.text_area = ctk.CTkTextbox(self, font=("Consolas", 12), state="disabled", fg_color="#1e1e1e", text_color="#d4d4d4")
        self.text_area.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Conecta o logger à função de escrita deste componente
        configurar_log_gui(self.escrever_log)

    def escrever_log(self, mensagem):
        self.text_area.configure(state="normal")
        self.text_area.insert("end", f"{mensagem}\n")
        self.text_area.see("end")
        self.text_area.configure(state="disabled")