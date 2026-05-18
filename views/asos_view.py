import os
import customtkinter as ctk
from tkinter import messagebox
import threading
from modules.soc.baixar_asos import baixar_asos_por_intervalo_data
from modules.betha.lancar_aso_via_api import executar as executar_lancamento_aso_via_api
from services.logger_service import logger
from services.utils import organizar_asos

CARDS_ASOS = [
    {
        "id": "baixar",
        "titulo": "Baixar ASOs por Período",
        "descricao": "Download automático\npor intervalo de datas",
    },
    {
        "id": "organizar",
        "titulo": "Organizar ASOs Baixados",
        "descricao": "Classifica e organiza\nos arquivos na pasta",
    },
    {
        "id": "lancar",
        "titulo": "Lançar ASOs",
        "descricao": "Registra e lança\nos ASOs processados",
    },
]


class AsosView(ctk.CTkFrame):
    def __init__(self, master, voltar=None, **kwargs):
        super().__init__(master, **kwargs)
        self.voltar = voltar
        self.configure(fg_color="transparent")
        self.hub_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.hub_frame.pack(fill="both", expand=True)
        header = ctk.CTkFrame(self.hub_frame, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0), padx=4)

        if self.voltar:
            ctk.CTkButton(
                header,
                text="← Voltar",
                width=90,
                height=32,
                fg_color="transparent",
                border_width=1,
                text_color=("gray20", "gray80"),
                hover_color=("gray85", "gray25"),
                command=self.voltar,
            ).pack(side="left", padx=4)

        ctk.CTkLabel(
            header,
            text="ASOs",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=14)

        grid = ctk.CTkFrame(self.hub_frame, fg_color="transparent")
        grid.pack(expand=True, pady=24)

        for i, card in enumerate(CARDS_ASOS):
            grid.grid_columnconfigure(i, weight=1, minsize=220)
            self._criar_card(grid, card, row=0, col=i)

    def _criar_card(self, parent, card: dict, row: int, col: int):
        frame = ctk.CTkFrame(
            parent, corner_radius=16, width=220, height=130, cursor="hand2"
        )
        frame.grid(row=row, column=col, padx=14, pady=14, sticky="nsew")
        frame.grid_propagate(False)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text=card["titulo"], font=ctk.CTkFont(size=15, weight="bold")
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            inner, text=card["descricao"], font=ctk.CTkFont(size=11), text_color="gray"
        ).pack()

        card_id = card["id"]
        for widget in [frame, inner] + list(inner.winfo_children()):
            widget.bind("<Button-1>", lambda e, cid=card_id: self._abrir(cid))

    def _abrir(self, card_id: str):
        self.hub_frame.pack_forget()

        if card_id == "baixar":
            self._mostrar_baixar()
        elif card_id == "organizar":
            self._mostrar_organizar()
        elif card_id == "lancar":
            self._mostrar_lancar()
        elif card_id == "atualizar_retorno":
            self._mostrar_atualizar_retorno()

    def _limpar_conteudo(self):
        if hasattr(self, "_sub_frame") and self._sub_frame.winfo_exists():
            self._sub_frame.destroy()

    def _mostrar_baixar(self):
        self._limpar_conteudo()
        self._sub_frame = _BaixarAsosFrame(self, voltar=self._voltar_hub)
        self._sub_frame.pack(fill="both", expand=True)

    def _mostrar_organizar(self):
        self._limpar_conteudo()
        self._sub_frame = _OrganizarAsosFrame(self, voltar=self._voltar_hub)
        self._sub_frame.pack(fill="both", expand=True)

    def _mostrar_lancar(self):
        self._limpar_conteudo()
        self._sub_frame = _LancarAsosFrame(self, voltar=self._voltar_hub)
        self._sub_frame.pack(fill="both", expand=True)

    def _voltar_hub(self):
        self._limpar_conteudo()
        self.hub_frame.pack(fill="both", expand=True)


