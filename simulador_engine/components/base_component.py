# simulador_engine/components/base_component.py
class BaseComponent:
    """Classe base para todos os componentes de um combatente."""
    def __init__(self, combatente_owner):
        self.owner = combatente_owner # Referência ao Combatente 'pai'

    def update(self, todos_combatentes, motor_simulacao):
        """
        Método a ser implementado por subclasses.
        Executa a lógica do componente para um tick.
        """
        pass

    def inicializar(self, **kwargs):
        """
        Chamado após todos os componentes serem criados,
        para configurar dependências ou valores iniciais.
        """
        pass