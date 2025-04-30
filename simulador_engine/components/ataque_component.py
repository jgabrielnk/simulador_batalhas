import math
import random
from .base_component import BaseComponent
from ..utils import calcular_distancia, normalizar_vetor

class AtaqueComponent(BaseComponent):
        def __init__(self, combatente_owner, forca_base, alcance_base, taxa_ataque_base,
                     estilo_luta_data, tipo_dano_base="fisico", chance_crit_base=0.05, mult_crit_base=1.5):
            super().__init__(combatente_owner)
            self.forca_base = forca_base
            self.alcance_base = alcance_base
            self.taxa_ataque_base = taxa_ataque_base # Ticks cooldown base
            self.estilo = estilo_luta_data # O dicionário do estilo
            self.tipo_dano_base = tipo_dano_base # Pode ser sobrescrito pelo estilo?
            self.chance_crit_base = chance_crit_base
            self.mult_crit_base = mult_crit_base

            # Atributos Calculados (com base no estilo)
            self.alcance_efetivo = self.alcance_base * self.estilo.get('modificador_alcance', 1.0)
            self.taxa_ataque_efetiva = int(self.taxa_ataque_base * self.estilo.get('modificador_taxa_ataque', 1.0))
            self.tipo_dano_ataque = self.estilo.get('tipo_dano_primario', self.tipo_dano_base) # Estilo pode definir o tipo
            self.chance_crit_final = self.chance_crit_base + self.estilo.get('chance_critico_bonus', 0.0)
            self.mult_crit_final = self.mult_crit_base * self.estilo.get('dano_critico_multiplicador', 1.0)

            self.tempo_recarga_restante = 0
            self.alvo_atual = None

        def encontrar_alvo(self, todos_combatentes):
             """Encontra alvo baseado na estratégia do estilo."""
             inimigos = [c for c in todos_combatentes if c.estado.esta_vivo and c.equipe != self.owner.equipe]
             if not inimigos:
                 self.alvo_atual = None
                 return

             estrategia = self.estilo.get("estrategia_mira", "mais_proximo")
             pos_propria = self.owner.movimento.posicao
             melhor_alvo = None

             if estrategia == "hp_mais_baixo":
                  melhor_alvo = min(inimigos, key=lambda inimigo: inimigo.estado.hp_atual, default=None)
             else: # mais_proximo
                  melhor_alvo = min(inimigos, key=lambda inimigo: calcular_distancia(pos_propria, inimigo.movimento.posicao), default=None)

             self.alvo_atual = melhor_alvo


        def _calcular_modificador_angulo(self, alvo):
             """Calcula bônus/penalidade baseado no ângulo de ataque (Facing/Flanking)."""
             if not hasattr(alvo, 'movimento') or not hasattr(self.owner, 'movimento'):
                  return 1.0 # Sem componente de movimento, sem bônus

             # Vetor da direção do ATACANTE
             dir_atacante = self.owner.movimento.direcao
             # Vetor da direção do ALVO
             dir_alvo = alvo.movimento.direcao
             # Vetor DO ATACANTE PARA O ALVO
             vetor_para_alvo = normalizar_vetor((alvo.movimento.posicao[0] - self.owner.movimento.posicao[0],
                                               alvo.movimento.posicao[1] - self.owner.movimento.posicao[1]))

             # Produto escalar entre direção do alvo e vetor para o alvo
             # cos(theta) = A dot B / (|A|*|B|) -> como são normalizados, é só A dot B
             # Valor > 0: Atacante está mais ou menos na frente do alvo
             # Valor < 0: Atacante está mais ou menos atrás do alvo
             # Valor ~= 0: Atacante está pelo lado
             dot_product = dir_alvo[0] * vetor_para_alvo[0] + dir_alvo[1] * vetor_para_alvo[1]

             # Define bônus/penalidades (AJUSTAR ESTES VALORES)
             if dot_product < -0.7: # Bem atrás (ângulo > 135 graus aprox)
                 #print(f"DEBUG FLANK: {self.owner.id_unico} atacou {alvo.id_unico} por trás!")
                 return 1.5 # Bônus de 50% no dano
             elif dot_product < 0.1: # Pelo lado (ângulo entre 85 e 135 graus aprox)
                 #print(f"DEBUG FLANK: {self.owner.id_unico} atacou {alvo.id_unico} pelo lado!")
                 return 1.2 # Bônus de 20%
             # elif dot_product > 0.8: # Bem de frente
             #    return 0.9 # Penalidade pequena se atacar de frente? Opcional
             else: # De frente
                 return 1.0 # Sem modificador

        def _calcular_dano_final(self, alvo):
             """Calcula o dano bruto, aplicando estilo, fadiga, ângulo e crítico."""
             # Modificador de Fadiga
             mod_fadiga = self.owner.stamina.get_modificador_fadiga()

             # Dano base ajustado pelo estilo e fadiga
             dano_base_calc = (self.forca_base * self.estilo.get('modificador_dano', 1.0) +
                              self.estilo.get('bonus_dano_vital', 0)) * mod_fadiga

             # Modificador de Ângulo (Flanqueamento)
             mod_angulo = self._calcular_modificador_angulo(alvo)
             dano_com_angulo = dano_base_calc * mod_angulo

             # Chance de Crítico
             dano_final = dano_com_angulo
             is_crit = False
             if random.random() < self.chance_crit_final:
                 is_crit = True
                 dano_final *= self.mult_crit_final
                 # TODO: Visualizar "CRÍTICO!"

             # Adicionar pequena variação aleatória final?
             dano_final *= random.uniform(0.95, 1.05)

             return round(dano_final), is_crit


        def update(self, todos_combatentes, motor_simulacao):
            if not self.owner.estado.esta_vivo or self.owner.estado.estado_atual == "Fugindo":
                 self.alvo_atual = None # Não ataca se morto ou fugindo
                 return

            # Atualiza cooldown
            if self.tempo_recarga_restante > 0:
                self.tempo_recarga_restante -= 1

            # Encontra alvo se necessário
            if not self.alvo_atual or not self.alvo_atual.estado.esta_vivo:
                 self.encontrar_alvo(todos_combatentes)
                 if not self.alvo_atual:
                      self.owner.estado.estado_atual = "Ocioso"
                      return # Sem alvo, fica ocioso

            # Verifica se pode atacar
            distancia_alvo = calcular_distancia(self.owner.movimento.posicao, self.alvo_atual.movimento.posicao)
            esta_no_alcance = distancia_alvo <= self.alcance_efetivo
            pronto_para_atacar = self.tempo_recarga_restante <= 0

            if esta_no_alcance and pronto_para_atacar:
                 # Verifica Stamina
                 custo_atk = self.owner.stamina.custo_ataque
                 if self.owner.stamina.gastar_stamina(custo_atk):
                     # ---- Realiza o Ataque ----
                     self.owner.estado.estado_atual = "Atacando" # Define estado

                     dano_bruto, foi_crit = self._calcular_dano_final(self.alvo_atual)

                     # Aplica o dano no alvo (que usará sua DefesaComponent)
                     dano_realizado = self.alvo_atual.estado.receber_dano(dano_bruto, self.tipo_dano_ataque)

                     # Reinicia cooldown
                     mod_fadiga = self.owner.stamina.get_modificador_fadiga() # Ataques mais lentos se cansado
                     self.tempo_recarga_restante = int(self.taxa_ataque_efetiva / mod_fadiga)

                     # TODO: Visualizar o ataque (linha, efeito)
                     # print(f"ATAQUE: {self.owner.id_unico} -> {self.alvo_atual.id_unico} | Dano Bruto: {dano_bruto} ({'CRIT!' if foi_crit else ''}) | Dano Real: {dano_realizado} | Tipo: {self.tipo_dano_ataque}")

                 else:
                     # Sem stamina para atacar
                     self.owner.estado.estado_atual = "Cansado"
                     # TODO: Visualizar "Sem fôlego!"
                     # print(f"SEM STAMINA: {self.owner.id_unico} não pode atacar.")

            elif esta_no_alcance and not pronto_para_atacar:
                  # Em alcance, mas esperando cooldown
                  self.owner.estado.estado_atual = "Ocioso" # Ou "EsperandoCooldown"?
            elif not esta_no_alcance:
                  # Fora de alcance, precisa mover
                  self.owner.estado.estado_atual = "Movendo"

            # Se não está atacando, reseta o estado para Ocioso ou Movendo (será definido pelo movimento)
            # if self.owner.estado.estado_atual == "Atacando": # Se acabou de atacar
            #    if esta_no_alcance: self.owner.estado.estado_atual = "Ocioso"
            #    else: self.owner.estado.estado_atual = "Movendo"
            # A lógica acima é tratada pela ordem de update no Combatente principal