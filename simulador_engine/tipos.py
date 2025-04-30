
class TipoCombatente:
    """Representa um modelo (template) para um tipo de combatente."""
    def __init__(self, nome_tipo, hp_max, forca_base, resistencia,
                 alcance_base, velocidade, taxa_ataque, tamanho_raio):
        self.nome_tipo = nome_tipo
        self.hp_max = float(hp_max) # Garante float
        self.forca_base = float(forca_base)
        self.resistencia = float(resistencia)
        self.alcance_base = float(alcance_base)
        self.velocidade = float(velocidade)
        self.taxa_ataque = int(taxa_ataque)
        self.tamanho_raio = int(tamanho_raio)

class EstiloLuta:
    """Representa um estilo de luta com seus modificadores e estratégias."""
    def __init__(self, nome_estilo, tipo_alcance, modificador_dano,
                 modificador_alcance, modificador_taxa_ataque,
                 bonus_dano_vital, estrategia_mira):
        self.nome_estilo = nome_estilo
        self.tipo_alcance = tipo_alcance
        self.modificador_dano = float(modificador_dano)
        self.modificador_alcance = float(modificador_alcance)
        self.modificador_taxa_ataque = float(modificador_taxa_ataque)
        self.bonus_dano_vital = float(bonus_dano_vital)
        self.estrategia_mira = estrategia_mira