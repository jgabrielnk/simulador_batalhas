class MotorSimulacao:
    """Gerencia o estado e a lógica da simulação de batalha."""

    def __init__(self, combatentes_iniciais):
        """
        Inicializa o motor da simulação.

        Args:
            combatentes_iniciais (list): A lista de objetos Combatente no início.
        """
        self.combatentes = combatentes_iniciais
        self.combatentes_vivos = list(self.combatentes)
        self.rodada = 0
        self.fim_de_jogo = False
        self.equipe_vencedora = None
        self.info_ultimos_ataques = []
        self.velocidade_sim = 1.0
        self.FPS_ALVO = 60 # Para cálculos de taxas

    def atualizar(self):
        """Executa um único tick (passo) da simulação."""
        if self.fim_de_jogo: return
        self.rodada += 1
        self.info_ultimos_ataques.clear()

        combatentes_na_rodada = list(self.combatentes_vivos) # Cópia para iteração segura
        for combatente in combatentes_na_rodada:
            if combatente.estado.esta_vivo: # Checa via componente
                 # Passa refs necessárias para os updates dos componentes
                 combatente.atualizar(todos_combatentes=combatentes_na_rodada, motor_simulacao=self)
                 # Como coletar info de ataque? O componente de ataque poderia popular uma lista no motor? Ou retornar info?
                 # Simplificação: Por ora, não coletamos info detalhada de ataques para visualização

        # Remove mortos (precisa checar o estado no componente)
        self.combatentes_vivos = [c for c in self.combatentes if c.estado.esta_vivo]

        self._checar_vitoria()

    def _checar_vitoria(self):
        """Verifica se apenas uma equipe restou."""
        if not self.combatentes_vivos:
            self.fim_de_jogo = True
            self.equipe_vencedora = None # Empate? Ou ninguém?
            print(f"Fim da Simulação na rodada {self.rodada}: Todos foram derrotados!")
            return

        equipes_restantes = set(c.equipe for c in self.combatentes_vivos)

        if len(equipes_restantes) == 1:
            self.fim_de_jogo = True
            self.equipe_vencedora = equipes_restantes.pop()
            print(f"Fim da Simulação na rodada {self.rodada}: Equipe {self.equipe_vencedora} venceu!")
        elif len(equipes_restantes) == 0: # Caso raro onde todos morrem no mesmo tick
             self.fim_de_jogo = True
             self.equipe_vencedora = None
             print(f"Fim da Simulação na rodada {self.rodada}: Empate mútuo!")


    def get_combatentes_vivos(self):
        """Retorna a lista de combatentes atualmente vivos."""
        return self.combatentes_vivos

    def get_todos_combatentes(self):
        """Retorna a lista original com todos os combatentes (inclui mortos)."""
        return self.combatentes

    def get_info_ultimos_ataques(self):
        """Retorna informações sobre os ataques ocorridos no último tick."""
        return self.info_ultimos_ataques

    def terminou(self):
        """Verifica se a simulação terminou."""
        return self.fim_de_jogo

    def get_resultado(self):
        """Retorna a equipe vencedora (ou None)."""
        if self.fim_de_jogo:
            return self.equipe_vencedora
        return None