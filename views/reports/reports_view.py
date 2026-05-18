import customtkinter as ctk


CARDS_RELATORIOS = [
    {
        "tela":     "rel_atestados",
        "titulo":   "Atestados",
        "descricao":"Relatório por nome\ndo funcionário",
    },
    {
        "tela":     "rel_afastamentos",
        "titulo":   "Afastamentos",
        "descricao":"Relatório por nome\ndo funcionário",
    },
    {
        "tela":     "rel_por_secretaria",
        "titulo":   "Por Secretaria",
        "descricao":"Funcionários ativos\npor lotação",
    },
    {
        "tela":     "rel_funcionarios_soc",
        "titulo":   "Funcionários SOC",
        "descricao":"Lista completa\nexportada do SOC",
    },
    {
        "tela":     "rel_atualizar_secretarias",
        "titulo":   "Atualizar Secretarias",
        "descricao":"Atualiza mapa de\nlotações Betha",
    },
    {
        "tela":     "rel_retorno_ao_trabalho",
        "titulo":   "Retorno ao Trabalho",
        "descricao":"Agendamentos do dia\nexportados do SOC",
    },
]


class RelatoriosView(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self._app = app
        self.configure(fg_color="transparent")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0), padx=4)

        ctk.CTkButton(
            header, text="← Voltar",
            width=90, height=32,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=lambda: app.mostrar_tela("home"),
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            header,
            text="Relatórios",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=14)

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(expand=True, pady=24)

        COLUNAS = 3
        for i, card in enumerate(CARDS_RELATORIOS):
            row, col = divmod(i, COLUNAS)
            grid.grid_columnconfigure(col, weight=1, minsize=210)
            grid.grid_rowconfigure(row, weight=1)
            self._criar_card(grid, card, row, col)

    def _criar_card(self, parent, card: dict, row: int, col: int):
        frame = ctk.CTkFrame(
            parent,
            corner_radius=16,
            width=210, height=130,
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

        tela = card["tela"]
        for widget in [frame, inner] + list(inner.winfo_children()):
            widget.bind("<Button-1>", lambda e, t=tela: self._app.mostrar_tela(t))