# simulador_engine/components/defesa_component.py
import random
from .base_component import BaseComponent

class DefesaComponent(BaseComponent):
    def __init__(self, combatente_owner, resistencias, chance_esquiva, chance_bloqueio):
        super().__init__(combatente_owner)
        # Ex: {'fisico': 5, 'fogo': 10, 'gelo': -5}
        self.resistencias = resistencias
        self.chance_esquiva = chance_esquiva # 0.0 a 1.0
        self.chance_bloqueio = chance_bloqueio # 0.0 a 1.0

    def calcular_dano_recebido(self, quantidade_bruta, tipo_dano):
        """Calcula o dano final após esquiva, bloqueio e resistências."""

        # 1. Chance de Esquiva (Evita TODO o dano)
        if random.random() < self.chance_esquiva:
            # TODO: Visualizar "Esquivou!"
            return 0 # Nenhum dano recebido

        # 2. Chance de Bloqueio (Pode reduzir o dano - ex: pela metade)
        dano_apos_bloqueio = quantidade_bruta
        if random.random() < self.chance_bloqueio:
            # TODO: Visualizar "Bloqueou!"
            dano_apos_bloqueio *= 0.5 # Exemplo: bloqueio reduz pela metade

        # 3. Aplica Resistências
        resistencia_especifica = self.resistencias.get(tipo_dano, self.resistencias.get("fisico", 0))
        # Modelo simples: Redução direta, garantindo dano mínimo 1 se passou
        dano_final = max(0, dano_apos_bloqueio - resistencia_especifica)

        # Garante dano mínimo 1 se o ataque não foi esquivado/bloqueado totalmente? Opcional.
        # if dano_apos_bloqueio > 0 and dano_final <= 0:
        #    dano_final = 1

        return round(dano_final)