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