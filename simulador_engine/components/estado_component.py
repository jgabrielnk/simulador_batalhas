# simulador_engine/components/estado_component.py
from .base_component import BaseComponent

class EstadoComponent(BaseComponent):
    def __init__(self, combatente_owner, hp_max):
        super().__init__(combatente_owner)
        self.hp_max = hp_max
        self.hp_atual = hp_max
        self._esta_vivo = True
        self.estado_atual = "Ocioso" # Ex: Ocioso, Movendo, Atacando, Fugindo, Cansado

    @property
    def esta_vivo(self):
        return self._esta_vivo

    def receber_dano(self, quantidade, tipo_dano="fisico"):
        if not self.esta_vivo:
            return 0

        # Pede ao componente de defesa para calcular a redução
        dano_reduzido = self.owner.defesa.calcular_dano_recebido(quantidade, tipo_dano)

        self.hp_atual -= dano_reduzido
        self.hp_atual = max(0, self.hp_atual) # Não deixa ficar negativo

        # Notifica outros componentes (ex: Moral) sobre o dano recebido
        self.owner.moral.registrar_dano_sofrido(dano_reduzido, self.hp_atual, self.hp_max)

        if self.hp_atual <= 0:
            self._esta_vivo = False
            self.estado_atual = "Derrotado"
            self.owner.morreu() # Notifica o combatente principal

        return dano_reduzido # Retorna quanto dano realmente passou

    def update(self, todos_combatentes, motor_simulacao):
        # Poderia ter lógica aqui, como regeneração passiva de HP
        pass