import sqlite3
import os
from datetime import datetime

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
    
    # Verificar se a tabela plano_manutencao já existe
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plano_manutencao'")
    tabela_plano_existe = c.fetchone()
    
    if tabela_plano_existe:
        # Verificar se a coluna 'mes_manutencao' existe
        c.execute("PRAGMA table_info(plano_manutencao)")
        colunas = c.fetchall()
        tem_coluna_mes_manutencao = any(col['name'] == 'mes_manutencao' for col in colunas)
        
        if not tem_coluna_mes_manutencao:
            # A tabela existe mas não tem a nova estrutura, precisamos recriar
            try:
                # Salvar os dados antigos
                c.execute("SELECT id_disp, cliente, cliente_id, periodicidade FROM plano_manutencao")
                dados_antigos = c.fetchall()
                
                # Remover tabela antiga
                c.execute("DROP TABLE plano_manutencao")
                
                # Criar nova tabela
                c.execute('''
                CREATE TABLE plano_manutencao (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_disp TEXT NOT NULL,
                    cliente TEXT NOT NULL,
                    cliente_id INTEGER,
                    mes_manutencao INTEGER,
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
                )
                ''')
                
                # Migrar dados antigos calculando o mês pela periodicidade
                # Para simplificar, colocamos todos os dispositivos no mês 1 (janeiro)
                if dados_antigos:
                    for dado in dados_antigos:
                        c.execute('''
                        INSERT INTO plano_manutencao (id_disp, cliente, cliente_id, mes_manutencao)
                        VALUES (?, ?, ?, 1)
                        ''', (dado['id_disp'], dado['cliente'], dado['cliente_id']))
                
                conn.commit()
                print("Tabela 'plano_manutencao' recriada com a nova estrutura")
            except Exception as e:
                print(f"Erro ao recriar tabela plano_manutencao: {str(e)}")
    else:
        # Criar tabela de plano de manutenção se não existir
        c.execute('''
        CREATE TABLE IF NOT EXISTS plano_manutencao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_disp TEXT NOT NULL,
            cliente TEXT NOT NULL,
            cliente_id INTEGER,
            mes_manutencao INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
        ''')
    
    # Verificar se a tabela testes_dispositivos já existe
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='testes_dispositivos'")
    tabela_testes_existe = c.fetchone()
    
    if not tabela_testes_existe:
        # Criar tabela para armazenar os testes de dispositivos
        c.execute('''
        CREATE TABLE IF NOT EXISTS testes_dispositivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_disp TEXT NOT NULL,
            cliente TEXT NOT NULL,
            cliente_id INTEGER,
            mes INTEGER NOT NULL,      -- Mês do teste (1-12)
            ano INTEGER NOT NULL,      -- Ano do teste (ex: 2023)
            status TEXT NOT NULL,      -- 'ok' ou 'nao_ok'
            observacao TEXT,           -- Observações adicionais
            data_teste TEXT,           -- Data em que o teste foi realizado
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
    plano_df (DataFrame): DataFrame com as colunas id_disp e mes_manutencao
    
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
    for _, row in plano_df.iterrows():
        c.execute('''
        INSERT INTO plano_manutencao (id_disp, cliente, cliente_id, mes_manutencao)
        VALUES (?, ?, ?, ?)
        ''', (
            row['id_disp'],
            cliente,
            cliente_id,
            row['mes_manutencao']
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
    SELECT id_disp, mes_manutencao
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
    
    # Debug: Verificar total de registros no plano de manutenção
    c.execute('''
    SELECT COUNT(*) FROM plano_manutencao WHERE cliente_id = ?
    ''', (cliente_id,))
    total_registros = c.fetchone()[0]
    print(f"Total de registros no plano para cliente {cliente}: {total_registros}")
    
    # Debug: Verificar quantos meses diferentes estão registrados
    c.execute('''
    SELECT mes_manutencao, COUNT(*) FROM plano_manutencao 
    WHERE cliente_id = ? GROUP BY mes_manutencao
    ''', (cliente_id,))
    meses_registrados = c.fetchall()
    for mes_reg in meses_registrados:
        print(f"Mês {mes_reg[0]}: {mes_reg[1]} dispositivos")
    
    # Buscar dispositivos que devem ser testados no mês
    c.execute('''
    SELECT pm.id_disp, pm.mes_manutencao,
            lp.type, lp.action, lp.description 
    FROM plano_manutencao pm
    JOIN lista_de_pontos lp ON pm.id_disp = lp.id_disp AND pm.cliente_id = lp.cliente_id
    WHERE pm.cliente_id = ? AND pm.mes_manutencao = ?
    ''', (cliente_id, mes))
    
    dispositivos_para_testar = [dict(row) for row in c.fetchall()]
    print(f"Encontrados {len(dispositivos_para_testar)} dispositivos para testar em {mes}")
    
    conn.close()
    return dispositivos_para_testar

def verificar_estado_plano(cliente):
    """
    Função de depuração para verificar o estado atual do plano de manutenção de um cliente
    
    Parâmetros:
    cliente (str): Nome do cliente
    
    Retorna:
    dict: Informações sobre o estado do plano
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # Obter ID do cliente
    cliente_id = get_cliente_id(cliente)
    if not cliente_id:
        conn.close()
        return {"erro": "Cliente não encontrado"}
    
    # Verificar se a tabela existe
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plano_manutencao'")
    tabela_existe = c.fetchone()
    if not tabela_existe:
        conn.close()
        return {"erro": "Tabela plano_manutencao não existe"}
    
    # Verificar estrutura da tabela
    c.execute("PRAGMA table_info(plano_manutencao)")
    colunas = [col['name'] for col in c.fetchall()]
    
    # Contar registros
    c.execute("SELECT COUNT(*) FROM plano_manutencao WHERE cliente_id = ?", (cliente_id,))
    total_registros = c.fetchone()[0]
    
    # Distribuição por mês
    c.execute('''
    SELECT mes_manutencao, COUNT(*) FROM plano_manutencao 
    WHERE cliente_id = ? GROUP BY mes_manutencao
    ''', (cliente_id,))
    distribuicao = {row[0]: row[1] for row in c.fetchall()}
    
    conn.close()
    
    return {
        "tabela_existe": bool(tabela_existe),
        "colunas": colunas,
        "total_registros": total_registros,
        "distribuicao_por_mes": distribuicao
    }

def salvar_teste_dispositivos(cliente, mes, ano, df_resultados):
    """
    Salva os resultados dos testes de dispositivos no banco de dados.
    
    Parâmetros:
    - cliente: Nome do cliente
    - mes: Mês do teste (número)
    - ano: Ano do teste
    - df_resultados: DataFrame com os resultados [id_disp, status, observacao]
    
    Retorna:
    - True se os dados foram salvos com sucesso
    - False em caso de erro
    """
    try:
        # Garantir que a tabela existe
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se a tabela existe e criar se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS testes_dispositivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT,
                mes INTEGER,
                ano INTEGER,
                id_disp TEXT,
                status TEXT,
                observacao TEXT,
                data_teste TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Para cada dispositivo no DataFrame
        for _, row in df_resultados.iterrows():
            id_disp = row['id_disp']
            status = row['status']
            observacao = row['observacao']
            
            # Verificar se já existe um registro para este dispositivo/cliente/mês/ano
            cursor.execute('''
                SELECT id FROM testes_dispositivos 
                WHERE cliente = ? AND mes = ? AND ano = ? AND id_disp = ?
            ''', (cliente, mes, ano, id_disp))
            
            resultado = cursor.fetchone()
            
            if resultado:
                # Atualizar registro existente
                cursor.execute('''
                    UPDATE testes_dispositivos
                    SET status = ?, observacao = ?, data_teste = CURRENT_TIMESTAMP
                    WHERE cliente = ? AND mes = ? AND ano = ? AND id_disp = ?
                ''', (status, observacao, cliente, mes, ano, id_disp))
            else:
                # Inserir novo registro
                cursor.execute('''
                    INSERT INTO testes_dispositivos
                    (cliente, mes, ano, id_disp, status, observacao)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (cliente, mes, ano, id_disp, status, observacao))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erro ao salvar testes de dispositivos: {str(e)}")
        return False

def buscar_testes_dispositivos(cliente, mes, ano):
    """
    Busca os resultados de testes de dispositivos para um cliente/mês/ano.
    
    Parâmetros:
    - cliente: Nome do cliente
    - mes: Mês do teste (número)
    - ano: Ano do teste
    
    Retorna:
    - Lista de dicionários com os testes realizados [id_disp, status, observacao]
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='testes_dispositivos'
        ''')
        
        if not cursor.fetchone():
            # Se a tabela não existe, retorna lista vazia
            conn.close()
            return []
        
        # Buscar os testes para o cliente/mês/ano
        cursor.execute('''
            SELECT id_disp, status, observacao, data_teste
            FROM testes_dispositivos
            WHERE cliente = ? AND mes = ? AND ano = ?
        ''', (cliente, mes, ano))
        
        resultados = cursor.fetchall()
        conn.close()
        
        # Converter para lista de dicionários
        testes = []
        for resultado in resultados:
            teste = {
                'id_disp': resultado[0],
                'status': resultado[1],
                'observacao': resultado[2],
                'data_teste': resultado[3]
            }
            testes.append(teste)
        
        return testes
    
    except Exception as e:
        print(f"Erro ao buscar testes de dispositivos: {str(e)}")
        return [] 