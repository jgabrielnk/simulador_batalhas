# interface_tkinter/app_principal.py
import tkinter as tk
from typing import TYPE_CHECKING
import pygame
# Importa as classes das páginas
from .paginas import (
    PaginaMenuPrincipal, PaginaCriarSimulacao, PaginaSimulacoesCriadas,
    PaginaEscolherTipoObjeto, PaginaListarEditarObjeto, PaginaEditarDetalhesObjeto
)
# Importa as classes necessárias do engine Pygame
from simulador_engine.configurador_pygame import ConfiguradorPygame
from simulador_engine.motor import MotorSimulacao
from simulador_engine.visualizador import Visualizador

# --- Função para Rodar a Simulação Pygame ---
def iniciar_simulacao_pygame(dados_cenario):
    """Inicializa e executa o loop da simulação Pygame."""

    # --- Inicialização Pygame ---
    pygame.init() # Garante que pygame está inicializado
    pygame.font.init()

    # --- Configuração e Criação ---
    try:
        config_pygame = ConfiguradorPygame(dados_cenario)
        combatentes_iniciais = config_pygame.criar_combatentes_iniciais()
        if not combatentes_iniciais:
            print("Erro: Não foi possível criar combatentes para a simulação Pygame.")
            pygame.quit()
            return # Retorna para o Tkinter

        arena_rect = config_pygame.get_arena_rect()
        motor = MotorSimulacao(combatentes_iniciais)
        visualizador = Visualizador(arena_rect.width, arena_rect.height, titulo=dados_cenario.get("nome_simulacao", "Simulação"))
        clock = pygame.time.Clock()

    except Exception as e:
        print(f"Erro durante a inicialização do Pygame/Configuração: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        return # Retorna para o Tkinter


    # --- Variáveis de Controle da Simulação ---
    rodando_pygame = True
    velocidade_simulacao = 1.0 # 1.0 = normal, > 1.0 = rápido, < 1.0 = lento
    pausado = False
    ticks_para_atualizar = 1 # Quantos ticks do motor por frame real

    # Adiciona controle de velocidade ao motor (precisa ser adicionado na classe MotorSimulacao)
    if not hasattr(motor, 'velocidade_sim'):
         motor.velocidade_sim = velocidade_simulacao

    # --- Loop Principal Pygame ---
    while rodando_pygame:
        # --- Tratamento de Eventos Pygame ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                rodando_pygame = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: # Fecha com ESC
                    rodando_pygame = False
                if event.key == pygame.K_SPACE: # Pausa/Despausa com Espaço
                    pausado = not pausado
                    print("Pausado:", pausado)
                if event.key == pygame.K_r: # Reinicia (Recarrega cenário)
                     print("Reiniciando simulação...")
                     # Recria tudo
                     try:
                          combatentes_iniciais = config_pygame.criar_combatentes_iniciais()
                          motor = MotorSimulacao(combatentes_iniciais)
                          motor.velocidade_sim = velocidade_simulacao # Mantem velocidade
                          pausado = False
                     except Exception as e:
                          print(f"Erro ao reiniciar: {e}")
                          rodando_pygame = False # Para se não conseguir reiniciar
                if event.key == pygame.K_PAGEUP: # Aumenta velocidade
                    velocidade_simulacao = min(5.0, velocidade_simulacao + 0.5)
                    motor.velocidade_sim = velocidade_simulacao
                    print(f"Velocidade: {velocidade_simulacao:.1f}x")
                if event.key == pygame.K_PAGEDOWN: # Diminui velocidade
                    velocidade_simulacao = max(0.1, velocidade_simulacao - 0.5)
                    motor.velocidade_sim = velocidade_simulacao
                    print(f"Velocidade: {velocidade_simulacao:.1f}x")


        # --- Lógica da Simulação ---
        if not pausado and not motor.terminou():
            # Controle de velocidade: decide quantos ticks do motor rodar
            ticks_para_atualizar = max(1, int(velocidade_simulacao)) # Roda pelo menos 1 tick
            # Se velocidade < 1, precisa de lógica mais complexa (rodar 1 tick a cada N frames)
            # Simplificação: velocidade < 1 apenas desacelera o FPS visual abaixo
            # Ou uma abordagem melhor: acumular tempo delta.

            # Roda N ticks do motor
            for _ in range(ticks_para_atualizar):
                 if not motor.terminou(): # Checa de novo a cada tick
                     motor.atualizar()
                 else:
                     break

        # --- Desenho ---
        visualizador.desenhar(motor, config_pygame) # Passa o config para pegar cores, etc.

        # --- Controle de FPS ---
        # Ajusta o FPS visual com base na velocidade para dar a sensação de aceleração/desaceleração
        fps_alvo = 60
        # Se velocidade < 1, roda mais devagar. Se > 1, tenta rodar a 60 FPS, motor faz o resto.
        fps_real = fps_alvo # * velocidade_simulacao # Desacelerar FPS pode ficar "travado"
        clock.tick(fps_real)


    # --- Fim da Simulação Pygame ---
    print("Encerrando Pygame...")
    pygame.quit()


class AplicacaoSimulador(tk.Tk):
    """Classe principal da aplicação Tkinter."""
    def __init__(self):
        super().__init__()
        self.title("Configurador de Simulação de Batalha")
        largura_janela = 700
        altura_janela = 650
        pos_x = (self.winfo_screenwidth() // 2) - (largura_janela // 2)
        pos_y = (self.winfo_screenheight() // 2) - (altura_janela // 2)
        self.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
        self.resizable(True, True) # Permite redimensionar

        # Container para as páginas
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.paginas = {} # Dicionário para guardar instâncias das páginas
        self.pagina_atual = None

        # Adiciona todas as páginas ao dicionário (sem mostrá-las ainda)
        for F in (PaginaMenuPrincipal, PaginaCriarSimulacao, PaginaSimulacoesCriadas,
                  PaginaEscolherTipoObjeto, PaginaListarEditarObjeto, PaginaEditarDetalhesObjeto):
            nome_pagina = F.__name__
            # As páginas que precisam de args no __init__ não são pré-carregadas aqui
            # Elas serão instanciadas quando chamadas por mostrar_pagina
            # self.paginas[nome_pagina] = F(container, self)

        self.container = container
        self.mostrar_pagina(PaginaMenuPrincipal) # Começa no menu principal

    def mostrar_pagina(self, classe_pagina, *args, **kwargs):
        """Mostra a página solicitada no container."""
        nome_pagina = classe_pagina.__name__
        print(f"Mostrando página: {nome_pagina} com args: {args}, kwargs: {kwargs}") # Debug

        # Limpa o container anterior
        if self.pagina_atual:
             self.pagina_atual.destroy()

        # Cria a nova página passando os argumentos necessários
        try:
            frame = classe_pagina(self.container, self, *args, **kwargs)
            self.pagina_atual = frame
            frame.pack(fill="both", expand=True) # Usa pack aqui
            # frame.grid(row=0, column=0, sticky="nsew") # Ou grid se preferir
        except Exception as e:
             print(f"Erro ao criar/mostrar a página {nome_pagina}: {e}")
             import traceback
             traceback.print_exc()
             # Volta ao menu principal em caso de erro grave
             if nome_pagina != "PaginaMenuPrincipal":
                  self.mostrar_pagina(PaginaMenuPrincipal)


    def iniciar_pygame(self, dados_cenario):
        """Esconde o Tkinter e inicia a simulação Pygame."""
        print("Escondendo Tkinter e iniciando Pygame...")
        self.withdraw() # Esconde a janela Tkinter
        try:
            # Chama a função que está no main_launcher (ou onde quer que a lógica Pygame esteja)
            iniciar_simulacao_pygame(dados_cenario)
        except Exception as e:
            print(f"Erro durante a execução do Pygame: {e}")
            import traceback
            traceback.print_exc()
            # Garante que o Tkinter reapareça mesmo se Pygame falhar
        finally:
             print("Simulação Pygame encerrada. Reexibindo Tkinter...")
             self.deiconify() # Reexibe a janela Tkinter

    def sair(self):
        """Fecha a aplicação."""
        self.quit()
        self.destroy()