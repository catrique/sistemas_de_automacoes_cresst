import customtkinter as ctk
from tkinter import messagebox
import threading
from modules.soc.baixar_asos import baixar_asos_por_intervalo_data
from services.logger_service import logger

class AsosView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        # Título
        ctk.CTkLabel(self, text="Download de ASOs por Período", 
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 10))

        # Card Central
        self.card = ctk.CTkFrame(self, corner_radius=15)
        self.card.pack(pady=10, padx=40, fill="x")

        # Inputs de Data
        ctk.CTkLabel(self.card, text="Data Inicial:", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))
        self.entry_inicio = ctk.CTkEntry(self.card, placeholder_text="10/03/2026", width=250)
        self.entry_inicio.pack(pady=5)

        ctk.CTkLabel(self.card, text="Data Final:", font=ctk.CTkFont(size=14)).pack(pady=(15, 5))
        self.entry_fim = ctk.CTkEntry(self.card, placeholder_text="10/03/2026", width=250)
        self.entry_fim.pack(pady=5)

        # Texto explicativo
        self.label_info = ctk.CTkLabel(self.card, 
                                       text="O robô irá acessar o SOCGED, filtrar por ASO\ne descarregar todos os arquivos do período.",
                                       font=ctk.CTkFont(size=12), text_color="gray")
        self.label_info.pack(pady=20)

        # --- BOTÃO DE CONFIRMAÇÃO (O que estava faltando) ---
        self.btn_confirmar = ctk.CTkButton(
            self, 
            text="🚀 Iniciar Download", 
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            width=300,
            command=self.executar_download
        )
        self.btn_confirmar.pack(pady=30)

    def executar_download(self):
        data_i = self.entry_inicio.get().strip()
        data_f = self.entry_fim.get().strip()

        if not data_i or not data_f:
            messagebox.showwarning("Atenção", "Por favor, preencha ambas as datas.")
            return

        # Bloqueia o botão para evitar cliques múltiplos
        self.btn_confirmar.configure(state="disabled", text="Processando...")
        
        # Dispara em Thread para não travar a interface
        threading.Thread(target=self._worker, args=(data_i, data_f), daemon=True).start()

    def _worker(self, data_i, data_f):
        try:
            logger.info(f"Iniciando busca de ASOs entre {data_i} e {data_f}...")
            baixar_asos_por_intervalo_data(data_i, data_f)
            messagebox.showinfo("Sucesso", "Download concluído!")
        except Exception as e:
            logger.error(f"Erro no download: {e}")
            messagebox.showerror("Erro", f"Ocorreu uma falha: {e}")
        finally:
            self.btn_confirmar.configure(state="normal", text="🚀 Iniciar Download")