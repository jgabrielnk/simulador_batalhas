# interface_tkinter/paginas.py
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import json
import random
from . import gerenciador_dados as gd # gd para abreviar

# --- Constantes ---
PAD_X = 5
PAD_Y = 5
LARGURA_ENTRY = 40

# --- Classe Base para Páginas ---
class PaginaBase(tk.Frame):
    """Classe base para todas as páginas da aplicação."""
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app_controller = app_controller # Referência à aplicação principal
        self.parent = parent

    def _criar_botao_voltar(self, pagina_anterior_cls, **kwargs):
        """Cria um botão 'Voltar' padrão, passando kwargs para a página anterior."""
        tk.Button(self, text="< Voltar",
              command=lambda cls=pagina_anterior_cls, k=kwargs: self.app_controller.mostrar_pagina(cls, **k)
             ).pack(side=tk.BOTTOM, anchor="sw", padx=PAD_X, pady=PAD_Y)

    def _validar_entry_numero(self, P, tipo_num=float):
        """Valida se a entrada é um número (float ou int)."""
        if P == "": return True # Permite apagar
        try:
            tipo_num(P)
            return True
        except ValueError:
            return False

    def _get_entry_value(self, entry, tipo_num=str):
        """Obtém o valor de um Entry, convertendo e tratando erro."""
        val_str = entry.get()
        if tipo_num == str:
             return val_str
        if not val_str: # Se vazio, retorna 0 para números
             if tipo_num == int or tipo_num == float:
                 return tipo_num(0)
             else:
                 return None # Ou lança erro?
        try:
             return tipo_num(val_str)
        except ValueError:
             messagebox.showerror("Erro de Valor", f"Valor inválido: '{val_str}'. Esperado um {tipo_num.__name__}.")
             return None # Indica erro

# --- Página Menu Principal ---
class PaginaMenuPrincipal(PaginaBase):
    def __init__(self, parent, app_controller):
        super().__init__(parent, app_controller)

        tk.Label(self, text="Simulador de Batalha", font=("Arial", 16)).pack(pady=20)

        tk.Button(self, text="Criar Nova Simulação", width=25,
                  command=lambda: self.app_controller.mostrar_pagina(PaginaCriarSimulacao)).pack(pady=PAD_Y)
        tk.Button(self, text="Ver Simulações Salvas", width=25,
                  command=lambda: self.app_controller.mostrar_pagina(PaginaSimulacoesCriadas)).pack(pady=PAD_Y)
        tk.Button(self, text="Criar Novo Objeto", width=25,
                  command=lambda: self.app_controller.mostrar_pagina(PaginaEscolherTipoObjeto, modo='criar')).pack(pady=PAD_Y)
        tk.Button(self, text="Editar Objeto Existente", width=25,
                  command=lambda: self.app_controller.mostrar_pagina(PaginaEscolherTipoObjeto, modo='editar')).pack(pady=PAD_Y)
        tk.Button(self, text="Sair", width=25, command=self.app_controller.sair).pack(pady=PAD_Y, side=tk.BOTTOM)

# --- Página Escolher Tipo de Objeto (para Criar/Editar) ---
class PaginaEscolherTipoObjeto(PaginaBase):
    def __init__(self, parent, app_controller, modo='criar'):
        super().__init__(parent, app_controller)
        self.modo = modo # 'criar' ou 'editar'
        titulo = "Criar Novo Objeto" if modo == 'criar' else "Editar Objeto Existente"
        tk.Label(self, text=titulo, font=("Arial", 14)).pack(pady=10)

        tk.Label(self, text="Selecione o tipo de objeto:").pack(pady=PAD_Y)

        self.tipo_var = tk.StringVar(value="Combatente")
        ttk.Radiobutton(self, text="Combatente", variable=self.tipo_var, value="Combatente").pack(anchor="w", padx=20)
        ttk.Radiobutton(self, text="Estilo de Luta", variable=self.tipo_var, value="Estilo").pack(anchor="w", padx=20)

        if self.modo == 'criar':
            tk.Button(self, text="Prosseguir >", command=self.prosseguir_criar).pack(pady=20)
        else: # modo editar
             tk.Button(self, text="Listar Objetos >", command=self.listar_para_editar).pack(pady=20)

        self._criar_botao_voltar(PaginaMenuPrincipal)

    def prosseguir_criar(self):
        tipo = self.tipo_var.get()
        self.app_controller.mostrar_pagina(PaginaEditarDetalhesObjeto,
                                           tipo_objeto=tipo,
                                           dados_objeto=None, # Indica criação
                                           nome_original=None)

    def listar_para_editar(self):
         tipo = self.tipo_var.get()
         self.app_controller.mostrar_pagina(PaginaListarEditarObjeto, tipo_objeto=tipo)


