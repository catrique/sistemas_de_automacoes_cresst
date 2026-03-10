import logging

logger = logging.getLogger("AutomacaoGRS")
logger.setLevel(logging.INFO)

class GuiHandler(logging.Handler):
    """Handler customizado que redireciona logs para uma função de texto da GUI."""
    def __init__(self, log_func):
        super().__init__()
        self.log_func = log_func

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_func(msg)
        except Exception:
            self.handleError(record)

def configurar_log_gui(funcao_exibir_na_tela):
    """
    Ativa o redirecionamento de logs para a interface gráfica.
    'funcao_exibir_na_tela' deve ser uma função que aceite uma string.
    """
    gui_handler = GuiHandler(funcao_exibir_na_tela)
    gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(gui_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
logger.addHandler(console_handler)