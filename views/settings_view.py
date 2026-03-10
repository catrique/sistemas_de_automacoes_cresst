import customtkinter as ctk
from tkinter import messagebox
from config.loaders import salvar_credenciais_criptografadas
from services.logger_service import logger

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="transparent")
        
        # Container centralizado para os inputs
        self.main_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # --- PORTAL BETHA ---
        ctk.CTkLabel(self.main_container, text="Portal Betha", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        self.betha_login = ctk.CTkEntry(self.main_container, placeholder_text="Login Betha", width=450)
        self.betha_login.pack(pady=5)
        self.betha_senha = ctk.CTkEntry(self.main_container, placeholder_text="Senha Betha", width=450, show="*")
        self.betha_senha.pack(pady=5)

        # --- PORTAL SOC ---
        ctk.CTkLabel(self.main_container, text="Portal SOC", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        self.soc_login = ctk.CTkEntry(self.main_container, placeholder_text="Usuário SOC", width=450)
        self.soc_login.pack(pady=5)
        self.soc_senha = ctk.CTkEntry(self.main_container, placeholder_text="Senha SOC", width=450, show="*")
        self.soc_senha.pack(pady=5)
        self.soc_virtual = ctk.CTkEntry(self.main_container, placeholder_text="Senha Virtual (ex: 3,7,3,2)", width=450)
        self.soc_virtual.pack(pady=5)

        # --- PROXY ---
        ctk.CTkLabel(self.main_container, text="Configurações de Proxy", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        self.proxy_user = ctk.CTkEntry(self.main_container, placeholder_text="Usuário Proxy", width=450)
        self.proxy_user.pack(pady=5)
        self.proxy_pass = ctk.CTkEntry(self.main_container, placeholder_text="Senha Proxy", width=450, show="*")
        self.proxy_pass.pack(pady=5)

        # --- BOTÃO SALVAR (O que estava faltando) ---
        self.btn_salvar = ctk.CTkButton(
            self.main_container, 
            text="💾 Salvar Credenciais", 
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#28a745", # Verde para indicar ação positiva
            hover_color="#218838",
            height=45,
            width=200,
            command=self.acao_salvar
        )
        self.btn_salvar.pack(pady=30)

    def acao_salvar(self):
        """Coleta os dados e salva de forma criptografada"""
        dados = {
            "betha_login": self.betha_login.get(),
            "betha_senha": self.betha_senha.get(),
            "soc_email": self.soc_login.get(),
            "soc_senha": self.soc_senha.get(),
            "soc_virtual": self.soc_virtual.get(),
            "proxy_user": self.proxy_user.get(),
            "proxy_senha": self.proxy_pass.get()
        }
        
        try:
            # Chama a função que movemos para o loaders.py
            salvar_credenciais_criptografadas(dados)
            messagebox.showinfo("Sucesso", "Credenciais salvas e criptografadas localmente!")
            logger.info("✅ Configurações de acesso atualizadas pelo usuário.")
        except Exception as e:
            logger.error(f"Falha ao salvar credenciais: {e}")
            messagebox.showerror("Erro", f"Não foi possível salvar: {e}")