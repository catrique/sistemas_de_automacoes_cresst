import customtkinter as ctk

CARDS_HOME = [
    {
        "tela": "esocial",
        "titulo": "eSocial",
        "descricao": "Revalidar pendentes\ne outras operações",
    },
    {
        "tela": "asos",
        "titulo": "ASOs",
        "descricao": "Download e organização\nde ASOs",
    },
    {
        "tela": "relatorios",
        "titulo": "Relatórios",
        "descricao": "Atestados, afastamentos,\nfuncionários e mais",
    },
    {
        "tela": "config",
        "titulo": "Configurações",
        "descricao": "Credenciais, token\ne preferências",
    },
]


class HomeView(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self._app = app
        self.configure(fg_color="transparent")

        ctk.CTkLabel(
            self,
            text="GRS Automação",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(pady=(30, 6))

        ctk.CTkLabel(
            self,
            text="Selecione um módulo para continuar",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack(pady=(0, 36))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(expand=True)

        COLUNAS = 2
        for i, card in enumerate(CARDS_HOME):
            row, col = divmod(i, COLUNAS)
            grid.grid_columnconfigure(col, weight=1, minsize=260)
            grid.grid_rowconfigure(row, weight=1)
            self._criar_card(grid, card, row, col)

    def _criar_card(self, parent, card: dict, row: int, col: int):
        frame = ctk.CTkFrame(
            parent,
            corner_radius=16,
            width=260,
            height=130,
            cursor="hand2",
        )
        frame.grid(row=row, column=col, padx=18, pady=18, sticky="nsew")
        frame.grid_propagate(False)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner,
            text=card["titulo"],
            font=ctk.CTkFont(size=17, weight="bold"),
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            inner,
            text=card["descricao"],
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="center",
        ).pack()

        tela = card["tela"]
        comando = lambda t=tela: self._app.mostrar_tela(t)
        for widget in [frame, inner] + list(inner.winfo_children()):
            widget.bind("<Button-1>", lambda e, c=comando: c())