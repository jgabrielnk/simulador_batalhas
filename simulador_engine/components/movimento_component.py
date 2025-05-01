# simulador_engine/components/movimento_component.py
import math
import random
from .base_component import BaseComponent
from ..utils import calcular_distancia, normalizar_vetor, limitar_valor

FORCA_SEPARACAO = 1.0 # Você aumentou, ok.

class MovimentoComponent(BaseComponent):
        def __init__(self, combatente_owner, velocidade_base, tamanho_raio, arena_rect):
            super().__init__(combatente_owner)
            self.velocidade_base = velocidade_base
            self.posicao = list(combatente_owner.posicao_inicial)
            self.direcao = normalizar_vetor((random.uniform(-1, 1), random.uniform(-1, 1)))
            self.tamanho_raio = tamanho_raio
            self.arena_rect = arena_rect
            # MUDANÇA: Não vamos mais guardar self.alvo_movimento aqui.
            # A decisão de para onde mover será feita inteiramente no update.

        def update(self, todos_combatentes, motor_simulacao):
            """Atualiza a posição do combatente com base no seu estado e alvo."""

            estado_atual = self.owner.estado.estado_atual

            # 1. Condições para NÃO mover:
            if not self.owner.estado.esta_vivo or estado_atual == "Atacando":
                return

            # 2. Determinar o PONTO DE DESTINO baseado no estado:
            ponto_destino = None
            is_fugindo = False # Flag para lógica específica de fuga

            if estado_atual == "Fugindo":
                is_fugindo = True
                ponto_destino = self.calcular_ponto_fuga(todos_combatentes) # Calcula e retorna o ponto (x,y) ou None
                if ponto_destino is None:
                    #print(f"DEBUG Movimento: {self.owner.id_unico} em fuga, mas não calculou ponto.")
                    return # Não conseguiu calcular ponto de fuga, não move

            elif estado_atual == "Movendo":
                alvo_ataque = self.owner.ataque.alvo_atual
                if alvo_ataque and alvo_ataque.estado.esta_vivo:
                    ponto_destino = alvo_ataque.movimento.posicao
                else:
                    # Se o estado é Movendo mas não tem alvo válido, volta para Ocioso
                    self.owner.estado.estado_atual = "Ocioso"
                    #print(f"DEBUG Movimento: {self.owner.id_unico} estava Movendo sem alvo, agora Ocioso.")
                    return # Sem alvo válido, não move

            elif estado_atual == "Ocioso" or estado_atual == "Cansado":
                # Se está ocioso ou cansado, SÓ move se estiver FORA de alcance do alvo atual
                alvo_ataque = self.owner.ataque.alvo_atual
                if alvo_ataque and alvo_ataque.estado.esta_vivo:
                    dist_ataque = calcular_distancia(self.posicao, alvo_ataque.movimento.posicao)
                    alcance_ajustado = self.owner.ataque.alcance_efetivo + alvo_ataque.movimento.tamanho_raio
                    # Só define ponto_destino se estiver fora de alcance
                    if dist_ataque > alcance_ajustado:
                        ponto_destino = alvo_ataque.movimento.posicao
                        # Se estava Ocioso/Cansado e precisa mover, muda estado para Movendo
                        if estado_atual != "Movendo":
                             self.owner.estado.estado_atual = "Movendo"
                             #print(f"DEBUG Movimento: {self.owner.id_unico} Ocioso/Cansado começou a Mover para {alvo_ataque.id_unico}")

            # Se após toda a lógica, não há ponto de destino, não faz nada
            if ponto_destino is None:
                #print(f"DEBUG Movimento: {self.owner.id_unico} sem ponto de destino no estado {estado_atual}.")
                return

            # 3. Calcular Velocidade e Custo de Stamina:
            mod_fadiga = self.owner.stamina.get_modificador_fadiga()
            # Fuga pode ter velocidade ligeiramente aumentada? Opcional.
            # if is_fugindo: mod_fadiga *= 1.1
            velocidade_atual = self.velocidade_base * mod_fadiga

            if velocidade_atual <= 0.01: # Praticamente parado devido à fadiga
                #print(f"DEBUG Movimento: {self.owner.id_unico} muito cansado para mover (Vel: {velocidade_atual:.2f})")
                # Se estava tentando mover, mas cansou, muda estado para Cansado
                if estado_atual == "Movendo" or estado_atual == "Fugindo":
                     self.owner.estado.estado_atual = "Cansado"
                return

            # Gasto de Stamina (agora só tenta gastar se for realmente mover)
            # Custo maior ao fugir? Opcional.
            fator_custo_fuga = 1.5 if is_fugindo else 1.0
            custo_stamina_tick = self.owner.stamina.custo_movimento * fator_custo_fuga
            if not self.owner.stamina.gastar_stamina(custo_stamina_tick):
                 #print(f"DEBUG Movimento: {self.owner.id_unico} sem stamina para mover (Estado: {estado_atual})")
                 self.owner.estado.estado_atual = "Cansado"
                 return # Não conseguiu gastar stamina, não move

            # 4. Calcular Vetor de Movimento Base:
            direcao_x = ponto_destino[0] - self.posicao[0]
            direcao_y = ponto_destino[1] - self.posicao[1]
            distancia_destino = math.sqrt(direcao_x**2 + direcao_y**2)

            # Condição para parar perto do destino
            limiar_parada = velocidade_atual * 0.5 # Para perto quando a distância é menor que meio passo
            if distancia_destino < limiar_parada:
                # Se estava fugindo e alcançou o ponto, recalcula na próxima vez
                # Se estava movendo para atacar, para aqui (será Ocioso no próximo tick se em alcance)
                #print(f"DEBUG Movimento: {self.owner.id_unico} chegou perto do destino (Dist: {distancia_destino:.1f})")
                # Poderia definir posição exata do ponto? Ou deixar a separação ajustar?
                # Deixar como está por enquanto.
                return

            vetor_direcao_desejada = normalizar_vetor((direcao_x, direcao_y))
            passo_x = vetor_direcao_desejada[0] * velocidade_atual
            passo_y = vetor_direcao_desejada[1] * velocidade_atual

            # Atualiza facing
            if abs(passo_x) > 0.01 or abs(passo_y) > 0.01:
                 self.direcao = normalizar_vetor((passo_x, passo_y))

            pos_desejada_x = self.posicao[0] + passo_x
            pos_desejada_y = self.posicao[1] + passo_y

            # 5. Calcular e Aplicar Separação:
            vetor_separacao_x = 0
            vetor_separacao_y = 0
            vizinhos_proximos = 0
            for outro in todos_combatentes:
                if outro == self.owner or not outro.estado.esta_vivo: continue
                # Usa posição ATUAL do outro para calcular separação
                dist_outro = calcular_distancia((pos_desejada_x, pos_desejada_y), outro.movimento.posicao)
                dist_minima = self.tamanho_raio + outro.movimento.tamanho_raio
                if dist_outro < dist_minima:
                    # ... (cálculo do empurrão - código anterior OK) ...
                    vizinhos_proximos += 1
                    empurrao_x = pos_desejada_x - outro.movimento.posicao[0]
                    empurrao_y = pos_desejada_y - outro.movimento.posicao[1]
                    mag_empurrao = math.sqrt(empurrao_x**2 + empurrao_y**2)
                    fator_empurrao = (dist_minima - dist_outro) / max(dist_minima, 0.1) # Evita divisão por zero
                    if mag_empurrao > 0.01:
                        vetor_separacao_x += (empurrao_x / mag_empurrao) * fator_empurrao
                        vetor_separacao_y += (empurrao_y / mag_empurrao) * fator_empurrao
                    else: # Sobrepostos
                         angle = random.uniform(0, 2 * math.pi)
                         vetor_separacao_x += math.cos(angle) * fator_empurrao # Aplica fator mesmo sobreposto
                         vetor_separacao_y += math.sin(angle) * fator_empurrao


            pos_final_x = pos_desejada_x
            pos_final_y = pos_desejada_y
            if vizinhos_proximos > 0:
                 mag_total_separacao = math.sqrt(vetor_separacao_x**2 + vetor_separacao_y**2)
                 if mag_total_separacao > 0.01:
                     fator_forca_separacao = FORCA_SEPARACAO * (1.0 - mod_fadiga * 0.5) # Separação menos eficaz se cansado?
                     # Força de separação limitada pela velocidade atual para não "teleportar"
                     forca_sep_aplicada = min(velocidade_atual, mag_total_separacao * fator_forca_separacao)

                     empurrao_aplicado_x = (vetor_separacao_x / mag_total_separacao) * forca_sep_aplicada
                     empurrao_aplicado_y = (vetor_separacao_y / mag_total_separacao) * forca_sep_aplicada

                     pos_final_x += empurrao_aplicado_x
                     pos_final_y += empurrao_aplicado_y
                     #print(f"DEBUG Separação: {self.owner.id_unico} aplicando ({empurrao_aplicado_x:.1f}, {empurrao_aplicado_y:.1f})")


            # 6. Clamp na Arena e Atualizar Posição:
            pos_final_x_clamp = limitar_valor(pos_final_x, self.arena_rect.left + self.tamanho_raio, self.arena_rect.right - self.tamanho_raio)
            pos_final_y_clamp = limitar_valor(pos_final_y, self.arena_rect.top + self.tamanho_raio, self.arena_rect.bottom - self.tamanho_raio)

            # Só atualiza se houve mudança significativa
            if calcular_distancia(self.posicao, (pos_final_x_clamp, pos_final_y_clamp)) > 0.1:
                self.posicao[0] = pos_final_x_clamp
                self.posicao[1] = pos_final_y_clamp
            #else:
            #    print(f"DEBUG Movimento: {self.owner.id_unico} movimento final muito pequeno.")


        def calcular_ponto_fuga(self, todos_combatentes):
             """Calcula e retorna um ponto de fuga (tupla x,y) ou None."""
             # (Código interno desta função permanece o mesmo da versão anterior)
             inimigos_visiveis = [c for c in todos_combatentes if c.equipe != self.owner.equipe and c.estado.esta_vivo]
             ponto_fuga = None # Valor padrão
             if not inimigos_visiveis:
                  # Foge para borda mais próxima
                  meio_x = self.arena_rect.centerx
                  meio_y = self.arena_rect.centery
                  if abs(self.posicao[0] - self.arena_rect.left) < abs(self.posicao[0] - self.arena_rect.right): target_x = self.arena_rect.left + 10
                  else: target_x = self.arena_rect.right - 10
                  if abs(self.posicao[1] - self.arena_rect.top) < abs(self.posicao[1] - self.arena_rect.bottom): target_y = self.arena_rect.top + 10
                  else: target_y = self.arena_rect.bottom - 10
                  ponto_fuga = (target_x, target_y)
             else:
                  # Calcula centro de massa inimigo
                  try:
                      avg_enemy_x = sum(e.movimento.posicao[0] for e in inimigos_visiveis) / len(inimigos_visiveis)
                      avg_enemy_y = sum(e.movimento.posicao[1] for e in inimigos_visiveis) / len(inimigos_visiveis)
                  except ZeroDivisionError:
                       return None # Evita erro se lista ficar vazia entre checagem e cálculo

                  # Calcula vetor e ponto de fuga
                  fuga_x = self.posicao[0] - avg_enemy_x
                  fuga_y = self.posicao[1] - avg_enemy_y
                  # Verifica se já está longe o suficiente ou se o vetor é zero
                  if math.sqrt(fuga_x**2 + fuga_y**2) < 1.0: # Vetor muito pequeno
                      # Foge para borda aleatória se estiver em cima do centro inimigo
                      target_x = random.choice([self.arena_rect.left + 10, self.arena_rect.right - 10])
                      target_y = random.choice([self.arena_rect.top + 10, self.arena_rect.bottom - 10])
                      ponto_fuga = (target_x, target_y)
                  else:
                      fuga_norm = normalizar_vetor((fuga_x, fuga_y))
                      ponto_fuga_x = self.posicao[0] + fuga_norm[0] * 500
                      ponto_fuga_y = self.posicao[1] + fuga_norm[1] * 500
                      # Clamp
                      ponto_fuga_x = limitar_valor(ponto_fuga_x, self.arena_rect.left + 10, self.arena_rect.right - 10)
                      ponto_fuga_y = limitar_valor(ponto_fuga_y, self.arena_rect.top + 10, self.arena_rect.bottom - 10)
                      ponto_fuga = (ponto_fuga_x, ponto_fuga_y)

             # print(f"DEBUG FUGA {self.owner.id_unico}: Calculou Ponto {ponto_fuga}")
             return ponto_fuga