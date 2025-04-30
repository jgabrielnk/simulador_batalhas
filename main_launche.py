# main_launcher.py
from typing import TYPE_CHECKING
import pygame
import time # Para controle de velocidade
from interface_tkinter.app_principal import AplicacaoSimulador


# --- Ponto de Entrada Principal ---
if __name__ == "__main__":
    app = AplicacaoSimulador()
    app.mainloop()