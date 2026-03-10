import customtkinter as ctk


class HomeView(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller  # Referência para trocar de tela no main.py

        self.configure(fg_color="transparent")

        lbl_welcome = ctk.CTkLabel(
            self,
            text="Bem-vindo ao GRS Automação",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        lbl_welcome.pack(pady=30)

        # Container de Cards/Botões
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(pady=10, padx=20)

        # Botão Atalho: ASOs
        self.btn_asos = self.criar_card(
            grid_frame,
            "📦 Baixar ASOs",
            "Download por período",
            lambda: self.controller.mostrar_tela("asos"),
            0,
            0,
        )

        # Botão Atalho: Token
        self.btn_token = self.criar_card(
            grid_frame,
            "🔑 Atualizar Token",
            "Captura automática Betha",
            lambda: self.controller.mostrar_tela("token"),
            0,
            1,
        )

        # Botão Atalho: Credenciais
        self.btn_cred = self.criar_card(
            grid_frame,
            "⚙️ Configurações",
            "Gerenciar usuários/senhas",
            lambda: self.controller.mostrar_tela("config"),
            1,
            0,
        )
        # No arquivo home_view.py, dentro do __init__ ou onde cria o card:
        self.btn_token = self.criar_card(
            grid_frame,
            "🔑 Atualizar Token",
            "Captura automática Betha",
            lambda: self.controller.disparar_token_direto(),  # Chama a execução direta
            0,
            1,
        )

    def criar_card(self, master, titulo, subtitulo, comando, row, col):
        card = ctk.CTkButton(
            master,
            text=f"{titulo}\n{subtitulo}",
            font=ctk.CTkFont(size=14),
            width=250,
            height=100,
            corner_radius=10,
            command=comando,
        )
        card.grid(row=row, column=col, padx=15, pady=15)
        return card
