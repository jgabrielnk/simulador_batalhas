import math
import random
from .base_component import BaseComponent
from ..utils import calcular_distancia, normalizar_vetor

# Constante para evitar divisão por zero em raios
RAIO_MINIMO = 1
# o raio do atacante precisa ser 2.5x maior que o raio do alvo primário para causar AoE.
AOE_TRIGGER_SIZE_RATIO_THRESHOLD = 2.0
'''
  "aoe_raio_mult": 1.0,      // Raio AoE = 1x o raio do Braquiossauro (80 pixels)
  "aoe_percentual_dano_primario": 0.25, // Dano AoE = 25% do dano primário
  "aoe_mod_dano_por_razao_tamanho": 0.1 // Modificador por tamanho (opcional, pode deix
'''

class AtaqueComponent(BaseComponent):
        def __init__(self, combatente_owner, forca_base, alcance_base, taxa_ataque_base,
                     estilo_luta_data, tipo_dano_base="fisico", chance_crit_base=0.05, mult_crit_base=1.5,
                     aoe_raio_mult=0.5, aoe_perc_dano=0.25, aoe_mod_tamanho=0.1):
            super().__init__(combatente_owner)
            self.forca_base = forca_base
            self.alcance_base = alcance_base
            self.taxa_ataque_base = taxa_ataque_base # Ticks cooldown base
            self.estilo = estilo_luta_data # O dicionário do estilo
            self.tipo_dano_base = tipo_dano_base # Pode ser sobrescrito pelo estilo?
            self.chance_crit_base = chance_crit_base
            self.mult_crit_base = mult_crit_base
            self.aoe_raio_mult = aoe_raio_mult
            self.aoe_perc_dano = aoe_perc_dano
            self.aoe_mod_tamanho = aoe_mod_tamanho

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
         
        def _aplicar_dano_aoe(self, dano_bruto_primario, alvo_primario, todos_combatentes):
            """Calcula e aplica dano em área ao redor do alvo primário.
           (Versão sem checagem interna de 'pode_causar_aoe')"""
            # Verifica se os parâmetros de AoE são válidos (maiores que zero)
            if self.aoe_raio_mult <= 0 or self.aoe_perc_dano <= 0:
                return # Não faz AoE se os parâmetros forem inválidos

            # Calcula raio do AoE baseado no raio do atacante
            raio_atacante = self.owner.movimento.tamanho_raio
            raio_aoe = raio_atacante * self.aoe_raio_mult

            # Calcula dano base do AoE
            dano_aoe_bruto_base = dano_bruto_primario * self.aoe_perc_dano

            pos_impacto = alvo_primario.movimento.posicao

            #print(f"--- AOE TRIGGER (Size Ratio Met) {self.owner.id_unico} -> Raio: {raio_aoe:.1f} Dano Base: {dano_aoe_bruto_base:.1f} ---")

            # Encontra e aplica dano a alvos secundários
            for alvo_secundario in todos_combatentes:
                if (alvo_secundario != self.owner and
                    alvo_secundario != alvo_primario and
                    alvo_secundario.estado.esta_vivo and
                    alvo_secundario.equipe != self.owner.equipe):

                    distancia_do_impacto = calcular_distancia(pos_impacto, alvo_secundario.movimento.posicao)

                    if distancia_do_impacto <= raio_aoe:
                        # Calcula modificador por tamanho (atacante vs secundário)
                        raio_secundario = max(RAIO_MINIMO, alvo_secundario.movimento.tamanho_raio)
                        # Usa max(RAIO_MINIMO, raio_atacante) para evitar problemas se atacante for minúsculo
                        razao_tamanho = max(RAIO_MINIMO, raio_atacante) / raio_secundario
                        mod_dano_tamanho = max(1.0, 1.0 + (razao_tamanho - 1.0) * self.aoe_mod_tamanho)

                        dano_aoe_final_bruto = dano_aoe_bruto_base * mod_dano_tamanho
                        dano_aoe_real = alvo_secundario.estado.receber_dano(round(dano_aoe_final_bruto), self.tipo_dano_ataque)

                        #print(f"  -> AoE Hit: {alvo_secundario.id_unico} (Dist: {distancia_do_impacto:.1f}, Razão Tam: {razao_tamanho:.1f}, Mod: {mod_dano_tamanho:.2f}) Dano: {dano_aoe_real}")


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
                      # Se não encontrou alvo E não está fugindo, fica Ocioso
                      if self.owner.estado.estado_atual != "Fugindo": # Checa de novo por segurança
                           self.owner.estado.estado_atual = "Ocioso"
                      return # Sem alvo, fica ocioso

            # Verifica se pode atacar
            distancia_alvo = calcular_distancia(self.owner.movimento.posicao, self.alvo_atual.movimento.posicao)
            
            if hasattr(self.alvo_atual, 'movimento'): # Garante que o alvo tem o componente movimento
                raio_alvo = self.alvo_atual.movimento.tamanho_raio
            else:
                raio_alvo = 0 # Se o alvo não tiver raio (improvável), considera 0
                print(f"AVISO: Alvo {self.alvo_atual.id_unico} não possui componente de movimento para obter raio.")

            alcance_ajustado_para_alvo = self.alcance_efetivo + raio_alvo
            esta_no_alcance = distancia_alvo <= alcance_ajustado_para_alvo
            
            pronto_para_atacar = self.tempo_recarga_restante <= 0

            if esta_no_alcance and pronto_para_atacar:
                 # Verifica Stamina
                 custo_atk = self.owner.stamina.custo_ataque
                 if self.owner.stamina.gastar_stamina(custo_atk):
                     # --- Realiza o Ataque Primário ---
                    self.owner.estado.estado_atual = "Atacando"
                    dano_bruto_primario, foi_crit = self._calcular_dano_final(self.alvo_atual)
                    dano_realizado_primario = self.alvo_atual.estado.receber_dano(dano_bruto_primario, self.tipo_dano_ataque)
                    mod_fadiga = self.owner.stamina.get_modificador_fadiga()
                    self.tempo_recarga_restante = int(self.taxa_ataque_efetiva / max(0.1, mod_fadiga))

                    #print(f"ATAQUE PRIMÁRIO: {self.owner.id_unico} -> {self.alvo_atual.id_unico} | Dano Bruto: {dano_bruto_primario} ({'CRIT!' if foi_crit else ''}) | Dano Real: {dano_realizado_primario}")

                    # --- NOVA LÓGICA DE TRIGGER AOE ---
                    # Verifica se o atacante é significativamente maior que o alvo primário
                    raio_atacante = max(RAIO_MINIMO, self.owner.movimento.tamanho_raio)
                    raio_alvo_primario = max(RAIO_MINIMO, self.alvo_atual.movimento.tamanho_raio)
                    razao_tamanho_primario = raio_atacante / raio_alvo_primario
                    # print(f"DEBUG AOE Check: Atacante {self.owner.id_unico} (R:{raio_atacante}) -> Alvo {self.alvo_atual.id_unico} (R:{raio_alvo_primario}) | Razão: {razao_tamanho_primario:.2f} | Limiar: {AOE_TRIGGER_SIZE_RATIO_THRESHOLD}")
                    # print(f"DEBUG AOE Check: Params Atacante: RaioMult={self.aoe_raio_mult}, PercDano={self.aoe_perc_dano}")

                    if razao_tamanho_primario >= AOE_TRIGGER_SIZE_RATIO_THRESHOLD:
                        #print(f"DEBUG AOE: Limiar ATINGIDO para {self.owner.id_unico}. Tentando aplicar AoE...")
                       # Verifica se os parâmetros permitem AoE
                        if self.aoe_raio_mult > 0 and self.aoe_perc_dano > 0:
                            self._aplicar_dano_aoe(dano_bruto_primario, self.alvo_atual, todos_combatentes)
                        #else:
                             #print(f"DEBUG AOE: Limiar atingido, mas parâmetros AoE (RaioMult/PercDano) são zero ou menores para {self.owner.id_unico}. AoE não aplicado.")
                    #else:
                        #print(f"DEBUG AOE: Limiar NÃO ATINGIDO para {self.owner.id_unico}.")
                        
                 else:
                     # Sem stamina para atacar
                     self.owner.estado.estado_atual = "Cansado"
                     # TODO: Visualizar "Sem fôlego!"
                     # print(f"SEM STAMINA: {self.owner.id_unico} não pode atacar.")

            elif esta_no_alcance and not pronto_para_atacar:
                 # Em alcance, mas cooldown
                 if self.owner.estado.estado_atual != "Fugindo": # Só muda se não estiver fugindo
                      self.owner.estado.estado_atual = "Ocioso" # Define estado OCIOSO
            elif not esta_no_alcance:
                 # Fora de alcance
                 if self.owner.estado.estado_atual != "Fugindo": # Só muda se não estiver fugindo
                      self.owner.estado.estado_atual = "Movendo" # Define estado MOVENDO

            # Se não está atacando, reseta o estado para Ocioso ou Movendo (será definido pelo movimento)
            # if self.owner.estado.estado_atual == "Atacando": # Se acabou de atacar
            #    if esta_no_alcance: self.owner.estado.estado_atual = "Ocioso"
            #    else: self.owner.estado.estado_atual = "Movendo"
            # A lógica acima é tratada pela ordem de update no Combatente principal