class _BaixarAsosFrame(ctk.CTkFrame):
    def __init__(self, master, voltar, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._voltar = voltar

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0), padx=4)

        ctk.CTkButton(
            header,
            text="← Voltar",
            width=90,
            height=32,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=voltar,
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            header,
            text="Baixar ASOs por Período",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=14)

        card = ctk.CTkFrame(self, corner_radius=15)
        card.pack(pady=20, padx=60, fill="x")

        ctk.CTkLabel(card, text="Data Inicial:", font=ctk.CTkFont(size=14)).pack(
            pady=(20, 5)
        )
        self.entry_inicio = ctk.CTkEntry(card, placeholder_text="10/03/2026", width=250)
        self.entry_inicio.pack(pady=5)

        ctk.CTkLabel(card, text="Data Final:", font=ctk.CTkFont(size=14)).pack(
            pady=(15, 5)
        )
        self.entry_fim = ctk.CTkEntry(card, placeholder_text="10/03/2026", width=250)
        self.entry_fim.pack(pady=5)

        ctk.CTkLabel(
            card,
            text="O robô irá acessar o SOCGED, filtrar por ASO\ne descarregar todos os arquivos do período.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(pady=(15, 20))

        self.btn_confirmar = ctk.CTkButton(
            self,
            text="Iniciar Download",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=48,
            width=260,
            command=self._executar_download,
        )
        self.btn_confirmar.pack(pady=20)

    def _executar_download(self):
        data_i = self.entry_inicio.get().strip()
        data_f = self.entry_fim.get().strip()
        if not data_i or not data_f:
            messagebox.showwarning("Atenção", "Por favor, preencha ambas as datas.")
            return
        self.btn_confirmar.configure(state="disabled", text="Processando...")
        threading.Thread(
            target=self._worker, args=(data_i, data_f), daemon=True
        ).start()

    def _worker(self, data_i, data_f):
        try:
            logger.info(f"Iniciando busca de ASOs entre {data_i} e {data_f}...")
            baixar_asos_por_intervalo_data(data_i, data_f)
            messagebox.showinfo("Sucesso", "Download concluído!")
        except Exception as e:
            logger.error(f"Erro no download: {e}")
            messagebox.showerror("Erro", f"Ocorreu uma falha: {e}")
        finally:
            self.btn_confirmar.configure(state="normal", text="Iniciar Download")


class _OrganizarAsosFrame(ctk.CTkFrame):
    def __init__(self, master, voltar, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._voltar = voltar

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0), padx=4)

        ctk.CTkButton(
            header,
            text="← Voltar",
            width=90,
            height=32,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=voltar,
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            header,
            text="Organizar ASOs Baixados",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=14)

        card = ctk.CTkFrame(self, corner_radius=15)
        card.pack(pady=20, padx=60, fill="x")

        ctk.CTkLabel(
            card,
            text="Organiza automaticamente os ASOs já baixados,\nclassificando-os por funcionário e data.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            justify="center",
        ).pack(pady=(30, 20))
        ctk.CTkLabel(card, text="Caminho da Pasta:", font=ctk.CTkFont(size=14)).pack(
            pady=(20, 5)
        )

        self.dir_path = ctk.CTkEntry(
            card, placeholder_text="Selecione a pasta", width=250
        )

        self.dir_path.pack(pady=5)

        self.btn = ctk.CTkButton(
            card,
            text="Organizar Agora",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            width=240,
            command=self._executar,
        )
        self.btn.pack(pady=(0, 30))

    def _executar(self):
        dir_path = self.dir_path.get().strip().replace('"', "")
        if not dir_path:
            messagebox.showwarning("Atenção", "Por favor, insira o caminho da pasta.")
            return
        self.btn.configure(state="disabled", text="Processando...")
        threading.Thread(target=self._worker, args=(dir_path,), daemon=True).start()

    def _worker(self, dir_path):
        try:
            organizar_asos.executar(diretorio_especifico=dir_path)
            messagebox.showinfo("Sucesso", "Organização concluída!")
        except Exception as e:
            logger.error(f"Erro na organização: {e}")
            messagebox.showerror("Erro", f"Ocorreu uma falha: {e}")
        finally:
            self.dir_path.delete(0, "end")
            self.btn.configure(state="normal", text="Organizar Agora")


class _LancarAsosFrame(ctk.CTkFrame):
    def __init__(self, master, voltar, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._voltar = voltar

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0), padx=4)

        ctk.CTkButton(
            header,
            text="← Voltar",
            width=90,
            height=32,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=voltar,
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            header,
            text="Lançar ASOs via API",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=14)

        card = ctk.CTkFrame(self, corner_radius=15)
        card.pack(pady=20, padx=60, fill="x")

        ctk.CTkLabel(
            card, text="Tipo de Exame para Lançar:", font=ctk.CTkFont(size=14)
        ).pack(pady=(20, 5))
        self.combo_tipo = ctk.CTkOptionMenu(
            card,
            values=[
                "TODOS",
                "ADMISSIONAL",
                "DEMISSIONAL",
                "PERIODICO",
                "RETORNO AO TRABALHO",
                "MUDANÇA DE FUNÇÃO",
            ],
            width=250,
        )
        self.combo_tipo.set("TODOS")
        self.combo_tipo.pack(pady=5)

        ctk.CTkLabel(card, text="Caminho do Excel:", font=ctk.CTkFont(size=14)).pack(
            pady=(15, 5)
        )
        self.excel_path = ctk.CTkEntry(
            card, placeholder_text="Caminho do arquivo .xlsx", width=250
        )
        self.excel_path.pack(pady=(5, 20))

        self.btn_confirmar = ctk.CTkButton(
            self,
            text="Iniciar Lançamento",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=48,
            width=260,
            command=self._executar_lancamento,
        )
        self.btn_confirmar.pack(pady=20)

    def _executar_lancamento(self):
        caminho_excel = self.excel_path.get().strip().replace('"', "")
        tipo_selecionado = self.combo_tipo.get()

        if not caminho_excel:
            messagebox.showwarning(
                "Atenção", "Por favor, informe o caminho do arquivo Excel."
            )
            return

        if not os.path.exists(caminho_excel):
            messagebox.showerror(
                "Erro", "O arquivo Excel especificado não foi encontrado."
            )
            return

        self.btn_confirmar.configure(state="disabled", text="Processando...")
        threading.Thread(
            target=self._worker,
            args=(caminho_excel, tipo_selecionado),
            daemon=True,
        ).start()

    def _worker(self, caminho_excel, tipo_selecionado):
        try:
            executar_lancamento_aso_via_api(
                caminho_excel, tipo_selecionado=tipo_selecionado
            )
            messagebox.showinfo(
                "Sucesso",
                "O lote de ASOs foi processado!\nVerifique o log para detalhes.",
            )
        except Exception as e:
            logger.error(f"Falha na execução do lançamento: {e}")
            messagebox.showerror("Erro Crítico", f"Erro ao processar: {e}")
        finally:
            self.btn_confirmar.configure(state="normal", text="Iniciar Lançamento")