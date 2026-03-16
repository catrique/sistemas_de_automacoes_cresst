import customtkinter as ctk


CARDS_HOME = [
    {
        "tela":     "asos",
        "emoji":    "⚙️",
        "titulo":   "Baixar ASOs",
        "descricao":"Download por período",
    },
    {
        "tela":     "relatorios",
        "emoji":    "📊",
        "titulo":   "Relatórios",
        "descricao":"Atestados, afastamentos,\nfuncionários e mais",
    },
    {
        "tela":     "token",
        "emoji":    "🔑",
        "titulo":   "Atualizar Token",
        "descricao":"Captura automática Betha",
    },
    {
        "tela":     "config",
        "emoji":    "⚙️",
        "titulo":   "Configurações",
        "descricao":"Gerenciar usuários/senhas",
    },
]


class HomeView(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self._app = app
        self.configure(fg_color="transparent")

        ctk.CTkLabel(
            self,
            text="Bem-vindo ao GRS Automação",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(pady=(30, 40))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(expand=True)

        COLUNAS = 2
        for i, card in enumerate(CARDS_HOME):
            row, col = divmod(i, COLUNAS)
            grid.grid_columnconfigure(col, weight=1, minsize=240)
            grid.grid_rowconfigure(row, weight=1)
            self._criar_card(grid, card, row, col)

    def _criar_card(self, parent, card: dict, row: int, col: int):
        frame = ctk.CTkFrame(
            parent,
            corner_radius=16,
            width=240, height=140,
            cursor="hand2",
        )
        frame.grid(row=row, column=col, padx=18, pady=18, sticky="nsew")
        frame.grid_propagate(False)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner,
            text=card["emoji"],
            font=ctk.CTkFont(size=30),
        ).pack()

        ctk.CTkLabel(
            inner,
            text=card["titulo"],
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(4, 2))

        ctk.CTkLabel(
            inner,
            text=card["descricao"],
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="center",
        ).pack()

        tela = card["tela"]
        comando = self._acao(tela)
        for widget in [frame, inner] + list(inner.winfo_children()):
            widget.bind("<Button-1>", lambda e, c=comando: c())

    def _acao(self, tela: str):
        if tela == "token":
            return self._app.disparar_token_direto
        return lambda: self._app.mostrar_tela(tela)