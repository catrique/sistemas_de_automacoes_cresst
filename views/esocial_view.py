import customtkinter as ctk


CARDS_ESOCIAL = [
    {
        "tela":     "esocial_revalidar_pendentes",
        "emoji":    "🔄",
        "titulo":   "Revalidar Pendentes",
        "descricao":"Busca e revalida todos\nos domínios com erro",
    },
]


class EsocialView(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self._app = app
        self.configure(fg_color="transparent")

        # Cabeçalho
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0))

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
            text="📡  eSocial",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=14)

        # Grade de cards
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(expand=True, pady=24)

        for i, card in enumerate(CARDS_ESOCIAL):
            grid.grid_columnconfigure(i, weight=1, minsize=210)
            grid.grid_rowconfigure(0, weight=1)
            self._criar_card(grid, card, row=0, col=i)

    def _criar_card(self, parent, card: dict, row: int, col: int):
        frame = ctk.CTkFrame(
            parent,
            corner_radius=16,
            width=210, height=140,
            cursor="hand2",
        )
        frame.grid(row=row, column=col, padx=14, pady=14, sticky="nsew")
        frame.grid_propagate(False)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text=card["emoji"],
                     font=ctk.CTkFont(size=30)).pack()
        ctk.CTkLabel(inner, text=card["titulo"],
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(4, 2))
        ctk.CTkLabel(inner, text=card["descricao"],
                     font=ctk.CTkFont(size=11),
                     text_color="gray", justify="center").pack()

        tela = card["tela"]
        for widget in [frame, inner] + list(inner.winfo_children()):
            widget.bind("<Button-1>", lambda e, t=tela: self._app.mostrar_tela(t))