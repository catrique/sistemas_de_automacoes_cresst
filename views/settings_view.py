import customtkinter as ctk
from tkinter import messagebox
from config.loaders import salvar_credenciais_criptografadas
from services.logger_service import logger


CARDS_CONFIG = [
    {
        "id":       "token",
        "titulo":   "Atualizar Token",
        "descricao":"Captura automática\ndo token Betha",
    },
    {
        "id":       "credenciais",
        "titulo":   "Configurar Credenciais",
        "descricao":"Usuários e senhas\nde acesso aos portais",
    },
]


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, voltar=None, **kwargs):
        super().__init__(master, **kwargs)
        self._voltar = voltar
        self.configure(fg_color="transparent")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0), padx=4)

        if self._voltar:
            ctk.CTkButton(
                header, text="← Voltar",
                width=90, height=32,
                fg_color="transparent",
                border_width=1,
                text_color=("gray20", "gray80"),
                hover_color=("gray85", "gray25"),
                command=self._voltar,
            ).pack(side="left", padx=4)

        ctk.CTkLabel(
            header,
            text="Configurações",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=14)

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(expand=True, pady=24)

        for i, card in enumerate(CARDS_CONFIG):
            grid.grid_columnconfigure(i, weight=1, minsize=220)
            grid.grid_rowconfigure(0, weight=1)
            self._criar_card(grid, card, row=0, col=i)

    def _criar_card(self, parent, card: dict, row: int, col: int):
        frame = ctk.CTkFrame(
            parent,
            corner_radius=16,
            width=220, height=130,
            cursor="hand2",
        )
        frame.grid(row=row, column=col, padx=14, pady=14, sticky="nsew")
        frame.grid_propagate(False)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text=card["titulo"],
                     font=ctk.CTkFont(size=15, weight="bold"),
                     justify="center").pack(pady=(0, 4))
        ctk.CTkLabel(inner, text=card["descricao"],
                     font=ctk.CTkFont(size=11),
                     text_color="gray", justify="center").pack()

        card_id = card["id"]
        for widget in [frame, inner] + list(inner.winfo_children()):
            widget.bind("<Button-1>", lambda e, cid=card_id: self._abrir(cid))

    def _abrir(self, card_id: str):
        if card_id == "token":
            self._mostrar_token()
        elif card_id == "credenciais":
            self._mostrar_credenciais()

    def _limpar_conteudo(self):
        if hasattr(self, "_sub_frame") and self._sub_frame.winfo_exists():
            self._sub_frame.destroy()

    def _mostrar_token(self):
        self._limpar_conteudo()
        self._sub_frame = _TokenFrame(self, voltar=self._voltar_hub)
        self._sub_frame.pack(fill="both", expand=True)

    def _mostrar_credenciais(self):
        self._limpar_conteudo()
        self._sub_frame = _CredenciaisFrame(self, voltar=self._voltar_hub)
        self._sub_frame.pack(fill="both", expand=True)

    def _voltar_hub(self):
        self._limpar_conteudo()


class _TokenFrame(ctk.CTkFrame):
    def __init__(self, master, voltar, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0), padx=4)

        ctk.CTkButton(
            header, text="← Voltar",
            width=90, height=32,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=voltar,
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            header,
            text="Atualizar Token",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=14)

        card = ctk.CTkFrame(self, corner_radius=15)
        card.pack(pady=20, padx=60, fill="x")

        ctk.CTkLabel(
            card,
            text="Captura automaticamente o token de autenticação\ndo portal Betha e o salva para uso nos módulos.",
            font=ctk.CTkFont(size=13), text_color="gray", justify="center",
        ).pack(pady=(30, 20))

        self.btn = ctk.CTkButton(
            card,
            text="Atualizar Token Agora",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45, width=240,
            command=self._executar,
        )
        self.btn.pack(pady=(0, 30))

    def _executar(self):
        import threading
        from config.loaders import atualizar_token_betha_automatico
        self.btn.configure(state="disabled", text="Atualizando...")

        def worker():
            try:
                atualizar_token_betha_automatico()
                messagebox.showinfo("Sucesso", "Token atualizado com sucesso!")
            except Exception as e:
                logger.error(f"Erro ao atualizar token: {e}")
                messagebox.showerror("Erro", str(e))
            finally:
                self.btn.configure(state="normal", text="Atualizar Token Agora")

        threading.Thread(target=worker, daemon=True).start()


class _CredenciaisFrame(ctk.CTkFrame):
    def __init__(self, master, voltar, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0), padx=4)

        ctk.CTkButton(
            header, text="← Voltar",
            width=90, height=32,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=voltar,
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            header,
            text="Configurar Credenciais",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=14)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(scroll, text="Portal Betha", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        self.betha_login = ctk.CTkEntry(scroll, placeholder_text="Login Betha", width=450)
        self.betha_login.pack(pady=5)
        self.betha_senha = ctk.CTkEntry(scroll, placeholder_text="Senha Betha", width=450, show="*")
        self.betha_senha.pack(pady=5)

        ctk.CTkLabel(scroll, text="Portal SOC", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        self.soc_login = ctk.CTkEntry(scroll, placeholder_text="Usuário SOC", width=450)
        self.soc_login.pack(pady=5)
        self.soc_senha = ctk.CTkEntry(scroll, placeholder_text="Senha SOC", width=450, show="*")
        self.soc_senha.pack(pady=5)
        self.soc_virtual = ctk.CTkEntry(scroll, placeholder_text="Senha Virtual (ex: 3,7,3,2)", width=450)
        self.soc_virtual.pack(pady=5)

        ctk.CTkLabel(scroll, text="Configurações de Proxy", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        self.proxy_user = ctk.CTkEntry(scroll, placeholder_text="Usuário Proxy", width=450)
        self.proxy_user.pack(pady=5)
        self.proxy_pass = ctk.CTkEntry(scroll, placeholder_text="Senha Proxy", width=450, show="*")
        self.proxy_pass.pack(pady=5)

        self.btn_salvar = ctk.CTkButton(
            scroll,
            text="Salvar Credenciais",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838",
            height=45, width=200,
            command=self._acao_salvar,
        )
        self.btn_salvar.pack(pady=30)

    def _acao_salvar(self):
        dados = {
            "betha_login": self.betha_login.get(),
            "betha_senha": self.betha_senha.get(),
            "soc_email":   self.soc_login.get(),
            "soc_senha":   self.soc_senha.get(),
            "soc_virtual": self.soc_virtual.get(),
            "proxy_user":  self.proxy_user.get(),
            "proxy_senha": self.proxy_pass.get(),
        }
        try:
            salvar_credenciais_criptografadas(dados)
            messagebox.showinfo("Sucesso", "Credenciais salvas e criptografadas localmente!")
            logger.info("Configurações de acesso atualizadas pelo usuário.")
        except Exception as e:
            logger.error(f"Falha ao salvar credenciais: {e}")
            messagebox.showerror("Erro", f"Não foi possível salvar: {e}")