# --- Página Listar/Editar Objetos ---
class PaginaListarEditarObjeto(PaginaBase):
    def __init__(self, parent, app_controller, tipo_objeto):
        super().__init__(parent, app_controller)
        self.tipo_objeto = tipo_objeto # "Combatente" ou "Estilo"

        tk.Label(self, text=f"Editar {tipo_objeto}", font=("Arial", 14)).pack(pady=10)

        frame_lista = tk.Frame(self)
        frame_lista.pack(pady=PAD_Y, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame_lista)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(frame_lista, yscrollcommand=scrollbar.set, width=50, height=15)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        self.carregar_lista()

        frame_botoes = tk.Frame(self)
        frame_botoes.pack(pady=PAD_Y)

        tk.Button(frame_botoes, text="Editar Selecionado", command=self.editar_selecionado).pack(side=tk.LEFT, padx=PAD_X)
        tk.Button(frame_botoes, text="Deletar Selecionado", command=self.deletar_selecionado).pack(side=tk.LEFT, padx=PAD_X)

        self._criar_botao_voltar(PaginaEscolherTipoObjeto) # Volta para a seleção de tipo

    def carregar_lista(self):
        self.listbox.delete(0, tk.END) # Limpa a lista
        if self.tipo_objeto == "Combatente":
            nomes = gd.obter_nomes_tipos_combatentes()
        elif self.tipo_objeto == "Estilo":
            nomes = gd.obter_nomes_estilos_luta()
        else:
            nomes = []

        for nome in nomes:
            self.listbox.insert(tk.END, nome)

    def editar_selecionado(self):
        selecionado_idx = self.listbox.curselection()
        if not selecionado_idx:
            messagebox.showwarning("Nenhum Objeto Selecionado", "Por favor, selecione um objeto da lista para editar.")
            return

        nome_selecionado = self.listbox.get(selecionado_idx[0])

        if self.tipo_objeto == "Combatente":
            dados_objeto = gd.obter_tipo_por_nome(nome_selecionado)
        elif self.tipo_objeto == "Estilo":
            dados_objeto = gd.obter_estilo_por_nome(nome_selecionado)
        else:
            dados_objeto = None

        if dados_objeto:
            self.app_controller.mostrar_pagina(PaginaEditarDetalhesObjeto,
                                               tipo_objeto=self.tipo_objeto,
                                               dados_objeto=dados_objeto,
                                               nome_original=nome_selecionado)
        else:
             messagebox.showerror("Erro", f"Não foi possível carregar os dados para '{nome_selecionado}'.")

    def deletar_selecionado(self):
        selecionado_idx = self.listbox.curselection()
        if not selecionado_idx:
            messagebox.showwarning("Nenhum Objeto Selecionado", "Por favor, selecione um objeto da lista para deletar.")
            return

        nome_selecionado = self.listbox.get(selecionado_idx[0])
        confirmar = messagebox.askyesno("Confirmar Deleção", f"Tem certeza que deseja deletar '{nome_selecionado}'?\nIsso não pode ser desfeito e pode afetar simulações salvas.")

        if confirmar:
            sucesso = gd.deletar_objeto(nome_selecionado, self.tipo_objeto)
            if sucesso:
                messagebox.showinfo("Sucesso", f"'{nome_selecionado}' deletado com sucesso.")
                self.carregar_lista() # Recarrega a lista
            else:
                messagebox.showerror("Erro", f"Não foi possível deletar '{nome_selecionado}'.")


