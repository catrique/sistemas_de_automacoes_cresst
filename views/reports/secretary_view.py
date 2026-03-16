import tkinter as tk
import customtkinter as ctk
import threading
from tkinter import messagebox

from views.reports.base_report_view import BaseRelatorioView
from modules.betha.funcionarios_por_secretaria import executar
from services.utils.secretarias_service import (
    carregar_secretarias, buscar_por_texto, json_disponivel,
)
from services.logger_service import logger


class PorSecretariaView(BaseRelatorioView):
    TITULO = "Funcionários por Secretaria"
    EMOJI  = "🏛️"

    def _construir(self):
        ctk.CTkLabel(
            self.card,
            text="Pesquise e selecione a secretaria ou lotação desejada.",
            font=ctk.CTkFont(size=13), text_color="gray",
        ).pack(pady=(24, 10))

        frame_cod = ctk.CTkFrame(self.card, fg_color="transparent")
        frame_cod.pack(fill="x", padx=30, pady=(0, 8))
        ctk.CTkLabel(frame_cod, text="Código selecionado:",
                     font=ctk.CTkFont(size=13)).pack(side="left")
        self._entry_cod = ctk.CTkEntry(frame_cod, width=130, placeholder_text="02.18")
        self._entry_cod.pack(side="left", padx=(10, 0))

        self._entry_busca = ctk.CTkEntry(
            self.card, placeholder_text="Digite parte do nome para filtrar...", width=420)
        self._entry_busca.pack(padx=30, pady=(0, 6))
        self._entry_busca.bind("<KeyRelease>", self._filtrar)

        frame_lista = ctk.CTkFrame(self.card, fg_color="transparent")
        frame_lista.pack(fill="x", padx=30, pady=(0, 16))

        sb = tk.Scrollbar(frame_lista)
        sb.pack(side="right", fill="y")
        self._listbox = tk.Listbox(
            frame_lista, height=9,
            yscrollcommand=sb.set,
            font=("Consolas", 11),
            selectbackground="#1f6aa5",
            activestyle="none",
            relief="flat", bd=0,
        )
        self._listbox.pack(side="left", fill="x", expand=True)
        sb.config(command=self._listbox.yview)
        self._listbox.bind("<<ListboxSelect>>", self._ao_selecionar)
        self._itens: list[dict] = []

        self._label_status = ctk.CTkLabel(
            self.card, text="", font=ctk.CTkFont(size=11), text_color="gray")
        self._label_status.pack()

        self._btn = ctk.CTkButton(
            self.card, text="Gerar Relatório",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45, width=220,
            command=self._iniciar,
        )
        self._btn.pack(pady=(10, 28))

        self._secretarias: dict = {}
        self._carregar_secretarias()

    def _carregar_secretarias(self):
        if json_disponivel():
            self._secretarias = carregar_secretarias()
            self._popular(self._secretarias)
        else:
            self._label_status.configure(text="⏳ Buscando secretarias na API...")
            threading.Thread(target=self._buscar_api, daemon=True).start()

    def _buscar_api(self):
        from modules.betha.secretarias import executar as atualizar
        try:
            self._secretarias = atualizar()
            self.after(0, lambda: self._popular(self._secretarias))
            self.after(0, lambda: self._label_status.configure(text="✅ Secretarias carregadas."))
        except Exception as e:
            erro = str(e)
            self.after(0, lambda: self._label_status.configure(text=f"❌ {erro}"))

    def _popular(self, secretarias: dict):
        self._listbox.delete(0, "end")
        self._itens = []
        for cod, dados in secretarias.items():
            self._listbox.insert("end", f"  {dados['descricao']}  ({cod})")
            self._itens.append({"codigo": cod})
            for lot in dados.get("lotacoes", []):
                self._listbox.insert("end", f"      └ {lot['descricao']}  ({lot['numero']})")
                self._itens.append({"codigo": lot["numero"]})

    def _filtrar(self, _=None):
        termo = self._entry_busca.get().strip()
        self._popular(buscar_por_texto(termo, self._secretarias) if termo else self._secretarias)

    def _ao_selecionar(self, _=None):
        sel = self._listbox.curselection()
        if not sel:
            return
        codigo = self._itens[sel[0]]["codigo"]
        self._entry_cod.delete(0, "end")
        self._entry_cod.insert(0, codigo)

    def _iniciar(self):
        codigo = self._entry_cod.get().strip()
        if not codigo:
            messagebox.showwarning("Atenção", "Selecione uma secretaria na lista.")
            return
        self._btn.configure(state="disabled", text="Processando...")
        threading.Thread(target=self._worker, args=(codigo,), daemon=True).start()

    def _worker(self, codigo: str):
        try:
            logger.info(f"Gerando relatório por secretaria: {codigo}")
            executar(prefixo=codigo)
            messagebox.showinfo("Sucesso", "Relatório gerado com sucesso!")
        except Exception as e:
            logger.error(f"Erro: {e}")
            messagebox.showerror("Erro", str(e))
        finally:
            self._btn.configure(state="normal", text="Gerar Relatório")