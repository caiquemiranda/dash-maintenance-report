import sqlite3
import os

def get_db_connection():
    """Estabelece conexão com o banco de dados SQLite"""
    # Verificar se o diretório data existe
    if not os.path.exists('../data/db'):
        os.makedirs('../data/db')
    
    # Caminho do banco de dados
    db_path = '../data/db/dashboard.db'
    
    # Conectar ao banco de dados
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    return conn

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Criar tabela de clientes se não existir
    c.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    )
    ''')
    
    # Verificar se a tabela lista_de_pontos já existe
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lista_de_pontos'")
    tabela_existe = c.fetchone()
    
    if tabela_existe:
        # Verificar se a coluna 'cliente' existe
        c.execute("PRAGMA table_info(lista_de_pontos)")
        colunas = c.fetchall()
        tem_coluna_cliente = any(col['name'] == 'cliente' for col in colunas)
        
        if not tem_coluna_cliente:
            # Adicionar a coluna cliente
            try:
                c.execute("ALTER TABLE lista_de_pontos ADD COLUMN cliente TEXT")
                # Preencher com dados existentes
                c.execute("""
                UPDATE lista_de_pontos 
                SET cliente = (SELECT nome FROM clientes WHERE clientes.id = lista_de_pontos.cliente_id)
                """)
                conn.commit()
                print("Coluna 'cliente' adicionada à tabela existente")
            except Exception as e:
                print(f"Erro ao adicionar coluna: {str(e)}")
    else:
        # Criar tabela de lista_de_pontos se não existir
        c.execute('''
        CREATE TABLE IF NOT EXISTS lista_de_pontos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_disp TEXT NOT NULL,
            type TEXT,
            action TEXT,
            description TEXT,
            cliente TEXT NOT NULL,
            cliente_id INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
        ''')
    
    # Criar tabela de plano de manutenção se não existir
    c.execute('''
    CREATE TABLE IF NOT EXISTS plano_manutencao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_disp TEXT NOT NULL,
        cliente TEXT NOT NULL,
        cliente_id INTEGER,
        periodicidade INTEGER,  -- 1=mensal, 3=trimestral, 6=semestral, 12=anual
        mes_inicio INTEGER,     -- mês de início da manutenção (1-12)
        FOREIGN KEY (cliente_id) REFERENCES clientes (id)
    )
    ''')
    
    # Inserir clientes iniciais
    clientes = ['BRD', 'BYR', 'AERO', 'BSC']
    for cliente in clientes:
        try:
            c.execute("INSERT INTO clientes (nome) VALUES (?)", (cliente,))
        except sqlite3.IntegrityError:
            # Cliente já existe, ignorar
            pass
    
    conn.commit()
    conn.close()

def get_cliente_id(nome_cliente):
    """Obtém o ID do cliente pelo nome"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT id FROM clientes WHERE nome = ?", (nome_cliente,))
    result = c.fetchone()
    
    conn.close()
    return result['id'] if result else None

def salvar_pontos(cliente, dados_df):
    """Salva os dados de pontos no banco para um cliente específico"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Obter ID do cliente
    cliente_id = get_cliente_id(cliente)
    if not cliente_id:
        # Se o cliente não existir, criar
        c.execute("INSERT INTO clientes (nome) VALUES (?)", (cliente,))
        cliente_id = c.lastrowid
    
    # Remover dados antigos deste cliente (opcional)
    c.execute("DELETE FROM lista_de_pontos WHERE cliente_id = ?", (cliente_id,))
    
    # Inserir novos dados
    for _, row in dados_df.iterrows():
        c.execute('''
        INSERT INTO lista_de_pontos (id_disp, type, action, description, cliente, cliente_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            row['id_disp'],
            row['type'],
            row['action'],
            row['description'],
            cliente,
            cliente_id
        ))
    
    conn.commit()
    conn.close()
    return True

