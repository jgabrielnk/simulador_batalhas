import pygame
import random

# Cores
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
CINZA = (100, 100, 100)
VERMELHO_CLARO = (255, 100, 100)
VERDE_CLARO = (100, 255, 100)

class Visualizador:
    """Responsável por desenhar o estado da simulação na tela com Pygame."""

    def __init__(self, largura, altura, titulo="Simulador de Batalha"):
        """
        Inicializa o Pygame e a janela de visualização.

        Args:
            largura (int): Largura da janela.
            altura (int): Altura da janela.
            titulo (str): Título da janela.
        """
        pygame.init()
        pygame.font.init() # Inicializa o módulo de fontes
        self.largura = largura
        self.altura = altura
        self.tela = pygame.display.set_mode((largura, altura))
        pygame.display.set_caption(titulo)
        self.fonte_padrao = pygame.font.SysFont(None, 24) # Fonte para texto
        self.fonte_pequena = pygame.font.SysFont(None, 18) # Fonte para HP
        self.fonte_legenda = pygame.font.SysFont(None, 20) # Fonte menor para legenda
        self.fonte_estado = pygame.font.SysFont(None, 16) # Para estado (Fugindo, Cansado)
        self.cores_equipes = {} # Cache de cores das equipes

    def _get_cor_equipe(self, id_equipe, config_cenario):
        """Obtém a cor para uma equipe, usando cache."""
        if id_equipe not in self.cores_equipes:
             cor_padrao = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
             cor = cor_padrao
             if config_cenario and 'equipes' in config_cenario:
                 for eq_data in config_cenario['equipes']:
                     if eq_data.get('id_equipe') == id_equipe:
                         cor = eq_data.get('cor', cor_padrao)
                         break
             self.cores_equipes[id_equipe] = tuple(cor) # Garante que é tupla
        return self.cores_equipes[id_equipe]


    def desenhar(self, motor_simulacao, configurador):
        """
        Desenha o estado atual da simulação.

        Args:
            motor_simulacao (MotorSimulacao): O motor contendo o estado atual.
            configurador (Configurador): Para buscar cores das equipes.
        """
        # 1. Limpa a tela (fundo cinza)
        self.tela.fill(CINZA)

        # 2. Desenha a Arena (opcional, se quiser bordas)
        # arena_rect = configurador.get_arena_rect()
        # pygame.draw.rect(self.tela, PRETO, arena_rect, 1) # Desenha borda preta

        # 3. Desenha os combatentes vivos
        config_cenario = configurador.get_config_cenario()
        for combatente in motor_simulacao.get_combatentes_vivos():
            # Acessa dados via componentes
            pos_x = int(combatente.movimento.posicao[0])
            pos_y = int(combatente.movimento.posicao[1])
            raio = combatente.movimento.tamanho_raio
            cor = configurador.get_cor_equipe(combatente.equipe)
            hp_ratio = combatente.estado.hp_atual / combatente.estado.hp_max if combatente.estado.hp_max > 0 else 0

            # Desenha corpo
            pygame.draw.circle(self.tela, cor, (pos_x, pos_y), raio)
            # Desenha Facing (opcional - pequena linha na direção)
            dir_x, dir_y = combatente.movimento.direcao
            pygame.draw.line(self.tela, PRETO, (pos_x, pos_y),
                             (pos_x + dir_x * raio, pos_y + dir_y * raio), 2)

            # Desenha barra de HP
            largura_hp = int(raio * 2 * hp_ratio)
            altura_hp = 4
            pos_hp_x = pos_x - raio
            pos_hp_y = pos_y - raio - altura_hp - 2
            pygame.draw.rect(self.tela, VERMELHO_CLARO, (pos_hp_x, pos_hp_y, raio * 2, altura_hp))
            pygame.draw.rect(self.tela, VERDE_CLARO, (pos_hp_x, pos_hp_y, largura_hp, altura_hp))

            # Desenha barra de Stamina (opcional)
            if hasattr(combatente, 'stamina'):
                stamina_ratio = combatente.stamina.stamina_atual / combatente.stamina.stamina_max if combatente.stamina.stamina_max > 0 else 0
                largura_stamina = int(raio * 2 * stamina_ratio)
                altura_stamina = 3
                pos_stamina_y = pos_hp_y - altura_stamina - 1
                AMARELO = (255, 255, 0)
                CINZA_ESCURO = (50, 50, 50)
                pygame.draw.rect(self.tela, CINZA_ESCURO, (pos_hp_x, pos_stamina_y, raio * 2, altura_stamina))
                pygame.draw.rect(self.tela, AMARELO, (pos_hp_x, pos_stamina_y, largura_stamina, altura_stamina))

            # Exibe Estado (Fugindo, Cansado, etc) - opcional
            estado_txt = combatente.estado.estado_atual
            if estado_txt != "Ocioso" and estado_txt != "Movendo" and estado_txt != "Atacando": # Mostra só estados especiais
                estado_surface = self.fonte_estado.render(estado_txt, True, BRANCO)
                estado_rect = estado_surface.get_rect(center=(pos_x, pos_y + raio + 8))
                self.tela.blit(estado_surface, estado_rect)

            # Opcional: Desenhar o alvo (uma linha fina)
            # if combatente.alvo_atual:
            #    pygame.draw.line(self.tela, (255, 255, 0, 100), # Amarelo transparente
            #                     (pos_x, pos_y),
            #                     (int(combatente.alvo_atual.posicao[0]), int(combatente.alvo_atual.posicao[1])),
            #                     1)

        # 4. Exibe informações (Rodada, Contagem, etc.)
        vivos_por_equipe = {}
        for c in motor_simulacao.get_combatentes_vivos():
            vivos_por_equipe[c.equipe] = vivos_por_equipe.get(c.equipe, 0) + 1

        info_texto = f"Rodada: {motor_simulacao.rodada} | FPS: {int(pygame.time.Clock().get_fps())} | Vel: {motor_simulacao.velocidade_sim:.1f}x | Vivos: "
        info_texto += " ".join([f"E{eq}({configurador.get_cor_equipe(eq)}):{cont}" for eq, cont in vivos_por_equipe.items()])
        texto_surface = self.fonte_padrao.render(info_texto, True, BRANCO)
        self.tela.blit(texto_surface, (10, 10))
        
        # 5. Exibe legenda	
        pos_y_legenda = self.altura - 70 # Posição inicial Y (perto do fundo)
        incremento_y = 18 # Espaço entre linhas

        legendas = [
            "[ESPAÇO] Pausar/Continuar",
            "[R] Reiniciar Simulação",
            "[PgUp] Acelerar",
            "[PgDn] Desacelerar",
            "[ESC] Sair da Simulação"
        ]

        for texto_legenda in legendas:
            legenda_surface = self.fonte_legenda.render(texto_legenda, True, BRANCO)
            self.tela.blit(legenda_surface, (10, pos_y_legenda))
            pos_y_legenda += incremento_y

        # 6. Exibe mensagem de fim de jogo
        if motor_simulacao.terminou():
            resultado = motor_simulacao.get_resultado()
            if resultado is not None:
                texto_fim = f"FIM DE JOGO! Equipe {resultado} venceu!"
                cor_vencedor = configurador.get_cor_equipe(resultado)
            else:
                texto_fim = "FIM DE JOGO! Empate ou Mútua Destruição!"
                cor_vencedor = BRANCO
            texto_fim_surface = self.fonte_padrao.render(texto_fim, True, cor_vencedor)
            texto_rect = texto_fim_surface.get_rect(center=(self.largura // 2, self.altura // 2))
            pygame.draw.rect(self.tela, PRETO, texto_rect.inflate(20, 10)) # Fundo para o texto
            self.tela.blit(texto_fim_surface, texto_rect)

        # 7. Atualiza a tela
        pygame.display.flip()

    def fechar(self):
        """Encerra o Pygame."""
        pygame.quit()