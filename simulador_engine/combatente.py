import pygame
import random
import math
from .utils import calcular_distancia, normalizar_vetor, limitar_valor

ID_COUNTER = 0
# Constante para a força da separação (ajuste conforme necessário)
# Valores maiores empurram mais forte, mas podem causar "tremor"
FORCA_SEPARACAO = 0.98

class Combatente:
    """Representa um único combatente na simulação."""

    def __init__(self, tipo_combatente, estilo_luta, equipe, posicao_inicial, arena_rect):
        """
        Inicializa um combatente individual.

        Args:
            tipo_combatente (TipoCombatente): O modelo base para este combatente.
            estilo_luta (EstiloLuta): O estilo de luta que define modificadores e táticas.
            equipe (int): O ID da equipe à qual o combatente pertence.
            posicao_inicial (tuple): A posição (x, y) inicial.
            arena_rect (pygame.Rect): O retângulo que define os limites da arena.
        """
        global ID_COUNTER
        self.id_unico = ID_COUNTER
        ID_COUNTER += 1

        self.tipo = tipo_combatente
        self.estilo = estilo_luta
        self.equipe = equipe
        self.arena_rect = arena_rect # Limites para movimento

        # Atributos de Estado
        self.posicao = list(posicao_inicial) # Usar lista para poder modificar x, y
        self.hp_atual = self.tipo.hp_max
        self.alvo_atual = None
        self.tempo_recarga_restante = 0 # Cooldown do ataque

        # Atributos Calculados (com base no tipo e estilo)
        self.alcance_efetivo = self.tipo.alcance_base * self.estilo.modificador_alcance
        self.taxa_ataque_efetiva = int(self.tipo.taxa_ataque * self.estilo.modificador_taxa_ataque)

    def esta_vivo(self):
        """Verifica se o combatente ainda tem HP."""
        return self.hp_atual > 0

    def encontrar_alvo(self, todos_combatentes):
        """Encontra o inimigo mais próximo (sem limite de raio de visão)."""
        inimigos = [c for c in todos_combatentes if c.esta_vivo() and c.equipe != self.equipe]
        if not inimigos:
            self.alvo_atual = None
            # DEBUG: print(f"DEBUG: {self.id_unico} não encontrou inimigos vivos na outra equipe.")
            return

        inimigo_escolhido = None
        melhor_valor = float('inf') # Para distância (mais próximo) ou float('-inf') para HP mais baixo

        # --- Estratégia de Mira ---
        if self.estilo.estrategia_mira == "hp_mais_baixo":
            # Ordena por HP e pega o primeiro (mais baixo)
            inimigos.sort(key=lambda c: c.hp_atual)
            if inimigos:
                 inimigo_escolhido = inimigos[0]
                 # DEBUG: print(f"DEBUG: {self.id_unico} mirou em {inimigo_escolhido.id_unico} (HP baixo)")

        else: # Padrão: "mais_proximo"
            pos_atual = self.posicao
            for inimigo in inimigos:
                dist = calcular_distancia(pos_atual, inimigo.posicao)
                if dist < melhor_valor:
                    melhor_valor = dist
                    inimigo_escolhido = inimigo
            # if inimigo_escolhido:
                 # DEBUG: print(f"DEBUG: {self.id_unico} mirou em {inimigo_escolhido.id_unico} (Mais próximo, Dist: {melhor_valor:.1f})")


        # --- CORREÇÃO: Removemos a checagem de raio_visao ---
        # Se um inimigo foi encontrado pela estratégia, ele se torna o alvo.
        self.alvo_atual = inimigo_escolhido

        # if not self.alvo_atual:
             # DEBUG: print(f"DEBUG: {self.id_unico} não conseguiu selecionar um alvo específico após aplicar estratégia.")

    def mover(self, todos_combatentes):
        """
        Move o combatente em direção ao alvo atual,
        aplicando separação para evitar sobreposição.
        """
        if not self.alvo_atual or not self.esta_vivo():
            return

        # 1. Calcular movimento base em direção ao alvo
        direcao_x = self.alvo_atual.posicao[0] - self.posicao[0]
        direcao_y = self.alvo_atual.posicao[1] - self.posicao[1]
        distancia_alvo = math.sqrt(direcao_x**2 + direcao_y**2)

        if distancia_alvo < 0.1: # Já muito perto do alvo, não precisa mover
             pos_desejada_x = self.posicao[0]
             pos_desejada_y = self.posicao[1]
        else:
            vetor_direcao = normalizar_vetor((direcao_x, direcao_y))
            passo_x = vetor_direcao[0] * self.tipo.velocidade
            passo_y = vetor_direcao[1] * self.tipo.velocidade

            # Garante que não ultrapasse o alvo num único passo
            if distancia_alvo < self.tipo.velocidade:
                pos_desejada_x = self.alvo_atual.posicao[0]
                pos_desejada_y = self.alvo_atual.posicao[1]
            else:
                pos_desejada_x = self.posicao[0] + passo_x
                pos_desejada_y = self.posicao[1] + passo_y

        # 2. Calcular vetor de separação
        vetor_separacao_x = 0
        vetor_separacao_y = 0
        vizinhos_proximos = 0 # Contagem de vizinhos muito próximos

        for outro in todos_combatentes:
            if outro == self or not outro.esta_vivo():
                continue

            distancia_outro = calcular_distancia((pos_desejada_x, pos_desejada_y), outro.posicao)
            distancia_minima = self.tipo.tamanho_raio + outro.tipo.tamanho_raio

            # Se a distância *seria* menor que a soma dos raios (colisão)
            if distancia_outro < distancia_minima:
                vizinhos_proximos += 1
                # Calcular vetor de 'outro' para 'self' (direção do empurrão)
                empurrao_x = pos_desejada_x - outro.posicao[0]
                empurrao_y = pos_desejada_y - outro.posicao[1]

                # Normalizar e ponderar pela "invasão" (quanto mais perto, mais forte empurra)
                # Evitar divisão por zero se estiverem exatamente no mesmo ponto
                if distancia_outro < 0.01:
                     # Empurra numa direção aleatória se sobrepostos
                     angle = random.uniform(0, 2 * math.pi)
                     empurrao_x = math.cos(angle)
                     empurrao_y = math.sin(angle)
                     fator_empurrao = 1.0 # Empurrão máximo
                else:
                     # Normaliza o vetor de empurrão
                     mag_empurrao = math.sqrt(empurrao_x**2 + empurrao_y**2)
                     empurrao_x /= mag_empurrao
                     empurrao_y /= mag_empurrao
                     # Pondera pela proximidade (1.0 = colidindo, 0 = no limite)
                     fator_empurrao = (distancia_minima - distancia_outro) / distancia_minima


                # Acumula o vetor de separação ponderado
                vetor_separacao_x += empurrao_x * fator_empurrao
                vetor_separacao_y += empurrao_y * fator_empurrao

        # 3. Combinar movimento base e separação
        pos_final_x = pos_desejada_x
        pos_final_y = pos_desejada_y

        # Só aplica separação se houve vizinhos muito próximos
        if vizinhos_proximos > 0:
            # Normaliza o vetor de separação acumulado (se não for zero)
            mag_total_separacao = math.sqrt(vetor_separacao_x**2 + vetor_separacao_y**2)
            if mag_total_separacao > 0.01:
                 vetor_separacao_x /= mag_total_separacao
                 vetor_separacao_y /= mag_total_separacao

                 # Aplica o empurrão de separação, limitado pela FORCA_SEPARACAO
                 # A força pode ser uma fração da velocidade ou um valor fixo
                 empurrao_aplicado_x = vetor_separacao_x * self.tipo.velocidade * FORCA_SEPARACAO
                 empurrao_aplicado_y = vetor_separacao_y * self.tipo.velocidade * FORCA_SEPARACAO

                 pos_final_x += empurrao_aplicado_x
                 pos_final_y += empurrao_aplicado_y
                 # DEBUG: print(f"DEBUG: {self.id_unico} aplicando separação ({empurrao_aplicado_x:.1f}, {empurrao_aplicado_y:.1f}) devido a {vizinhos_proximos} vizinhos.")


        # 4. Aplicar limites da arena à posição final calculada
        pos_final_x_clamp = limitar_valor(pos_final_x, self.arena_rect.left + self.tipo.tamanho_raio, self.arena_rect.right - self.tipo.tamanho_raio)
        pos_final_y_clamp = limitar_valor(pos_final_y, self.arena_rect.top + self.tipo.tamanho_raio, self.arena_rect.bottom - self.tipo.tamanho_raio)

        # 5. Atualizar a posição do combatente
        # Aplicar somente se a posição calculada for significativamente diferente da atual
        # para evitar "tremor" desnecessário.
        if calcular_distancia(self.posicao, (pos_final_x_clamp, pos_final_y_clamp)) > 0.1:
            self.posicao[0] = pos_final_x_clamp
            self.posicao[1] = pos_final_y_clamp
            # DEBUG: print(f"DEBUG: {self.id_unico} moveu/separou para ({self.posicao[0]:.1f}, {self.posicao[1]:.1f})")
        # else:
            # DEBUG: print(f"DEBUG: {self.id_unico} movimento final muito pequeno, mantendo posição.")

    def atacar(self):
        """
        Tenta atacar o alvo atual. Retorna info do ataque ou None.
        A checagem de alcance e cooldown é feita ANTES de chamar esta função.
        """
        if not self.alvo_atual or not self.esta_vivo() or not self.alvo_atual.esta_vivo():
             return None

        # Calcula o dano
        dano_base = self.tipo.forca_base * self.estilo.modificador_dano
        dano_bonus_vital = self.estilo.bonus_dano_vital
        variacao_dano = random.uniform(0.9, 1.1) # Pequena variação
        dano_total_bruto = (dano_base * variacao_dano) + dano_bonus_vital

        # Aplica resistência do alvo
        reducao = self.alvo_atual.tipo.resistencia
        dano_final = max(1, round(dano_total_bruto - reducao)) # Arredonda o dano final

        # Aplica o dano ao alvo
        self.alvo_atual.receber_dano(dano_final)

        # Reinicia cooldown (importante!)
        self.tempo_recarga_restante = self.taxa_ataque_efetiva

        # print(f"INFO: {self.tipo.nome_tipo} {self.id_unico} atacou {self.alvo_atual.tipo.nome_tipo} {self.alvo_atual.id_unico}, Dano: {dano_final}")

        # Retorna informações sobre o ataque
        return {
            "atacante_id": self.id_unico,
            "alvo_id": self.alvo_atual.id_unico,
            "dano": dano_final
        }
    
    def receber_dano(self, quantidade):
        """Aplica dano ao HP do combatente."""
        self.hp_atual -= quantidade
        if self.hp_atual <= 0:
            self.hp_atual = 0
            # print(f"INFO: {self.tipo.nome_tipo} {self.id_unico} (Equipe {self.equipe}) foi derrotado.")
            self.alvo_atual = None # Perde o alvo se morrer
            
    def atualizar(self, todos_combatentes):
        """Executa a lógica de um tick para este combatente (LÓGICA DE MOVIMENTO AJUSTADA)."""
        if not self.esta_vivo():
            return None

        # 1. Atualizar Cooldown
        if self.tempo_recarga_restante > 0:
            self.tempo_recarga_restante -= 1

        # 2. Gerenciar Alvo
        if not self.alvo_atual or not self.alvo_atual.esta_vivo():
            self.encontrar_alvo(todos_combatentes)
            if not self.alvo_atual:
                 # DEBUG: print(f"DEBUG: {self.id_unico} sem alvo válido após procurar.")
                 return None # Espera até ter alvo

        # 3. Decidir Ação (Atacar ou Mover)
        info_ataque = None
        distancia_ao_alvo = calcular_distancia(self.posicao, self.alvo_atual.posicao)
        esta_no_alcance = distancia_ao_alvo <= self.alcance_efetivo
        pode_atacar_agora = esta_no_alcance and self.tempo_recarga_restante <= 0

        # Prioridade: Atacar se possível
        if pode_atacar_agora:
            # DEBUG: print(f"DEBUG: {self.id_unico} ({self.estilo.tipo_alcance}) ATACANDO (Dist: {distancia_ao_alvo:.1f}, Alc: {self.alcance_efetivo:.1f})")
            info_ataque = self.atacar()
        else:
            # Se não atacou, decidir se move
            precisa_mover = False
            if not esta_no_alcance:
                # Sempre move se estiver fora de alcance
                precisa_mover = True
                # DEBUG: print(f"DEBUG: {self.id_unico} ({self.estilo.tipo_alcance}) MOVENDO (Fora de alcance. Dist: {distancia_ao_alvo:.1f}, Alc: {self.alcance_efetivo:.1f})")
            elif esta_no_alcance and self.tempo_recarga_restante > 0:
                # --- CORREÇÃO: Diferenciação Melee vs Ranged ---
                if self.estilo.tipo_alcance == 'corpo_a_corpo':
                    # Melee continua se aproximando mesmo em alcance se estiver em cooldown
                    precisa_mover = True
                    # DEBUG: print(f"DEBUG: {self.id_unico} ({self.estilo.tipo_alcance}) MOVENDO (Em alcance, mas em cooldown - Melee)")
                else:
                    # Ranged PARA de mover se já está em alcance, mesmo em cooldown
                    precisa_mover = False
                    # DEBUG: print(f"DEBUG: {self.id_unico} ({self.estilo.tipo_alcance}) PARADO (Em alcance, em cooldown - Ranged)")
            # else:
                 # DEBUG: print(f"DEBUG: {self.id_unico} ({self.estilo.tipo_alcance}) PARADO (Em alcance, pronto pra atacar no prox tick)")


            if precisa_mover:
                self.mover(todos_combatentes)

        return info_ataque