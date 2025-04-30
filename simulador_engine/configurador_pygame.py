# simulador_engine/configurador_pygame.py
import pygame
import random
import os
import json # Necessário para carregar tipos e estilos

# Importa as classes do engine (CUIDADO com imports circulares se mover muito)
from .combatente import Combatente #TipoCombatente, EstiloLuta
from .tipos import TipoCombatente, EstiloLuta

# Assume que gerenciador_dados.py está um nível acima
# Isso pode ser problemático dependendo de como você executa.
# Uma solução mais robusta usaria paths relativos ou adicionaria ao sys.path
try:
    from interface_tkinter import gerenciador_dados
except ImportError:
    # Fallback se executado diretamente de dentro do simulador_engine (para testes?)
    # Ou se a estrutura de pastas estiver diferente
    print("Aviso: Não foi possível importar gerenciador_dados. Funções de carregamento podem falhar.")
    # Tentar um import relativo diferente? Ou definir stubs?
    # Por simplicidade, vamos deixar assim, mas isso precisa de atenção na execução real.
    pass


class ConfiguradorPygame:
    """Carrega configurações e cria combatentes para a simulação Pygame."""

    def __init__(self, dados_cenario):
        """
        Inicializa o Configurador com os dados do cenário específico.

        Args:
            dados_cenario (dict): Dicionário contendo a configuração da simulação
                                  (arena, equipes, membros) vindo do Tkinter.
        """
        self.config_cenario = dados_cenario
        self.tipos_combatentes_defs = self._carregar_definicoes("tipos")
        self.estilos_luta_defs = self._carregar_definicoes("estilos")
        self.arena_rect = self._configurar_arena()
        self.cores_equipes = self._configurar_cores_equipes()

        # Instancia os objetos TipoCombatente e EstiloLuta para uso interno
        self.tipos_combatentes_obj = {
            nome: TipoCombatente(**data)
            for nome, data in self.tipos_combatentes_defs.items()
        }
        self.estilos_luta_obj = {
            nome: EstiloLuta(**data)
            for nome, data in self.estilos_luta_defs.items()
        }


    def _carregar_definicoes(self, tipo):
        """Carrega definições de tipos ou estilos do JSON."""
        defs = {}
        try:
            if tipo == "tipos":
                dados_lista = gerenciador_dados.carregar_tipos_combatentes()
                chave_nome = "nome_tipo"
            elif tipo == "estilos":
                dados_lista = gerenciador_dados.carregar_estilos_luta()
                chave_nome = "nome_estilo"
            else:
                return {}

            for item_data in dados_lista:
                nome = item_data.get(chave_nome)
                if nome:
                    defs[nome] = item_data
            print(f"Carregadas {len(defs)} definições de {tipo}.")
            return defs
        except Exception as e:
             print(f"Erro crítico ao carregar definições de {tipo}: {e}")
             return {} # Retorna vazio para evitar crash total


    def _configurar_arena(self):
        """Configura o retângulo da arena com base nos dados do cenário."""
        largura = self.config_cenario.get("arena_largura", 800)
        altura = self.config_cenario.get("arena_altura", 600)
        return pygame.Rect(0, 0, largura, altura)

    def _configurar_cores_equipes(self):
        """Extrai as cores das equipes do cenário."""
        cores = {}
        for equipe_data in self.config_cenario.get('equipes', []):
            id_equipe = equipe_data.get('id_equipe')
            cor = equipe_data.get('cor', (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
            if id_equipe is not None:
                cores[id_equipe] = tuple(cor)
        return cores

    def get_arena_rect(self):
        """Retorna o Rect da arena."""
        return self.arena_rect

    def get_cor_equipe(self, id_equipe):
        """Retorna a cor de uma equipe específica."""
        return self.cores_equipes.get(id_equipe, (128, 128, 128)) # Cinza padrão

    def criar_combatentes_iniciais(self):
        """
        Cria a lista inicial de objetos Combatente com base no cenário fornecido.
        """
        combatentes = []
        if not self.config_cenario or 'equipes' not in self.config_cenario:
            print("Erro: Dados de cenário inválidos ou ausentes.")
            return []

        if not self.tipos_combatentes_obj or not self.estilos_luta_obj:
             print("Erro: Definições de tipos/estilos não carregadas corretamente.")
             return []

        largura_arena = self.arena_rect.width
        altura_arena = self.arena_rect.height

        num_equipes = len(self.config_cenario.get('equipes', []))
        largura_zona_equipe = largura_arena / max(1, num_equipes) if num_equipes > 0 else largura_arena

        Combatente.ID_COUNTER = 0 # Reseta o contador global de IDs

        for i, equipe_data in enumerate(self.config_cenario.get('equipes', [])):
            id_equipe = equipe_data.get('id_equipe')
            if id_equipe is None:
                print(f"Aviso: Equipe sem id_equipe: {equipe_data}")
                continue

            # Calcular zona de spawn para esta equipe
            zona_inicio_x = i * largura_zona_equipe
            zona_fim_x = (i + 1) * largura_zona_equipe

            for membro_data in equipe_data.get('membros', []):
                nome_tipo = membro_data.get('nome_tipo')
                quantidade = membro_data.get('quantidade', 0)
                nome_estilo = membro_data.get('estilo_luta')

                tipo_obj = self.tipos_combatentes_obj.get(nome_tipo)
                estilo_obj = self.estilos_luta_obj.get(nome_estilo)

                if not tipo_obj:
                    print(f"Aviso: Tipo Combatente '{nome_tipo}' não encontrado nas definições. Pulando.")
                    continue
                if not estilo_obj:
                    print(f"Aviso: Estilo de Luta '{nome_estilo}' não encontrado nas definições. Pulando.")
                    continue
                if quantidade <= 0:
                    continue

                print(f"Criando {quantidade} '{nome_tipo}' (Estilo: '{nome_estilo}') para Equipe {id_equipe}")

                for _ in range(quantidade):
                    # Define posição inicial aleatória DENTRO da zona da equipe
                    # Adiciona margem para não nascer colado na borda
                    margem = tipo_obj.tamanho_raio + 5
                    pos_x = random.uniform(zona_inicio_x + margem, zona_fim_x - margem)
                    pos_y = random.uniform(self.arena_rect.top + margem, self.arena_rect.bottom - margem)

                    # Garante que está dentro da arena global também (redundante mas seguro)
                    pos_x = max(self.arena_rect.left + tipo_obj.tamanho_raio, min(pos_x, self.arena_rect.right - tipo_obj.tamanho_raio))
                    pos_y = max(self.arena_rect.top + tipo_obj.tamanho_raio, min(pos_y, self.arena_rect.bottom - tipo_obj.tamanho_raio))

                    combatente = Combatente(tipo_obj, estilo_obj, id_equipe, (pos_x, pos_y), self.arena_rect)
                    combatentes.append(combatente)

        print(f"Total de {len(combatentes)} combatentes criados para a simulação.")
        return combatentes
    
    def get_config_cenario(self):
        return self.config_cenario
        
