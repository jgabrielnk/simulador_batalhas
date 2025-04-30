# simulador_engine/components/stamina_component.py
from .base_component import BaseComponent

class StaminaComponent(BaseComponent):
    def __init__(self, combatente_owner, stamina_max, taxa_regen, custo_mov, custo_atk):
        super().__init__(combatente_owner)
        self.stamina_max = stamina_max
        self.stamina_atual = stamina_max
        self.taxa_regen = taxa_regen # Pontos por segundo (ou por tick)
        self.custo_movimento = custo_mov # Stamina por tick se movendo
        self.custo_ataque = custo_atk # Stamina por ataque
        self.esta_cansado = False

    def tem_stamina(self, custo):
        return self.stamina_atual >= custo

    def gastar_stamina(self, custo):
        if self.tem_stamina(custo):
            self.stamina_atual -= custo
            self.stamina_atual = max(0, self.stamina_atual)
            if self.stamina_atual == 0:
                self.esta_cansado = True
                # Notificar EstadoComponent?
                # self.owner.estado.estado_atual = "Cansado"
            return True
        return False

    def update(self, todos_combatentes, motor_simulacao):
        # Regenera stamina (simplificado - regenera a cada tick)
        # Uma taxa por segundo seria: regen_por_tick = self.taxa_regen / motor_simulacao.FPS_ALVO
        regen_por_tick = self.taxa_regen / motor_simulacao.FPS_ALVO
        
        if self.stamina_atual < self.stamina_max:
            # Regenera mais rápido se não estiver fazendo nada cansativo?
            estado = self.owner.estado.estado_atual
            fator_regen = 1.0
            if estado == "Movendo": fator_regen = 0.8 # Regenera mais devagar se movendo
            elif estado == "Atacando": fator_regen = 0.0 # Não regenera enquanto ataca

            self.stamina_atual += regen_por_tick * fator_regen # Ajuste a taxa conforme necessário
            self.stamina_atual = min(self.stamina_max, self.stamina_atual)

        # Se estava cansado mas recuperou um pouco, não está mais
        if self.esta_cansado and self.stamina_atual > self.stamina_max * 0.1: # Ex: recuperou 10%
            self.esta_cansado = False
            # self.owner.estado.estado_atual = "Ocioso" # Ou o estado anterior?

    def get_modificador_fadiga(self):
        """Retorna um multiplicador para ações baseado na fadiga (ex: 1.0 = normal, 0.5 = lento/fraco)."""
        if self.esta_cansado:
            return 0.1 # Ex: Ações pela metade da eficácia
        elif self.stamina_atual < self.stamina_max * 0.75: # Ex: Abaixo de 75%
            return 0.8
        elif self.stamina_atual < self.stamina_max * 0.5: # Ex: Abaixo de 50%
            return 0.6
        elif self.stamina_atual < self.stamina_max * 0.25: # Ex: Abaixo de 25%
            return 0.3
        return 1.0