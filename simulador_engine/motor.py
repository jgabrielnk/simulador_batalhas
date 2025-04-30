class MotorSimulacao:
    """Gerencia o estado e a lógica da simulação de batalha."""

    def __init__(self, combatentes_iniciais):
        """
        Inicializa o motor da simulação.

        Args:
            combatentes_iniciais (list): A lista de objetos Combatente no início.
        """
        self.combatentes = combatentes_iniciais
        self.combatentes_vivos = list(self.combatentes) # Cópia inicial
        self.rodada = 0
        self.fim_de_jogo = False
        self.velocidade_sim = 1.0 # Valor inicial
        self.equipe_vencedora = None
        self.info_ultimos_ataques = [] # Para visualização opcional

    def atualizar(self):
        """Executa um único tick (passo) da simulação."""
        if self.fim_de_jogo:
            return

        self.rodada += 1
        self.info_ultimos_ataques.clear() # Limpa infos da rodada anterior

        # Atualiza cada combatente vivo
        # Iterar sobre uma cópia caso a lista seja modificada (morte)
        combatentes_na_rodada = list(self.combatentes_vivos)
        for combatente in combatentes_na_rodada:
            if combatente.esta_vivo():
                 info_ataque = combatente.atualizar(combatentes_na_rodada) # Passa a lista atualizada
                 if info_ataque:
                     self.info_ultimos_ataques.append(info_ataque)

        # Remove os mortos da lista de vivos
        mortos_nesta_rodada = [c for c in self.combatentes_vivos if not c.esta_vivo()]
        self.combatentes_vivos = [c for c in self.combatentes_vivos if c.esta_vivo()]

        # Verifica condição de vitória
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