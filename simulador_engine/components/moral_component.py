# simulador_engine/components/moral_component.py
import random
from .base_component import BaseComponent
from ..utils import calcular_distancia # Import relativo

RAIO_CHEK_MORAL = 100 # Pixels para checar aliados/inimigos próximos
RECUPERACAO_MORAL_PASSIVA = 0.01 # Pequena quantidade de moral recuperada por check (ajustar!)

class MoralComponent(BaseComponent):
    def __init__(self, combatente_owner, moral_max, coragem, imune_a_medo=False):
        super().__init__(combatente_owner)
        self.moral_max = moral_max
        self.moral_atual = moral_max
        self.imune_a_medo = imune_a_medo # Guarda a informaçã
        self.coragem = coragem # 0.0 a 1.0 (modifica perda/ganho de moral)
        self.limiar_fugir = moral_max * 0.15 # Ex: Foge abaixo de 20%
        self.limiar_recuperar = moral_max * 0.4 # Ex: Recupera acima de 40%
        self.recarga_check = 0
        self.TICKS_ENTRE_CHECKS = 30 # Ex: Checa a cada 30 ticks (ajustar conforme FPS do motor)

    def registrar_dano_sofrido(self, dano, hp_atual, hp_max):
        if dano > 0 and not self.imune_a_medo: # Só perde moral se não for imune
             perda = (dano / hp_max) * self.moral_max * 0.7 # Ex: perde 50% da moral relativa ao % de vida perdido
             self.modificar_moral(-perda)

    def modificar_moral(self, quantidade):
        # Coragem reduz perda e aumenta ganho
        if quantidade < 0:
             quantidade *= (1.0 - self.coragem * 0.7) # Coragem 1.0 reduz perda em 50%
        else:
             quantidade *= (1.0 + self.coragem * 0.4) # Coragem 1.0 aumenta ganho em 20%

        self.moral_atual += quantidade
        self.moral_atual = max(0, min(self.moral_max, self.moral_atual))
        #print(f"DEBUG MORAL {self.owner.id_unico}: {self.moral_atual:.1f}/{self.moral_max}")

    def _checar_ambiente(self, todos_combatentes):
        """Verifica aliados/inimigos próximos e mortes recentes."""
        
        if self.imune_a_medo: return # Imunes não se importam com o ambiente para moral
        
        aliados_perto = 0
        inimigos_perto = 0
        aliados_mortos_recente = 0 # Precisaria de um timestamp de morte ou flag

        pos_propria = self.owner.movimento.posicao
        for outro in todos_combatentes:
            if outro == self.owner: continue
            dist = calcular_distancia(pos_propria, outro.movimento.posicao)

            if dist < RAIO_CHEK_MORAL:
                if outro.equipe == self.owner.equipe:
                     if outro.estado.esta_vivo:
                         aliados_perto += 1
                     else:
                         # Como saber se foi recente? Simplificação: conta todos mortos perto
                         aliados_mortos_recente += 1
                else:
                     if outro.estado.esta_vivo:
                          inimigos_perto += 1

        # -- Lógica de Modificação de Moral --
        # Perda por aliados mortos
        if aliados_mortos_recente > 0:
             # Perda maior se estiver em menor número?
             mod_num = 1.0 + max(0, inimigos_perto - aliados_perto) * 0.1 # Penalidade maior se outnumbered
             self.modificar_moral(-aliados_mortos_recente * (self.moral_max * 0.05) * mod_num) # Ex: 5% max moral por morte

        # Perda/Ganho por superioridade/inferioridade numérica local
        diferenca_num = aliados_perto - inimigos_perto
        fator_influencia_num = 0.01 # Quanto a diferença numérica afeta
        self.modificar_moral(diferenca_num * (self.moral_max * fator_influencia_num))


    def update(self, todos_combatentes, motor_simulacao):
        # Não atualiza moral se estiver morto
        if not self.owner.estado.esta_vivo:
            return

        self.recarga_check -= 1
        if self.recarga_check <= 0:
            # 1. Regeneração Passiva (representa calma ao longo do tempo)
            # Só regenera se não estiver ativamente perdendo moral por outras fontes?
            # Ou regenera sempre um pouco? Vamos regenerar sempre um pouquinho.
            if self.moral_atual < self.moral_max:
                 self.modificar_moral(RECUPERACAO_MORAL_PASSIVA)

            # 2. Checar Ambiente (e modificar moral com base nele)
            self._checar_ambiente(todos_combatentes)
            self.recarga_check = self.TICKS_ENTRE_CHECKS

            # 3. Avaliar Estado de Fuga/Recuperação
            estado_atual = self.owner.estado.estado_atual

            if estado_atual == "Fugindo":
                # Tenta Recuperar
                if self.moral_atual > self.limiar_recuperar:
                    # Condição adicional: não há inimigos muito próximos? (Opcional)
                    inimigos_muito_perto = False
                    for inimigo in [c for c in todos_combatentes if c.equipe != self.owner.equipe and c.estado.esta_vivo]:
                         if calcular_distancia(self.owner.movimento.posicao, inimigo.movimento.posicao) < self.owner.ataque.alcance_efetivo * 1.5: # Ex: 1.5x o alcance
                              inimigos_muito_perto = True
                              break
                    if not inimigos_muito_perto:
                        print(f"RECUPEROU MORAL: {self.owner.id_unico} parou de fugir.")
                        self.owner.estado.estado_atual = "Ocioso" # Volta ao estado normal
                    # else: print(f"DEBUG RECUPERAR: {self.owner.id_unico} moral ok, mas inimigos perto.")

            elif not self.imune_a_medo: # Só tenta fugir se não for imune
                # Tenta Fugir
                if self.moral_atual <= self.limiar_fugir:
                    # Chance de resistir com base na coragem
                    # Formula: se random > coragem^X -> Foge (coragem alta = menor chance de passar)
                    # Ex: X=0.5 => random > sqrt(coragem). Se coragem=0.81, precisa random > 0.9 (10% chance fugir)
                    # Ex: X=1.0 => random > coragem. Se coragem=0.8, precisa random > 0.8 (20% chance fugir)
                    fator_resistencia_coragem = self.coragem # Usar coragem diretamente (0 a 1)
                    if random.random() > fator_resistencia_coragem:
                        print(f"FUGINDO: {self.owner.id_unico} entrou em pânico!")
                        self.owner.estado.estado_atual = "Fugindo"
                        self.owner.ataque.alvo_atual = None # Para de mirar
                    # else: print(f"DEBUG FUGIR: {self.owner.id_unico} resistiu ao medo (Moral: {self.moral_atual:.1f})")