def buscar_pontos(cliente):
    """Busca os dados de pontos para um cliente específico"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Obter ID do cliente
    cliente_id = get_cliente_id(cliente)
    if not cliente_id:
        conn.close()
        return []
    
    # Verificar se a coluna cliente existe na tabela
    c.execute("PRAGMA table_info(lista_de_pontos)")
    colunas = c.fetchall()
    tem_coluna_cliente = any(col['name'] == 'cliente' for col in colunas)
    
    # Definir colunas a selecionar com base na existência da coluna cliente
    if tem_coluna_cliente:
        colunas_select = "id_disp, type, action, description, cliente"
    else:
        colunas_select = "id_disp, type, action, description"
    
    # Buscar dados
    c.execute(f'''
    SELECT {colunas_select}
    FROM lista_de_pontos
    WHERE cliente_id = ?
    ''', (cliente_id,))
    
    # Converter para lista de dicionários
    resultado = [dict(row) for row in c.fetchall()]
    
    # Se a coluna cliente não existir, adicionar o nome do cliente manualmente
    if not tem_coluna_cliente:
        for row in resultado:
            row['cliente'] = cliente
    
    conn.close()
    return resultado

def salvar_plano_manutencao(cliente, plano_df):
    """
    Salva o plano de manutenção para um cliente específico
    
    Parâmetros:
    cliente (str): Nome do cliente
    plano_df (DataFrame): DataFrame com as colunas id_disp e periodicidade
    
    Retorna:
    bool: True se salvo com sucesso
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # Obter ID do cliente
    cliente_id = get_cliente_id(cliente)
    if not cliente_id:
        # Se o cliente não existir, criar
        c.execute("INSERT INTO clientes (nome) VALUES (?)", (cliente,))
        cliente_id = c.lastrowid
    
    # Remover plano antigo deste cliente
    c.execute("DELETE FROM plano_manutencao WHERE cliente_id = ?", (cliente_id,))
    
    # Inserir novos dados
    import datetime
    mes_atual = datetime.datetime.now().month
    
    for _, row in plano_df.iterrows():
        c.execute('''
        INSERT INTO plano_manutencao (id_disp, cliente, cliente_id, periodicidade, mes_inicio)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            row['id_disp'],
            cliente,
            cliente_id,
            row['periodicidade'],
            mes_atual  # Começa a partir do mês atual
        ))
    
    conn.commit()
    conn.close()
    return True

def buscar_plano_manutencao(cliente):
    """
    Busca o plano de manutenção para um cliente específico
    
    Parâmetros:
    cliente (str): Nome do cliente
    
    Retorna:
    list: Lista de dicionários com o plano de manutenção
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # Obter ID do cliente
    cliente_id = get_cliente_id(cliente)
    if not cliente_id:
        conn.close()
        return []
    
    # Buscar dados
    c.execute('''
    SELECT id_disp, periodicidade, mes_inicio
    FROM plano_manutencao
    WHERE cliente_id = ?
    ''', (cliente_id,))
    
    # Converter para lista de dicionários
    resultado = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return resultado

def buscar_manutencao_mensal(cliente, mes):
    """
    Busca as manutenções programadas para um cliente em um mês específico
    
    Parâmetros:
    cliente (str): Nome do cliente
    mes (int): Número do mês (1-12)
    
    Retorna:
    list: Lista de ids de dispositivos que devem ser testados no mês
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # Obter ID do cliente
    cliente_id = get_cliente_id(cliente)
    if not cliente_id:
        conn.close()
        return []
    
    # Buscar dispositivos que devem ser testados no mês
    c.execute('''
    SELECT pm.id_disp, pm.periodicidade, pm.mes_inicio,
           lp.type, lp.action, lp.description 
    FROM plano_manutencao pm
    JOIN lista_de_pontos lp ON pm.id_disp = lp.id_disp AND pm.cliente_id = lp.cliente_id
    WHERE pm.cliente_id = ?
    ''', (cliente_id,))
    
    resultados = [dict(row) for row in c.fetchall()]
    dispositivos_para_testar = []
    
    # Para cada dispositivo, verifica se ele deve ser testado no mês especificado
    for disp in resultados:
        periodicidade = disp['periodicidade']
        mes_inicio = disp['mes_inicio']
        
        # Meses desde o início
        meses_desde_inicio = (mes - mes_inicio) % 12
        
        # Mensal (periodicidade=1): testar todos os meses
        # Trimestral (periodicidade=3): testar a cada 3 meses
        # Semestral (periodicidade=6): testar a cada 6 meses
        # Anual (periodicidade=12): testar uma vez por ano
        if meses_desde_inicio % periodicidade == 0:
            dispositivos_para_testar.append(disp)
    
    conn.close()
    return dispositivos_para_testar 