# --- Página Editar Detalhes do Objeto (Combatente ou Estilo) ---
class PaginaEditarDetalhesObjeto(PaginaBase):
    def __init__(self, parent, app_controller, tipo_objeto, dados_objeto=None, nome_original=None):
        super().__init__(parent, app_controller)
        self.tipo_objeto = tipo_objeto
        self.dados_originais = dados_objeto # Guarda os dados se for edição
        self.nome_original = nome_original # Guarda o nome original se for edição

        titulo = f"Criar Novo {tipo_objeto}" if dados_objeto is None else f"Editar {tipo_objeto}: {nome_original}"
        tk.Label(self, text=titulo, font=("Arial", 14)).pack(pady=10)

        self.entries = {} # Dicionário para guardar os widgets de entrada
        self.vars = {} # Dicionário para guardar as StringVars/Outras Vars

        frame_form = tk.Frame(self)
        frame_form.pack(pady=PAD_Y, padx=20, fill="x")

        # --- Campos Comuns e Específicos ---
        if self.tipo_objeto == "Combatente":
            atributos = gd.get_atributos_tipo_combatente()
            valores_padrao = gd.get_valores_padrao_tipo_combatente()
            campos_numericos_int = ["hp_max", "taxa_ataque", "tamanho_raio"]
            campos_numericos_float = ["forca_base", "resistencia", "alcance_base", "velocidade"]
            campos_dropdown = {}
        elif self.tipo_objeto == "Estilo":
            atributos = gd.get_atributos_estilo_luta()
            valores_padrao = gd.get_valores_padrao_estilo_luta()
            campos_numericos_int = ["bonus_dano_vital"]
            campos_numericos_float = ["modificador_dano", "modificador_alcance", "modificador_taxa_ataque"]
            campos_dropdown = {
                 "tipo_alcance": gd.get_tipos_alcance_validos(),
                 "estrategia_mira": gd.get_estrategias_mira_validas()
            }
        else:
             tk.Label(frame_form, text="Tipo de objeto inválido.").pack()
             self._criar_botao_voltar(PaginaEscolherTipoObjeto)
             return # Não continua a criar campos

        # Cria labels e entries/dropdowns dinamicamente
        for i, attr in enumerate(atributos):
            valor_atual = self.dados_originais.get(attr) if self.dados_originais else valores_padrao.get(attr)

            tk.Label(frame_form, text=f"{attr.replace('_', ' ').title()}:").grid(row=i, column=0, sticky="w", padx=PAD_X, pady=PAD_Y)

            if attr in campos_dropdown:
                opcoes = campos_dropdown[attr]
                var = tk.StringVar(value=str(valor_atual))
                combobox = ttk.Combobox(frame_form, textvariable=var, values=opcoes, state="readonly", width=LARGURA_ENTRY-2)
                combobox.grid(row=i, column=1, sticky="ew", padx=PAD_X, pady=PAD_Y)
                self.entries[attr] = combobox # Guardamos o widget para pegar o valor depois
                self.vars[attr] = var
            else:
                var = tk.StringVar(value=str(valor_atual))
                entry = tk.Entry(frame_form, textvariable=var, width=LARGURA_ENTRY)
                entry.grid(row=i, column=1, sticky="ew", padx=PAD_X, pady=PAD_Y)
                self.entries[attr] = entry
                self.vars[attr] = var

                # Adiciona validação para campos numéricos
                if attr in campos_numericos_int:
                    vcmd = (self.register(lambda P: self._validar_entry_numero(P, int)), '%P')
                    entry.config(validate='key', validatecommand=vcmd)
                elif attr in campos_numericos_float:
                    # Permite '.' para float
                    vcmd = (self.register(lambda P: self._validar_entry_numero(P, float)), '%P')
                    entry.config(validate='key', validatecommand=vcmd)


        # Botão Salvar
        tk.Button(self, text="Salvar", command=self.salvar).pack(pady=20)

        # Botão Voltar (volta para lista se editou, ou escolha de tipo se criou)
        pagina_anterior = PaginaListarEditarObjeto if self.dados_originais else PaginaEscolherTipoObjeto
        # Passa o tipo_objeto se estiver voltando para a lista
        kwargs_voltar = {'tipo_objeto': self.tipo_objeto} if self.dados_originais else {}
        self._criar_botao_voltar(pagina_anterior, **kwargs_voltar)

    def salvar(self):
        """Coleta os dados dos campos e salva no JSON."""
        novos_dados = {}
        chave_nome = "nome_tipo" if self.tipo_objeto == "Combatente" else "nome_estilo"
        nome_novo = ""

        # Define campos numéricos para conversão correta
        if self.tipo_objeto == "Combatente":
            campos_numericos_int = ["hp_max", "taxa_ataque", "tamanho_raio"]
            campos_numericos_float = ["forca_base", "resistencia", "alcance_base", "velocidade"]
        else: # Estilo
            campos_numericos_int = ["bonus_dano_vital"]
            campos_numericos_float = ["modificador_dano", "modificador_alcance", "modificador_taxa_ataque"]

        for attr, widget in self.entries.items():
            valor_str = self.vars[attr].get()
            valor_final = None

            if not valor_str and attr != chave_nome: # Permite nome vazio temporariamente? Não.
                 if attr in campos_numericos_int or attr in campos_numericos_float:
                      valor_str = "0" # Default para números se vazio
                 else:
                      messagebox.showerror("Erro", f"O campo '{attr}' não pode estar vazio.")
                      return

            try:
                if attr == chave_nome:
                    if not valor_str.strip():
                         messagebox.showerror("Erro", "O nome não pode estar vazio.")
                         return
                    valor_final = valor_str.strip()
                    nome_novo = valor_final
                elif attr in campos_numericos_int:
                    valor_final = int(valor_str)
                elif attr in campos_numericos_float:
                    valor_final = float(valor_str)
                else: # Strings (como tipo_alcance, estrategia_mira)
                    valor_final = valor_str

                novos_dados[attr] = valor_final
            except ValueError:
                messagebox.showerror("Erro de Conversão", f"Valor inválido '{valor_str}' para o campo '{attr}'.")
                return # Interrompe o salvamento

        # Tenta salvar
        sucesso = False
        if self.tipo_objeto == "Combatente":
            sucesso = gd.adicionar_ou_atualizar_tipo(novos_dados, self.nome_original)
        elif self.tipo_objeto == "Estilo":
             sucesso = gd.adicionar_ou_atualizar_estilo(novos_dados, self.nome_original)

        if sucesso:
            messagebox.showinfo("Sucesso", f"{self.tipo_objeto} '{nome_novo}' salvo com sucesso!")
            # Volta para a tela anterior
            pagina_anterior = PaginaListarEditarObjeto if self.dados_originais else PaginaEscolherTipoObjeto
            # Se estava editando, precisa passar o tipo de objeto de volta
            if self.dados_originais:
                 self.app_controller.mostrar_pagina(pagina_anterior, tipo_objeto=self.tipo_objeto)
            else:
                 self.app_controller.mostrar_pagina(pagina_anterior) # Modo criar não precisa
        else:
            messagebox.showerror("Erro", f"Falha ao salvar o {self.tipo_objeto}.")

