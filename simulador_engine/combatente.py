# simulador_engine/combatente.py
import pygame # Para Rect
from .components.estado_component import EstadoComponent
from .components.movimento_component import MovimentoComponent
from .components.ataque_component import AtaqueComponent
from .components.defesa_component import DefesaComponent
from .components.moral_component import MoralComponent
from .components.stamina_component import StaminaComponent
# Import futuro: from .components.formation_component import FormationComponent

ID_COUNTER = 0

class Combatente:
    """Representa um único combatente na simulação, agora como um container de componentes."""

    def __init__(self, tipo_data, estilo_data, equipe, posicao_inicial, arena_rect):
        """
        Inicializa um combatente e seus componentes com base nos dados fornecidos.

        Args:
            tipo_data (dict): Dicionário com os atributos do TipoCombatente.
            estilo_data (dict): Dicionário com os atributos do EstiloLuta.
            equipe (int): ID da equipe.
            posicao_inicial (tuple): Posição (x, y) inicial.
            arena_rect (pygame.Rect): Retângulo da arena.
        """
        global ID_COUNTER
        self.id_unico = ID_COUNTER
        ID_COUNTER += 1

        self.tipo_nome = tipo_data.get("nome_tipo", "Desconhecido")
        self.estilo_nome = estilo_data.get("nome_estilo", "Desconhecido")
        self.equipe = equipe
        self.posicao_inicial = posicao_inicial # Guardada para reinicio talvez

        # --- Criação dos Componentes ---
        # Os componentes podem acessar 'self' para interagir uns com os outros (self.movimento, self.estado etc)
        try:
            # Componentes Essenciais
            self.estado = EstadoComponent(self,
                                        hp_max=float(tipo_data.get('hp_max', 1)))
            self.movimento = MovimentoComponent(self,
                                            velocidade_base=float(tipo_data.get('velocidade', 1)),
                                            tamanho_raio=int(tipo_data.get('tamanho_raio', 5)),
                                            arena_rect=arena_rect)
            self.defesa = DefesaComponent(self,
                                       resistencias=tipo_data.get('resistencias', {'fisico': 0}), # Espera dict no JSON
                                       chance_esquiva=float(tipo_data.get('chance_esquiva_base', 0.0)),
                                       chance_bloqueio=float(tipo_data.get('chance_bloqueio_base', 0.0)))
            self.ataque = AtaqueComponent(self,
                                        forca_base=float(tipo_data.get('forca_base', 1)),
                                        alcance_base=float(tipo_data.get('alcance_base', 10)),
                                        taxa_ataque_base=int(tipo_data.get('taxa_ataque', 60)),
                                        estilo_luta_data=estilo_data, # Passa o dict do estilo
                                        tipo_dano_base=tipo_data.get('tipo_dano_base', 'fisico'),
                                        chance_crit_base=float(tipo_data.get('chance_critico_base', 0.05)),
                                        mult_crit_base=float(tipo_data.get('dano_critico_multiplicador_base', 1.5)))

            # Componentes Opcionais (poderiam ser ativados por config)
            self.stamina = StaminaComponent(self,
                                          stamina_max=float(tipo_data.get('stamina_max', 100)),
                                          taxa_regen=float(tipo_data.get('taxa_regen_stamina', 1.0)), # Por tick? Ajustar!
                                          custo_mov=float(tipo_data.get('custo_stamina_movimento', 0.1)),
                                          custo_atk=float(tipo_data.get('custo_stamina_ataque', 5.0)))
            self.moral = MoralComponent(self,
                                      moral_max=float(tipo_data.get('moral_max', 100)),
                                      coragem=float(tipo_data.get('coragem', 0.5)),
                                      imune_a_medo=bool(tipo_data.get('imune_a_medo', False)) # Passa o novo atributo
                                     )

            # self.formacao = FormationComponent(self, ...) # Futuro

            self.componentes = [ # Ordem de update pode importar!
                self.estado, self.stamina, self.moral, # Primeiro atualiza estados internos
                self.ataque, # Depois decide o alvo/se ataca (define estado Atacando/Movendo/Ocioso)
                self.movimento, # Depois executa o movimento baseado no estado
                self.defesa # Defesa não tem update ativo, é chamado por receber_dano
                # Adicionar outros componentes aqui
            ]

            # Inicializa componentes que precisam de refs cruzadas (se houver)
            # for comp in self.componentes:
            #    if hasattr(comp, 'inicializar'): comp.inicializar()

        except KeyError as e:
            print(f"Erro ao criar componente para {self.tipo_nome}: Atributo ausente no JSON -> {e}")
            # Lançar exceção ou tentar continuar com valores padrão?
            raise # Falha rápido para indicar problema de config
        except Exception as e:
            print(f"Erro inesperado ao criar componentes para {self.tipo_nome}: {e}")
            raise

    def atualizar(self, todos_combatentes, motor_simulacao):
        """Atualiza todos os componentes do combatente."""
        if not self.estado.esta_vivo:
            return

        # A ordem de atualização pode ser importante!
        # Ex: Atualizar stamina/moral ANTES de decidir ação? Ou DEPOIS?
        # Ordem atual: Estado/Stamina/Moral -> Ataque (decide intenção) -> Movimento (executa)
        for componente in self.componentes:
             if hasattr(componente, 'update'):
                 componente.update(todos_combatentes, motor_simulacao)

    def morreu(self):
        """Chamado pelo EstadoComponent quando HP chega a zero."""
        # Limpa referências ou realiza ações de morte
        self.ataque.alvo_atual = None
        self.movimento.alvo_movimento = None
        # Notificar outros? (Ex: Moral de quem viu morrer) - Já feito em _checar_ambiente
        print(f"MORTE: {self.tipo_nome} {self.id_unico} (Equipe {self.equipe}) foi derrotado.")

    # Métodos de conveniência para acesso rápido (opcional)
    def get_posicao(self):
        return self.movimento.posicao

    def get_hp_ratio(self):
        if self.estado.hp_max <= 0: return 0
        return self.estado.hp_atual / self.estado.hp_max

    def get_raio(self):
        return self.movimento.tamanho_raio