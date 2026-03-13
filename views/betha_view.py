import tkinter as tk
import threading
import customtkinter as ctk
from tkinter import messagebox

from modules.betha.afastamentos import gerar_relatorio as gerar_afastamentos
from modules.betha.atestados import gerar_relatorio as gerar_atestados
from modules.betha.funcionarios_por_secretaria import executar as exportar_por_secretaria
from modules.betha.secretarias import executar as atualizar_secretarias
from services.utils.secretarias_service import (
    carregar_secretarias, buscar_por_texto, json_disponivel,
)
from services.logger_service import logger


# ── Widget auxiliar: Card colapsável ─────────────────────────────────────────

class CardColapsavel(ctk.CTkFrame):
    """Cabeçalho clicável — conteúdo oculto até expandir."""

    def __init__(self, master, titulo: str, emoji: str, ao_expandir, **kwargs):
        super().__init__(master, corner_radius=15, **kwargs)
        self._expandido = False
        self._ao_expandir = ao_expandir

        self._header = ctk.CTkButton(
            self,
            text=f"{emoji}  {titulo}",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            anchor="w",
            command=self._toggle,
        )
        self._header.pack(fill="x", padx=15, pady=12)
        self._corpo = ctk.CTkFrame(self, fg_color="transparent")

    def _toggle(self):
        if self._expandido:
            self._colapsar()
        else:
            self._ao_expandir(self)
            self._expandir()

    def _expandir(self):
        self._corpo.pack(fill="x", padx=20, pady=(0, 15))
        self._expandido = True

    def _colapsar(self):
        self._corpo.pack_forget()
        self._expandido = False

    @property
    def corpo(self) -> ctk.CTkFrame:
        return self._corpo


# ── Widget auxiliar: Seletor de Secretaria ───────────────────────────────────

class SeletorSecretaria(ctk.CTkFrame):
    """
    Campo de busca + listbox. Preenche o entry de código ao selecionar.
    Se o JSON ainda não existir, busca automaticamente da API em background.
    """

    def __init__(self, master, entry_codigo: ctk.CTkEntry, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._entry_codigo = entry_codigo
        self._secretarias: dict = {}

        ctk.CTkLabel(self, text="Buscar secretaria ou lotação:",
                     font=ctk.CTkFont(size=12)).pack(anchor="w")

        self._entry_busca = ctk.CTkEntry(
            self, placeholder_text="Digite parte do nome...", width=380)
        self._entry_busca.pack(fill="x", pady=(4, 6))
        self._entry_busca.bind("<KeyRelease>", self._filtrar)

        frame_lista = ctk.CTkFrame(self, fg_color="transparent")
        frame_lista.pack(fill="x")

        scrollbar = tk.Scrollbar(frame_lista)
        scrollbar.pack(side="right", fill="y")

        self._listbox = tk.Listbox(
            frame_lista,
            height=8,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 11),
            selectbackground="#1f6aa5",
            activestyle="none",
            relief="flat",
            bd=0,
        )
        self._listbox.pack(side="left", fill="x", expand=True)
        scrollbar.config(command=self._listbox.yview)
        self._listbox.bind("<<ListboxSelect>>", self._ao_selecionar)

        self._itens: list[dict] = []

        self._label_status = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color="gray")
        self._label_status.pack(anchor="w", pady=(4, 0))

        self._inicializar()

    def _inicializar(self):
        if json_disponivel():
            self._secretarias = carregar_secretarias()
            self._popular(self._secretarias)
        else:
            self._label_status.configure(
                text="⏳ Buscando secretarias na API pela primeira vez...")
            threading.Thread(target=self._buscar_da_api, daemon=True).start()

    def _buscar_da_api(self):
        try:
            self._secretarias = atualizar_secretarias()
            self.after(0, lambda: self._popular(self._secretarias))
            self.after(0, lambda: self._label_status.configure(text="✅ Secretarias carregadas."))
        except Exception as e:
            erro_msg = str(e)
            logger.error(f"Erro ao buscar secretarias: {erro_msg}")
            self.after(0, lambda: self._label_status.configure(
                text=f"❌ Falha ao carregar secretarias: {erro_msg}"))

    def _popular(self, secretarias: dict):
        self._listbox.delete(0, "end")
        self._itens = []
        for cod_sec, dados in secretarias.items():
            self._listbox.insert("end", f"  {dados['descricao']}  ({cod_sec})")
            self._itens.append({"codigo": cod_sec})
            for lot in dados.get("lotacoes", []):
                self._listbox.insert("end", f"      └ {lot['descricao']}  ({lot['numero']})")
                self._itens.append({"codigo": lot["numero"]})

    def _filtrar(self, _event=None):
        termo = self._entry_busca.get().strip()
        self._popular(
            buscar_por_texto(termo, self._secretarias) if termo else self._secretarias)

    def _ao_selecionar(self, _event=None):
        sel = self._listbox.curselection()
        if not sel:
            return
        codigo = self._itens[sel[0]]["codigo"]
        self._entry_codigo.delete(0, "end")
        self._entry_codigo.insert(0, codigo)

    def recarregar(self):
        self._label_status.configure(text="⏳ Recarregando...")
        threading.Thread(target=self._buscar_da_api, daemon=True).start()


