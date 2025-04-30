# simulador_engine/components/movimento_component.py
import math
import random
from .base_component import BaseComponent
from ..utils import calcular_distancia, normalizar_vetor, limitar_valor

FORCA_SEPARACAO = 1.0

class MovimentoComponent(BaseComponent):
        def __init__(self, combatente_owner, velocidade_base, tamanho_raio, arena_rect):
            super().__init__(combatente_owner)
            self.velocidade_base = velocidade_base
            self.posicao = list(combatente_owner.posicao_inicial) # Pega do owner agora
            self.direcao = (random.uniform(-1, 1), random.uniform(-1, 1)) # Direção inicial aleatória
            self.direcao = normalizar_vetor(self.direcao)
            self.tamanho_raio = tamanho_raio
            self.arena_rect = arena_rect
            self.alvo_movimento = None # Pode ser um Combatente ou uma Posição (para fuga)

        def update(self, todos_combatentes, motor_simulacao):
            estado = self.owner.estado.estado_atual
            if not self.owner.estado.esta_vivo or estado == "Atacando": # Não move se morto ou atacando
                return

            # Determina o alvo do movimento com base no estado
            if estado == "Fugindo":
                 self.definir_alvo_fuga(todos_combatentes)
            elif estado == "Movendo" or estado == "Ocioso": # Se ocioso, pode precisar se mover para o alvo
                 self.alvo_movimento = self.owner.ataque.alvo_atual # Pega alvo do AtaqueComponent

            if not self.alvo_movimento:
                # TODO: Comportamento Ocioso (vagar?)
                return # Sem alvo, não move

            # Calcula velocidade efetiva (considera fadiga)
            mod_fadiga = self.owner.stamina.get_modificador_fadiga()
            velocidade_atual = self.velocidade_base * mod_fadiga

            if velocidade_atual <= 0: return # Cansado demais para mover

            # Calcula custo de stamina
            custo_stamina_tick = self.owner.stamina.custo_movimento * (1.0 / motor_simulacao.FPS_ALVO if motor_simulacao.FPS_ALVO > 0 else 1.0) # Ajusta custo por tick

            # Tenta gastar stamina, se não conseguir, não move
            if not self.owner.stamina.gastar_stamina(custo_stamina_tick):
                 # TODO: Visualizar "Cansado!"
                 self.owner.estado.estado_atual = "Cansado" # Mudar estado?
                 return

            # Ponto de destino (posição do alvo ou ponto de fuga)
            if isinstance(self.alvo_movimento, tuple): # É uma posição (fuga)
                 ponto_destino = self.alvo_movimento
            else: # É um combatente
                 ponto_destino = self.alvo_movimento.movimento.posicao


            # --- Lógica de Movimento e Separação (similar à anterior) ---
            direcao_x = ponto_destino[0] - self.posicao[0]
            direcao_y = ponto_destino[1] - self.posicao[1]
            distancia_destino = math.sqrt(direcao_x**2 + direcao_y**2)

            if distancia_destino < 0.1:
                 if estado == "Fugindo": self.definir_alvo_fuga(todos_combatentes) # Atingiu ponto de fuga, calcula novo
                 return # Já chegou ou muito perto

            vetor_direcao_desejada = normalizar_vetor((direcao_x, direcao_y))

            # Aplica velocidade
            passo_x = vetor_direcao_desejada[0] * velocidade_atual
            passo_y = vetor_direcao_desejada[1] * velocidade_atual

            # Guarda a direção principal do movimento (para Facing)
            if abs(passo_x) > 0.01 or abs(passo_y) > 0.01:
                 self.direcao = normalizar_vetor((passo_x, passo_y))

            pos_desejada_x = self.posicao[0] + passo_x
            pos_desejada_y = self.posicao[1] + passo_y

            # --- Separação ---
            vetor_separacao_x = 0
            vetor_separacao_y = 0
            vizinhos_proximos = 0
            for outro in todos_combatentes:
                # Só considera outros vivos para separação
                if outro == self.owner or not outro.estado.esta_vivo: continue

                dist_outro = calcular_distancia((pos_desejada_x, pos_desejada_y), outro.movimento.posicao)
                dist_minima = self.tamanho_raio + outro.movimento.tamanho_raio

                if dist_outro < dist_minima:
                    vizinhos_proximos += 1
                    empurrao_x = pos_desejada_x - outro.movimento.posicao[0]
                    empurrao_y = pos_desejada_y - outro.movimento.posicao[1]
                    mag_empurrao = math.sqrt(empurrao_x**2 + empurrao_y**2)
                    fator_empurrao = (dist_minima - dist_outro) / dist_minima
                    if mag_empurrao > 0.01:
                        vetor_separacao_x += (empurrao_x / mag_empurrao) * fator_empurrao
                        vetor_separacao_y += (empurrao_y / mag_empurrao) * fator_empurrao
                    else: # Exatamente sobrepostos
                         angle = random.uniform(0, 2 * math.pi)
                         vetor_separacao_x += math.cos(angle)
                         vetor_separacao_y += math.sin(angle)

            # Combina e aplica
            pos_final_x = pos_desejada_x
            pos_final_y = pos_desejada_y
            if vizinhos_proximos > 0:
                 mag_total_separacao = math.sqrt(vetor_separacao_x**2 + vetor_separacao_y**2)
                 if mag_total_separacao > 0.01:
                     # Força de separação é proporcional à velocidade atual (reduzida por fadiga)
                     empurrao_aplicado_x = (vetor_separacao_x / mag_total_separacao) * velocidade_atual * FORCA_SEPARACAO
                     empurrao_aplicado_y = (vetor_separacao_y / mag_total_separacao) * velocidade_atual * FORCA_SEPARACAO
                     pos_final_x += empurrao_aplicado_x
                     pos_final_y += empurrao_aplicado_y

            # Clamp e Atualiza posição
            self.posicao[0] = limitar_valor(pos_final_x, self.arena_rect.left + self.tamanho_raio, self.arena_rect.right - self.tamanho_raio)
            self.posicao[1] = limitar_valor(pos_final_y, self.arena_rect.top + self.tamanho_raio, self.arena_rect.bottom - self.tamanho_raio)

        def definir_alvo_fuga(self, todos_combatentes):
             """Define um ponto na borda da arena, longe dos inimigos."""
             inimigos_visiveis = [c for c in todos_combatentes if c.equipe != self.owner.equipe and c.estado.esta_vivo]
             if not inimigos_visiveis:
                  # Sem inimigos, foge para a borda mais próxima
                  meio_x = self.arena_rect.centerx
                  meio_y = self.arena_rect.centery
                  if abs(self.posicao[0] - self.arena_rect.left) < abs(self.posicao[0] - self.arena_rect.right): target_x = self.arena_rect.left + 10
                  else: target_x = self.arena_rect.right - 10
                  if abs(self.posicao[1] - self.arena_rect.top) < abs(self.posicao[1] - self.arena_rect.bottom): target_y = self.arena_rect.top + 10
                  else: target_y = self.arena_rect.bottom - 10
                  self.alvo_movimento = (target_x, target_y)
                  return

             # Calcula o centro de massa dos inimigos próximos (ou todos)
             avg_enemy_x = sum(e.movimento.posicao[0] for e in inimigos_visiveis) / len(inimigos_visiveis)
             avg_enemy_y = sum(e.movimento.posicao[1] for e in inimigos_visiveis) / len(inimigos_visiveis)

             # Vetor de fuga (longe do centro inimigo)
             fuga_x = self.posicao[0] - avg_enemy_x
             fuga_y = self.posicao[1] - avg_enemy_y
             fuga_norm = normalizar_vetor((fuga_x, fuga_y))

             # Projeta um ponto longe na direção de fuga
             ponto_fuga_x = self.posicao[0] + fuga_norm[0] * 500 # Projeta longe
             ponto_fuga_y = self.posicao[1] + fuga_norm[1] * 500

             # Clampa para a borda da arena
             ponto_fuga_x = limitar_valor(ponto_fuga_x, self.arena_rect.left + 10, self.arena_rect.right - 10)
             ponto_fuga_y = limitar_valor(ponto_fuga_y, self.arena_rect.top + 10, self.arena_rect.bottom - 10)
             self.alvo_movimento = (ponto_fuga_x, ponto_fuga_y)
             #print(f"DEBUG FUGA {self.owner.id_unico}: Indo para {self.alvo_movimento}")