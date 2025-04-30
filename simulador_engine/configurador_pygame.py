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
# Importa gerenciador de dados para carregar JSONs
try:
    from interface_tkinter import gerenciador_dados
except ImportError:
    print("Aviso: Não foi possível importar gerenciador_dados.")
    # Definir funções stub se necessário para testes isolados
    class MockGerenciador:
        def carregar_tipos_combatentes(self): return []
        def carregar_estilos_luta(self): return []
    gerenciador_dados = MockGerenciador()


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
        '''
        # Instancia os objetos TipoCombatente e EstiloLuta para uso interno
        self.tipos_combatentes_obj = {
            nome: TipoCombatente(**data)
            for nome, data in self.tipos_combatentes_defs.items()
        }
        self.estilos_luta_obj = {
            nome: EstiloLuta(**data)
            for nome, data in self.estilos_luta_defs.items()
        }
        '''
        
    def _carregar_definicoes(self, tipo):
        """Carrega definições de tipos ou estilos do JSON."""
        defs = {}
        dados_lista = []
        chave_nome = None
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
                    defs[nome] = item_data # Guarda o dict inteiro
            print(f"Carregadas {len(defs)} definições de {tipo}.")
            return defs
        except Exception as e:
             print(f"Erro crítico ao carregar definições de {tipo}: {e}")
             return {}


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
        (Versão Corrigida)
        """
        combatentes = []
        if not self.config_cenario or 'equipes' not in self.config_cenario:
            print("Erro: Dados de cenário inválidos ou ausentes.")
            return []

        # --- CORREÇÃO AQUI ---
        # Verifica se os dicionários de definições foram carregados
        if not self.tipos_combatentes_defs or not self.estilos_luta_defs:
             print("Erro: Definições de tipos/estilos não carregadas corretamente (dicionários vazios).")
             print(f"Tipos carregados: {len(self.tipos_combatentes_defs)}") # Debug extra
             print(f"Estilos carregados: {len(self.estilos_luta_defs)}")   # Debug extra
             return []
        # --- FIM DA CORREÇÃO ---

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
            # (A lógica de cálculo da zona precisa da pos_x, pos_y definida dentro do loop de quantidade)
            zona_inicio_x = i * largura_zona_equipe
            zona_fim_x = (i + 1) * largura_zona_equipe

            for membro_data in equipe_data.get('membros', []):
                nome_tipo = membro_data.get('nome_tipo')
                quantidade = membro_data.get('quantidade', 0)
                nome_estilo = membro_data.get('estilo_luta')

                # Pega os DICIONÁRIOS de definição - Está CORRETO
                tipo_data = self.tipos_combatentes_defs.get(nome_tipo)
                estilo_data = self.estilos_luta_defs.get(nome_estilo)

                if not tipo_data:
                    print(f"Aviso: Definição Tipo '{nome_tipo}' não encontrada. Pulando.")
                    continue
                if not estilo_data:
                    print(f"Aviso: Definição Estilo '{nome_estilo}' não encontrada. Pulando.")
                    continue
                if quantidade <= 0:
                    continue

                print(f"Criando {quantidade} '{nome_tipo}' (Estilo: '{nome_estilo}') para Equipe {id_equipe}")

                for _ in range(quantidade):
                    # Calcular pos_x, pos_y aleatórios na zona AQUI
                    tamanho_raio_aprox = int(tipo_data.get('tamanho_raio', 5))
                    margem = tamanho_raio_aprox + 5
                    # Garante que a zona tenha alguma largura/altura mínima para a margem
                    min_x_zona = zona_inicio_x + margem
                    max_x_zona = zona_fim_x - margem
                    min_y_zona = self.arena_rect.top + margem
                    max_y_zona = self.arena_rect.bottom - margem

                    # Se a zona for muito pequena, coloca no centro dela
                    if min_x_zona >= max_x_zona:
                        pos_x = (zona_inicio_x + zona_fim_x) / 2
                    else:
                        pos_x = random.uniform(min_x_zona, max_x_zona)

                    if min_y_zona >= max_y_zona:
                         pos_y = (self.arena_rect.top + self.arena_rect.bottom) / 2
                    else:
                         pos_y = random.uniform(min_y_zona, max_y_zona)

                    # Clamp final para garantir que está dentro da arena global
                    pos_x = max(self.arena_rect.left + tamanho_raio_aprox, min(pos_x, self.arena_rect.right - tamanho_raio_aprox))
                    pos_y = max(self.arena_rect.top + tamanho_raio_aprox, min(pos_y, self.arena_rect.bottom - tamanho_raio_aprox))

                    # Cria o combatente passando os dicionários de dados - Está CORRETO
                    try:
                        combatente = Combatente(tipo_data, estilo_data, id_equipe, (pos_x, pos_y), self.arena_rect)
                        combatentes.append(combatente)
                    except Exception as e:
                         print(f"!!!! Erro ao INSTANCIAR combatente '{nome_tipo}' da equipe {id_equipe}: {e}")
                         print("!!!! Verifique se todos os atributos necessários estão no JSON e se os componentes estão corretos.")
                         import traceback
                         traceback.print_exc() # Imprime o traceback completo para ajudar a depurar
                         # return [] # Parar é mais seguro em caso de erro aqui

        print(f"Total de {len(combatentes)} combatentes criados para a simulação.")
        return combatentes
    
    def get_config_cenario(self):
        return self.config_cenario
        