# ── View principal ────────────────────────────────────────────────────────────

class BethaView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")

        ctk.CTkLabel(self, text="Relatórios Betha",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 6))

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._cards: list[CardColapsavel] = []
        self._seletor: SeletorSecretaria | None = None

        self._montar_card_afastamentos()
        self._montar_card_atestados()
        self._montar_card_funcionarios_secretaria()
        self._montar_card_atualizar_secretarias()

    # ── Controle de abertura única ────────────────────────────────────────────

    def _ao_expandir(self, card_aberto: CardColapsavel):
        for card in self._cards:
            if card is not card_aberto and card._expandido:
                card._colapsar()

    def _adicionar_card(self, titulo: str, emoji: str) -> CardColapsavel:
        card = CardColapsavel(
            self._scroll, titulo=titulo, emoji=emoji,
            ao_expandir=self._ao_expandir,
        )
        card.pack(fill="x", padx=10, pady=6)
        self._cards.append(card)
        return card

    # ── Card: Afastamentos ────────────────────────────────────────────────────

    def _montar_card_afastamentos(self):
        card = self._adicionar_card("Relatório de Afastamentos", "📄")
        corpo = card.corpo

        ctk.CTkLabel(corpo,
                     text="Informe um ou mais nomes separados por vírgula.",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", pady=(0, 6))

        self._entry_afastamento = ctk.CTkEntry(
            corpo, placeholder_text="NOME COMPLETO, OUTRO NOME", width=380)
        self._entry_afastamento.pack(anchor="w", pady=(0, 10))

        self._btn_afastamento = ctk.CTkButton(
            corpo, text="Gerar Relatório",
            font=ctk.CTkFont(size=13, weight="bold"), height=40, width=200,
            command=self._iniciar_afastamentos,
        )
        self._btn_afastamento.pack(anchor="w")

    # ── Card: Atestados ───────────────────────────────────────────────────────

    def _montar_card_atestados(self):
        card = self._adicionar_card("Relatório de Atestados", "🏥")
        corpo = card.corpo

        ctk.CTkLabel(corpo,
                     text="Informe um ou mais nomes separados por vírgula.",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", pady=(0, 6))

        self._entry_atestado = ctk.CTkEntry(
            corpo, placeholder_text="NOME COMPLETO, OUTRO NOME", width=380)
        self._entry_atestado.pack(anchor="w", pady=(0, 10))

        self._btn_atestado = ctk.CTkButton(
            corpo, text="Gerar Relatório",
            font=ctk.CTkFont(size=13, weight="bold"), height=40, width=200,
            command=self._iniciar_atestados,
        )
        self._btn_atestado.pack(anchor="w")

    # ── Card: Funcionários por Secretaria ─────────────────────────────────────

    def _montar_card_funcionarios_secretaria(self):
        card = self._adicionar_card("Funcionários por Secretaria", "🏛️")
        corpo = card.corpo

        ctk.CTkLabel(corpo,
                     text="Pesquise e selecione a secretaria ou lotação.\n"
                          "O código será preenchido automaticamente.",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", pady=(0, 8))

        frame_cod = ctk.CTkFrame(corpo, fg_color="transparent")
        frame_cod.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(frame_cod, text="Código selecionado:",
                     font=ctk.CTkFont(size=12)).pack(side="left")
        self._entry_secretaria = ctk.CTkEntry(
            frame_cod, width=120, placeholder_text="02.18")
        self._entry_secretaria.pack(side="left", padx=(8, 0))

        self._seletor = SeletorSecretaria(corpo, entry_codigo=self._entry_secretaria)
        self._seletor.pack(fill="x", pady=(0, 10))

        self._btn_secretaria = ctk.CTkButton(
            corpo, text="Gerar Relatório",
            font=ctk.CTkFont(size=13, weight="bold"), height=40, width=200,
            command=self._iniciar_funcionarios_secretaria,
        )
        self._btn_secretaria.pack(anchor="w")

    # ── Card: Atualizar Secretarias ───────────────────────────────────────────

    def _montar_card_atualizar_secretarias(self):
        card = self._adicionar_card("Atualizar Mapa de Secretarias", "🔄")
        corpo = card.corpo

        ctk.CTkLabel(corpo,
                     text="Busca a estrutura de lotações na API Betha e atualiza\n"
                          "o arquivo secretarias.json usado nos relatórios.",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", pady=(0, 10))

        self._btn_secretarias = ctk.CTkButton(
            corpo, text="Atualizar Agora",
            font=ctk.CTkFont(size=13, weight="bold"), height=40, width=200,
            command=self._iniciar_atualizar_secretarias,
        )
        self._btn_secretarias.pack(anchor="w")

    # ── Workers ───────────────────────────────────────────────────────────────

    def _iniciar_afastamentos(self):
        nomes = self._entry_afastamento.get().strip()
        if not nomes:
            messagebox.showwarning("Atenção", "Informe ao menos um nome.")
            return
        self._btn_afastamento.configure(state="disabled", text="Processando...")
        threading.Thread(target=self._worker_afastamentos, args=(nomes,), daemon=True).start()

    def _worker_afastamentos(self, nomes: str):
        try:
            for nome in [n.strip().upper() for n in nomes.split(",") if n.strip()]:
                logger.info(f"Gerando afastamentos: {nome}")
                gerar_afastamentos(nome)
            messagebox.showinfo("Sucesso", "Relatório(s) de afastamentos gerado(s)!")
        except Exception as e:
            logger.error(f"Erro afastamentos: {e}")
            messagebox.showerror("Erro", str(e))
        finally:
            self._btn_afastamento.configure(state="normal", text="Gerar Relatório")

    def _iniciar_atestados(self):
        nomes = self._entry_atestado.get().strip()
        if not nomes:
            messagebox.showwarning("Atenção", "Informe ao menos um nome.")
            return
        self._btn_atestado.configure(state="disabled", text="Processando...")
        threading.Thread(target=self._worker_atestados, args=(nomes,), daemon=True).start()

    def _worker_atestados(self, nomes: str):
        try:
            for nome in [n.strip().upper() for n in nomes.split(",") if n.strip()]:
                logger.info(f"Gerando atestados: {nome}")
                gerar_atestados(nome)
            messagebox.showinfo("Sucesso", "Relatório(s) de atestados gerado(s)!")
        except Exception as e:
            logger.error(f"Erro atestados: {e}")
            messagebox.showerror("Erro", str(e))
        finally:
            self._btn_atestado.configure(state="normal", text="Gerar Relatório")

    def _iniciar_funcionarios_secretaria(self):
        codigo = self._entry_secretaria.get().strip()
        if not codigo:
            messagebox.showwarning("Atenção", "Selecione uma secretaria na lista.")
            return
        self._btn_secretaria.configure(state="disabled", text="Processando...")
        threading.Thread(target=self._worker_secretaria, args=(codigo,), daemon=True).start()

    def _worker_secretaria(self, codigo: str):
        try:
            logger.info(f"Gerando relatório por secretaria: {codigo}")
            exportar_por_secretaria(prefixo=codigo)
            messagebox.showinfo("Sucesso", "Relatório por secretaria gerado!")
        except Exception as e:
            logger.error(f"Erro funcionários por secretaria: {e}")
            messagebox.showerror("Erro", str(e))
        finally:
            self._btn_secretaria.configure(state="normal", text="Gerar Relatório")

    def _iniciar_atualizar_secretarias(self):
        self._btn_secretarias.configure(state="disabled", text="Atualizando...")
        threading.Thread(target=self._worker_secretarias, daemon=True).start()

    def _worker_secretarias(self):
        try:
            logger.info("Atualizando mapa de secretarias...")
            atualizar_secretarias()
            if self._seletor:
                self._seletor.recarregar()
            messagebox.showinfo("Sucesso", "Mapa de secretarias atualizado!")
        except Exception as e:
            logger.error(f"Erro ao atualizar secretarias: {e}")
            messagebox.showerror("Erro", str(e))
        finally:
            self._btn_secretarias.configure(state="normal", text="Atualizar Agora")