# interface_tkinter/gerenciador_dados.py
import json
import os
import random

CONFIG_DIR = "config"
TIPOS_FILE = os.path.join(CONFIG_DIR, "tipos_combatentes.json")
ESTILOS_FILE = os.path.join(CONFIG_DIR, "estilos_luta.json")
SIMULACOES_FILE = os.path.join(CONFIG_DIR, "simulacoes_salvas.json")

# Garante que o diretório de configuração exista
os.makedirs(CONFIG_DIR, exist_ok=True)

def _carregar_json(filepath, default_value=[]):
    """Carrega dados de um arquivo JSON, retornando default se não existir ou erro."""
    if not os.path.exists(filepath):
        return default_value
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Erro ao carregar {filepath}: {e}")
        return default_value

def _salvar_json(filepath, data):
    """Salva dados em um arquivo JSON."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Erro ao salvar {filepath}: {e}")
        return False

# --- Funções para Tipos de Combatentes ---
def carregar_tipos_combatentes():
    """Retorna a lista de dicionários de tipos de combatentes."""
    return _carregar_json(TIPOS_FILE)

def salvar_tipos_combatentes(tipos):
    """Salva a lista de tipos de combatentes."""
    return _salvar_json(TIPOS_FILE, tipos)

def obter_nomes_tipos_combatentes():
    """Retorna uma lista apenas com os nomes dos tipos."""
    tipos = carregar_tipos_combatentes()
    return [t.get("nome_tipo", "Nome Inválido") for t in tipos]

def obter_tipo_por_nome(nome):
    """Busca um tipo pelo nome."""
    tipos = carregar_tipos_combatentes()
    for t in tipos:
        if t.get("nome_tipo") == nome:
            return t
    return None

def adicionar_ou_atualizar_tipo(novo_tipo_data, nome_original=None):
    """Adiciona um novo tipo ou atualiza um existente."""
    tipos = carregar_tipos_combatentes()
    encontrado = False
    if nome_original: # Atualizando
        for i, tipo in enumerate(tipos):
            if tipo.get("nome_tipo") == nome_original:
                tipos[i] = novo_tipo_data
                encontrado = True
                break
    if not encontrado: # Adicionando novo ou atualizando sem nome original (usa novo nome)
         # Verifica se já existe com o novo nome para evitar duplicatas ao renomear
         indice_existente = -1
         for i, tipo in enumerate(tipos):
             if tipo.get("nome_tipo") == novo_tipo_data.get("nome_tipo"):
                 indice_existente = i
                 break
         if indice_existente != -1:
              tipos[indice_existente] = novo_tipo_data
         else:
              tipos.append(novo_tipo_data)

    return salvar_tipos_combatentes(tipos)


# --- Funções para Estilos de Luta ---
def carregar_estilos_luta():
    """Retorna a lista de dicionários de estilos de luta."""
    return _carregar_json(ESTILOS_FILE)

def salvar_estilos_luta(estilos):
    """Salva a lista de estilos de luta."""
    return _salvar_json(ESTILOS_FILE, estilos)

def obter_nomes_estilos_luta():
    """Retorna uma lista apenas com os nomes dos estilos."""
    estilos = carregar_estilos_luta()
    return [e.get("nome_estilo", "Nome Inválido") for e in estilos]

def obter_estilo_por_nome(nome):
    """Busca um estilo pelo nome."""
    estilos = carregar_estilos_luta()
    for e in estilos:
        if e.get("nome_estilo") == nome:
            return e
    return None

def adicionar_ou_atualizar_estilo(novo_estilo_data, nome_original=None):
    """Adiciona um novo estilo ou atualiza um existente."""
    estilos = carregar_estilos_luta()
    encontrado = False
    if nome_original: # Atualizando
        for i, estilo in enumerate(estilos):
            if estilo.get("nome_estilo") == nome_original:
                estilos[i] = novo_estilo_data
                encontrado = True
                break
    if not encontrado: # Adicionando novo ou atualizando sem nome original
        indice_existente = -1
        for i, estilo in enumerate(estilos):
             if estilo.get("nome_estilo") == novo_estilo_data.get("nome_estilo"):
                 indice_existente = i
                 break
        if indice_existente != -1:
             estilos[indice_existente] = novo_estilo_data
        else:
             estilos.append(novo_estilo_data)

    return salvar_estilos_luta(estilos)

# --- Funções para Simulações Salvas ---
def carregar_simulacoes_salvas():
    """Retorna a lista de dicionários de cenários salvos."""
    return _carregar_json(SIMULACOES_FILE)

def salvar_simulacoes(simulacoes):
    """Salva a lista de cenários."""
    return _salvar_json(SIMULACOES_FILE, simulacoes)

def obter_nomes_simulacoes():
    """Retorna uma lista com os nomes das simulações salvas."""
    simulacoes = carregar_simulacoes_salvas()
    return [s.get("nome_simulacao", "Nome Inválido") for s in simulacoes]

def obter_simulacao_por_nome(nome):
    """Busca um cenário pelo nome."""
    simulacoes = carregar_simulacoes_salvas()
    for s in simulacoes:
        if s.get("nome_simulacao") == nome:
            return s
    return None

def adicionar_ou_atualizar_simulacao(nova_simulacao_data, nome_original=None):
    """Adiciona ou atualiza um cenário."""
    simulacoes = carregar_simulacoes_salvas()
    encontrado = False
    if nome_original: # Atualizando
        for i, sim in enumerate(simulacoes):
            if sim.get("nome_simulacao") == nome_original:
                simulacoes[i] = nova_simulacao_data
                encontrado = True
                break
    if not encontrado: # Adicionando novo ou atualizando sem nome original
        indice_existente = -1
        for i, sim in enumerate(simulacoes):
            if sim.get("nome_simulacao") == nova_simulacao_data.get("nome_simulacao"):
                 indice_existente = i
                 break
        if indice_existente != -1:
            simulacoes[indice_existente] = nova_simulacao_data
        else:
            simulacoes.append(nova_simulacao_data)

    return salvar_simulacoes(simulacoes)

def deletar_simulacao(nome_simulacao):
    """Deleta uma simulação pelo nome."""
    simulacoes = carregar_simulacoes_salvas()
    simulacoes_filtradas = [s for s in simulacoes if s.get("nome_simulacao") != nome_simulacao]
    if len(simulacoes_filtradas) < len(simulacoes):
        return salvar_simulacoes(simulacoes_filtradas)
    return False # Não encontrou ou erro ao salvar

def deletar_objeto(nome_objeto, tipo_objeto):
    """Deleta um tipo de combatente ou estilo pelo nome."""
    if tipo_objeto == "Combatente":
        objetos = carregar_tipos_combatentes()
        chave_nome = "nome_tipo"
        funcao_salvar = salvar_tipos_combatentes
    elif tipo_objeto == "Estilo":
        objetos = carregar_estilos_luta()
        chave_nome = "nome_estilo"
        funcao_salvar = salvar_estilos_luta
    else:
        return False

    objetos_filtrados = [o for o in objetos if o.get(chave_nome) != nome_objeto]
    if len(objetos_filtrados) < len(objetos):
        return funcao_salvar(objetos_filtrados)
    return False

# --- Valores Padrão para Novos Objetos ---
def get_atributos_tipo_combatente():
    """Retorna lista completa de atributos configuráveis."""
    return [
        "nome_tipo", "hp_max", "forca_base", "alcance_base", "velocidade",
        "taxa_ataque", "tamanho_raio",
        "resistencias",
        "chance_esquiva_base", "chance_bloqueio_base",
        "stamina_max", "taxa_regen_stamina", "custo_stamina_movimento", "custo_stamina_ataque",
        "moral_max", "coragem", "imune_a_medo", # Adicionado aqui
        "tipo_dano_base",
        "chance_critico_base", "dano_critico_multiplicador_base"
    ]

def get_valores_padrao_tipo_combatente():
     """Retorna dicionário com valores padrão para todos os atributos."""
     return {
        "nome_tipo": "Novo Combatente", "hp_max": 100, "forca_base": 10.0,
        "alcance_base": 30.0, "velocidade": 3.0, "taxa_ataque": 60, "tamanho_raio": 10,
        "resistencias": {"contundente": 0, "perfurante": 0, "cortante": 0, "fogo": 0, "gelo": 0, "acido": 0, "electrico": 0, "explosivo": 0},
        "chance_esquiva_base": 0.05, "chance_bloqueio_base": 0.05,
        "stamina_max": 100.0, "taxa_regen_stamina": 1.0, "custo_stamina_movimento": 0.1, "custo_stamina_ataque": 5.0,
        "moral_max": 100.0, "coragem": 0.5, "imune_a_medo": False, # Adicionado aqui
        "tipo_dano_base": "fisico",
        "chance_critico_base": 0.05, "dano_critico_multiplicador_base": 1.5
     }
     
def get_atributos_estilo_luta():
    """Retorna lista completa de atributos configuráveis."""
    return [
        "nome_estilo", "tipo_alcance", "modificador_dano", "modificador_alcance",
        "modificador_taxa_ataque", "bonus_dano_vital", "estrategia_mira",
        "tipo_dano_primario", # Pode ser string ou null/None
        "chance_critico_bonus", "dano_critico_multiplicador"
        ]

def get_valores_padrao_estilo_luta():
     """Retorna dicionário com valores padrão para todos os atributos."""
     return {
        "nome_estilo": "Novo Estilo", "tipo_alcance": "corpo_a_corpo",
        "modificador_dano": 1.0, "modificador_alcance": 1.0, "modificador_taxa_ataque": 1.0,
        "bonus_dano_vital": 0.0, "estrategia_mira": "mais_proximo",
        "tipo_dano_primario": None, # Default é usar o do combatente
        "chance_critico_bonus": 0.0, "dano_critico_multiplicador": 1.0
     }
     
def get_tipos_alcance_validos():
    return ["corpo_a_corpo", "longo_alcance"]

def get_tipos_dano_validos():
    return ["contundente", "perfurante", "cortante", "fogo", "gelo", "acido", "electrico", "explosivo", ""] 

def get_estrategias_mira_validas():
    return ["mais_proximo", "hp_mais_baixo"]