# --- Página Criar/Editar Simulação ---
class PaginaCriarSimulacao(PaginaBase):
    def __init__(self, parent, app_controller, simulacao_existente=None):
        super().__init__(parent, app_controller)
        self.simulacao_original = simulacao_existente # Guarda dados se for edição
        self.nome_original = simulacao_existente.get("nome_simulacao") if simulacao_existente else None

        titulo = "Criar Nova Simulação" if simulacao_existente is None else f"Editar Simulação: {self.nome_original}"
        tk.Label(self, text=titulo, font=("Arial", 14)).pack(pady=10)

        # --- Frame Principal para Scroll ---
        canvas = tk.Canvas(self)
        scrollbar_y = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollbar_x = tk.Scrollbar(self, orient="horizontal", command=canvas.xview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)


        # --- Configurações Gerais ---
        frame_geral = ttk.LabelFrame(scrollable_frame, text="Configurações Gerais")
        frame_geral.pack(pady=PAD_Y, padx=PAD_X, fill="x")

        tk.Label(frame_geral, text="Nome da Simulação:").grid(row=0, column=0, sticky="w", padx=PAD_X, pady=PAD_Y)
        self.nome_simulacao_var = tk.StringVar(value=self.nome_original or "Nova Simulação")
        tk.Entry(frame_geral, textvariable=self.nome_simulacao_var, width=LARGURA_ENTRY).grid(row=0, column=1, sticky="ew", padx=PAD_X, pady=PAD_Y)

        # Arena (opcional, pode ser fixo ou configurável)
        tk.Label(frame_geral, text="Largura Arena:").grid(row=1, column=0, sticky="w", padx=PAD_X, pady=PAD_Y)
        self.largura_arena_var = tk.StringVar(value=str(simulacao_existente.get("arena_largura", 800) if simulacao_existente else 800))
        vcmd_int = (self.register(lambda P: self._validar_entry_numero(P, int)), '%P')
        tk.Entry(frame_geral, textvariable=self.largura_arena_var, width=10, validate='key', validatecommand=vcmd_int).grid(row=1, column=1, sticky="w", padx=PAD_X, pady=PAD_Y)

        tk.Label(frame_geral, text="Altura Arena:").grid(row=2, column=0, sticky="w", padx=PAD_X, pady=PAD_Y)
        self.altura_arena_var = tk.StringVar(value=str(simulacao_existente.get("arena_altura", 600) if simulacao_existente else 600))
        tk.Entry(frame_geral, textvariable=self.altura_arena_var, width=10, validate='key', validatecommand=vcmd_int).grid(row=2, column=1, sticky="w", padx=PAD_X, pady=PAD_Y)

        # --- Configuração de Equipes ---
        self.frame_equipes_container = tk.Frame(scrollable_frame)
        self.frame_equipes_container.pack(pady=PAD_Y, padx=PAD_X, fill="x")
        self.frames_equipes = [] # Guarda os frames de cada equipe
        self.dados_equipes = [] # Guarda os dados (membros) de cada equipe

        # Carrega tipos e estilos para os dropdowns
        self.tipos_combatentes_nomes = gd.obter_nomes_tipos_combatentes()
        self.estilos_luta_nomes = gd.obter_nomes_estilos_luta()
        if not self.tipos_combatentes_nomes:
             messagebox.showwarning("Aviso", "Nenhum tipo de combatente definido. Crie um antes de configurar a simulação.")
        if not self.estilos_luta_nomes:
             messagebox.showwarning("Aviso", "Nenhum estilo de luta definido. Crie um antes de configurar a simulação.")


        tk.Button(scrollable_frame, text="Adicionar Equipe", command=self.adicionar_frame_equipe).pack(pady=PAD_Y)

        # --- Empacotamento do Canvas e Scrollbars (ainda dentro do 'self') ---
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True) # Canvas ocupa o topo
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X) # Scroll X abaixo do canvas

        # --- Botões de Ação (fora do scroll, no 'self', abaixo de tudo) ---
        frame_acoes = tk.Frame(self) # Criado diretamente no 'self' (a página)
        frame_acoes.pack(side=tk.BOTTOM, fill="x", pady=10) # Empacota no fundo

        # Centraliza os botões dentro do frame_acoes
        tk.Button(frame_acoes, text="Salvar Simulação", command=self.salvar_simulacao).pack(side=tk.LEFT, padx=PAD_X, expand=True)
        tk.Button(frame_acoes, text="Começar Simulação", command=self.comecar_simulacao).pack(side=tk.LEFT, padx=PAD_X, expand=True)
        self._criar_botao_voltar_simulacao(frame_acoes) # O botão voltar ainda vai para a direita deste frame
        
        # Preenche com equipes existentes se estiver editando
        if simulacao_existente and 'equipes' in simulacao_existente:
             for equipe_data in simulacao_existente['equipes']:
                 self.adicionar_frame_equipe(equipe_data) # Passa os dados para preencher


    def _criar_botao_voltar_simulacao(self, parent_frame):
        pagina_anterior = PaginaSimulacoesCriadas if self.simulacao_original else PaginaMenuPrincipal
        # Não precisa de kwargs extras aqui, pois PaginaSimulacoesCriadas e PaginaMenuPrincipal não exigem
        tk.Button(parent_frame, text="< Voltar",
              command=lambda cls=pagina_anterior: self.app_controller.mostrar_pagina(cls)
             ).pack(side=tk.RIGHT, padx=PAD_X) # Coloca no lado direito

    def adicionar_frame_equipe(self, dados_equipe_existente=None):
        """Adiciona um novo frame para configurar uma equipe."""
        id_equipe = len(self.frames_equipes) + 1
        frame_equipe = ttk.LabelFrame(self.frame_equipes_container, text=f"Equipe {id_equipe}")
        frame_equipe.pack(pady=PAD_Y, padx=PAD_X, fill="x", expand=True)
        self.frames_equipes.append(frame_equipe)

        # --- Cor da Equipe ---
        frame_cor = tk.Frame(frame_equipe)
        frame_cor.pack(fill="x", padx=PAD_X, pady=PAD_Y)
        tk.Label(frame_cor, text="Cor:").pack(side=tk.LEFT)
        cor_inicial_rgb = dados_equipe_existente.get('cor', (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))) if dados_equipe_existente else (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        cor_inicial_hex = '#%02x%02x%02x' % cor_inicial_rgb
        cor_label = tk.Label(frame_cor, text="    ", bg=cor_inicial_hex, relief="sunken", width=4)
        cor_label.pack(side=tk.LEFT, padx=PAD_X)
        tk.Button(frame_cor, text="Escolher Cor", command=lambda lbl=cor_label: self.escolher_cor(lbl)).pack(side=tk.LEFT)

        # Guarda a referência da label de cor para buscar a cor depois
        frame_equipe.cor_label = cor_label # Associa ao frame da equipe

        # --- Adicionar Membros ---
        frame_add_membro = tk.Frame(frame_equipe)
        frame_add_membro.pack(fill="x", padx=PAD_X, pady=PAD_Y)

        tk.Label(frame_add_membro, text="Tipo:").pack(side=tk.LEFT)
        tipo_var = tk.StringVar()
        tipo_combo = ttk.Combobox(frame_add_membro, textvariable=tipo_var, values=self.tipos_combatentes_nomes, state="readonly", width=15)
        tipo_combo.pack(side=tk.LEFT, padx=PAD_X)
        if self.tipos_combatentes_nomes: tipo_combo.current(0) # Seleciona o primeiro se houver

        tk.Label(frame_add_membro, text="Estilo:").pack(side=tk.LEFT)
        estilo_var = tk.StringVar()
        estilo_combo = ttk.Combobox(frame_add_membro, textvariable=estilo_var, values=self.estilos_luta_nomes, state="readonly", width=15)
        estilo_combo.pack(side=tk.LEFT, padx=PAD_X)
        if self.estilos_luta_nomes: estilo_combo.current(0)

        tk.Label(frame_add_membro, text="Qtd:").pack(side=tk.LEFT)
        qtd_var = tk.StringVar(value="1")
        vcmd_int = (self.register(lambda P: self._validar_entry_numero(P, int)), '%P')
        qtd_entry = tk.Entry(frame_add_membro, textvariable=qtd_var, width=5, validate='key', validatecommand=vcmd_int)
        qtd_entry.pack(side=tk.LEFT, padx=PAD_X)

        tk.Button(frame_add_membro, text="+ Add Membro",
                  command=lambda f=frame_equipe, tv=tipo_var, ev=estilo_var, qv=qtd_var: self.adicionar_membro_lista(f, tv, ev, qv)
                  ).pack(side=tk.LEFT, padx=PAD_X)

        # --- Lista de Membros Adicionados ---
        frame_lista_membros = tk.Frame(frame_equipe)
        frame_lista_membros.pack(fill="x", expand=True, padx=PAD_X, pady=PAD_Y)

        listbox_membros = tk.Listbox(frame_lista_membros, height=4, width=55)
        listbox_membros.pack(side=tk.LEFT, fill="x", expand=True)
        frame_equipe.listbox_membros = listbox_membros # Associa ao frame da equipe

        tk.Button(frame_lista_membros, text="- Remover Sel.",
                  command=lambda lb=listbox_membros: self.remover_membro_lista(lb)
                  ).pack(side=tk.LEFT, padx=PAD_X, anchor="center")

        # Guarda a referência dos widgets de entrada para esta equipe
        frame_equipe.widgets_entrada = {'tipo': tipo_combo, 'estilo': estilo_combo, 'qtd': qtd_entry}

        # Preenche a lista se editando
        if dados_equipe_existente and 'membros' in dados_equipe_existente:
             frame_equipe.dados_membros_internos = list(dados_equipe_existente['membros']) # Copia os dados
             self._atualizar_listbox_membros(frame_equipe)
        else:
             frame_equipe.dados_membros_internos = [] # Lista para guardar {'nome_tipo': '...', 'quantidade': ..., 'estilo_luta': '...'}


    def escolher_cor(self, label_cor):
        """Abre o seletor de cores e atualiza a label."""
        cor_rgb, cor_hex = colorchooser.askcolor(parent=self, title="Escolha a cor da equipe")
        if cor_hex:
            label_cor.config(bg=cor_hex)

    def adicionar_membro_lista(self, frame_equipe, tipo_var, estilo_var, qtd_var):
        """Adiciona um membro à lista interna e visual da equipe."""
        nome_tipo = tipo_var.get()
        nome_estilo = estilo_var.get()
        try:
            quantidade = int(qtd_var.get())
            if quantidade <= 0:
                messagebox.showerror("Erro", "Quantidade deve ser maior que zero.")
                return
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida.")
            return

        if not nome_tipo or not nome_estilo:
             messagebox.showerror("Erro", "Selecione um Tipo e um Estilo.")
             return

        novo_membro = {
            "nome_tipo": nome_tipo,
            "quantidade": quantidade,
            "estilo_luta": nome_estilo
        }
        frame_equipe.dados_membros_internos.append(novo_membro)
        self._atualizar_listbox_membros(frame_equipe)
        # Limpa campos? Opcional
        # qtd_var.set("1")

    def remover_membro_lista(self, listbox_membros):
        """Remove o membro selecionado da lista."""
        selecionado_idx = listbox_membros.curselection()
        if not selecionado_idx:
            messagebox.showwarning("Aviso", "Selecione um membro da lista para remover.")
            return

        idx = selecionado_idx[0]
        # Encontra o frame pai (da equipe) a partir da listbox
        frame_equipe = listbox_membros.master.master # listbox -> frame_lista -> frame_equipe
        if idx < len(frame_equipe.dados_membros_internos):
            del frame_equipe.dados_membros_internos[idx]
            self._atualizar_listbox_membros(frame_equipe)

    def _atualizar_listbox_membros(self, frame_equipe):
        """Atualiza o conteúdo da listbox de membros de uma equipe."""
        listbox = frame_equipe.listbox_membros
        listbox.delete(0, tk.END)
        for membro in frame_equipe.dados_membros_internos:
            texto = f"{membro['quantidade']}x {membro['nome_tipo']} ({membro['estilo_luta']})"
            listbox.insert(tk.END, texto)

    def _coletar_dados_simulacao(self):
        """Coleta todos os dados configurados na página."""
        nome_sim = self.nome_simulacao_var.get().strip()
        if not nome_sim:
            messagebox.showerror("Erro", "O nome da simulação não pode estar vazio.")
            return None

        try:
             largura = int(self.largura_arena_var.get())
             altura = int(self.altura_arena_var.get())
             if largura <= 0 or altura <= 0: raise ValueError()
        except ValueError:
             messagebox.showerror("Erro", "Largura e Altura da Arena devem ser números positivos.")
             return None

        dados_simulacao = {
            "nome_simulacao": nome_sim,
            "arena_largura": largura,
            "arena_altura": altura,
            "equipes": []
        }

        for i, frame_eq in enumerate(self.frames_equipes):
            id_equipe = i + 1
            cor_hex = frame_eq.cor_label.cget("bg")
            cor_rgb = tuple(int(cor_hex[i:i+2], 16) for i in (1, 3, 5)) # Converte #rrggbb para (r, g, b)

            membros = frame_eq.dados_membros_internos
            if not membros:
                 messagebox.showwarning("Aviso", f"Equipe {id_equipe} não tem membros e será ignorada.")
                 continue # Pula equipe vazia

            dados_simulacao["equipes"].append({
                "id_equipe": id_equipe,
                "cor": list(cor_rgb), # Salva como lista no JSON
                "membros": membros
            })

        if len(dados_simulacao["equipes"]) < 2:
             messagebox.showerror("Erro", "A simulação precisa de pelo menos duas equipes com membros.")
             return None

        return dados_simulacao


    def salvar_simulacao(self):
        """Salva a configuração atual da simulação."""
        dados_para_salvar = self._coletar_dados_simulacao()
        if dados_para_salvar:
            sucesso = gd.adicionar_ou_atualizar_simulacao(dados_para_salvar, self.nome_original)
            if sucesso:
                messagebox.showinfo("Sucesso", f"Simulação '{dados_para_salvar['nome_simulacao']}' salva.")
                self.nome_original = dados_para_salvar['nome_simulacao'] # Atualiza nome original caso tenha sido renomeado
            else:
                messagebox.showerror("Erro", "Falha ao salvar a simulação.")

    def comecar_simulacao(self):
        """Coleta os dados e chama o controller para iniciar o Pygame."""
        dados_simulacao = self._coletar_dados_simulacao()
        if dados_simulacao:
            print("Iniciando simulação com os seguintes dados:")
            print(json.dumps(dados_simulacao, indent=2))
            self.app_controller.iniciar_pygame(dados_simulacao)


# --- Página Listar Simulações Criadas ---
class PaginaSimulacoesCriadas(PaginaBase):
    def __init__(self, parent, app_controller):
        super().__init__(parent, app_controller)

        tk.Label(self, text="Simulações Salvas", font=("Arial", 14)).pack(pady=10)

        frame_lista = tk.Frame(self)
        frame_lista.pack(pady=PAD_Y, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame_lista)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(frame_lista, yscrollcommand=scrollbar.set, width=50, height=15)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        self.carregar_lista()

        frame_botoes = tk.Frame(self)
        frame_botoes.pack(pady=PAD_Y)

        tk.Button(frame_botoes, text="Editar Selecionada", command=self.editar_selecionada).pack(side=tk.LEFT, padx=PAD_X)
        tk.Button(frame_botoes, text="Começar Selecionada", command=self.comecar_selecionada).pack(side=tk.LEFT, padx=PAD_X)
        tk.Button(frame_botoes, text="Deletar Selecionada", command=self.deletar_selecionada).pack(side=tk.LEFT, padx=PAD_X)

        self._criar_botao_voltar(PaginaMenuPrincipal)

    def carregar_lista(self):
        self.listbox.delete(0, tk.END)
        nomes = gd.obter_nomes_simulacoes()
        for nome in nomes:
            self.listbox.insert(tk.END, nome)

    def _get_simulacao_selecionada(self):
        """Obtém os dados da simulação selecionada na listbox."""
        selecionado_idx = self.listbox.curselection()
        if not selecionado_idx:
            messagebox.showwarning("Nenhuma Simulação Selecionada", "Por favor, selecione uma simulação da lista.")
            return None, None

        nome_selecionado = self.listbox.get(selecionado_idx[0])
        dados_simulacao = gd.obter_simulacao_por_nome(nome_selecionado)

        if not dados_simulacao:
             messagebox.showerror("Erro", f"Não foi possível carregar os dados para a simulação '{nome_selecionado}'. O arquivo JSON pode estar corrompido.")
             return None, None
        return nome_selecionado, dados_simulacao

    def editar_selecionada(self):
        nome_selecionado, dados_simulacao = self._get_simulacao_selecionada()
        if dados_simulacao:
            self.app_controller.mostrar_pagina(PaginaCriarSimulacao, simulacao_existente=dados_simulacao)

    def comecar_selecionada(self):
        nome_selecionado, dados_simulacao = self._get_simulacao_selecionada()
        if dados_simulacao:
            print(f"Iniciando simulação salva: {nome_selecionado}")
            print(json.dumps(dados_simulacao, indent=2))
            self.app_controller.iniciar_pygame(dados_simulacao)

    def deletar_selecionada(self):
        nome_selecionado, _ = self._get_simulacao_selecionada()
        if nome_selecionado:
             confirmar = messagebox.askyesno("Confirmar Deleção", f"Tem certeza que deseja deletar a simulação '{nome_selecionado}'?")
             if confirmar:
                 sucesso = gd.deletar_simulacao(nome_selecionado)
                 if sucesso:
                     messagebox.showinfo("Sucesso", f"Simulação '{nome_selecionado}' deletada.")
                     self.carregar_lista() # Atualiza a lista visual
                 else:
                      messagebox.showerror("Erro", f"Falha ao deletar a simulação '{nome_selecionado}'.")