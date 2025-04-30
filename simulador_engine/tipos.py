class TipoCombatente:
    """Representa um modelo (template) para um tipo de combatente."""
    def __init__(self, nome_tipo, hp_max, forca_base, alcance_base, velocidade,
                 taxa_ataque, tamanho_raio, resistencias, chance_esquiva_base,
                 chance_bloqueio_base, stamina_max, taxa_regen_stamina,
                 custo_stamina_movimento, custo_stamina_ataque, moral_max, coragem,
                 tipo_dano_base, chance_critico_base, dano_critico_multiplicador_base,
                 **kwargs): # Adiciona **kwargs para ignorar extras se houver
        """Inicializa com TODOS os atributos definidos no JSON."""
        self.nome_tipo = nome_tipo
        self.hp_max = float(hp_max)
        self.forca_base = float(forca_base)
        self.alcance_base = float(alcance_base)
        self.velocidade = float(velocidade)
        self.taxa_ataque = int(taxa_ataque)
        self.tamanho_raio = int(tamanho_raio)
        self.resistencias = resistencias # Já é um dict
        self.chance_esquiva_base = float(chance_esquiva_base)
        self.chance_bloqueio_base = float(chance_bloqueio_base)
        self.stamina_max = float(stamina_max)
        self.taxa_regen_stamina = float(taxa_regen_stamina)
        self.custo_stamina_movimento = float(custo_stamina_movimento)
        self.custo_stamina_ataque = float(custo_stamina_ataque)
        self.moral_max = float(moral_max)
        self.coragem = float(coragem)
        self.tipo_dano_base = tipo_dano_base
        self.chance_critico_base = float(chance_critico_base)
        self.dano_critico_multiplicador_base = float(dano_critico_multiplicador_base)
        # kwargs captura quaisquer outros campos inesperados sem causar erro

class EstiloLuta:
    """Representa um estilo de luta com seus modificadores e estratégias."""
    def __init__(self, nome_estilo, tipo_alcance, modificador_dano,
                 modificador_alcance, modificador_taxa_ataque,
                 bonus_dano_vital, estrategia_mira, tipo_dano_primario,
                 chance_critico_bonus, dano_critico_multiplicador,
                 **kwargs): # Adiciona **kwargs
        """Inicializa com TODOS os atributos definidos no JSON."""
        self.nome_estilo = nome_estilo
        self.tipo_alcance = tipo_alcance
        self.modificador_dano = float(modificador_dano)
        self.modificador_alcance = float(modificador_alcance)
        self.modificador_taxa_ataque = float(modificador_taxa_ataque)
        self.bonus_dano_vital = float(bonus_dano_vital)
        self.estrategia_mira = estrategia_mira
        self.tipo_dano_primario = tipo_dano_primario # Pode ser None
        self.chance_critico_bonus = float(chance_critico_bonus)
        self.dano_critico_multiplicador = float(dano_critico_multiplicador)
        # kwargs captura quaisquer outros campos inesperados