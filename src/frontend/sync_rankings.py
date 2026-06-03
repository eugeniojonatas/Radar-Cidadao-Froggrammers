import os
import sys
import time
import requests
import pymysql
from concurrent.futures import ThreadPoolExecutor, as_completed

# =====================================================
# CONFIGURAÇÃO DE TESTE VS PRODUÇÃO
# =====================================================
MODO_TESTE = False  

# =====================================================
# CREDENCIAIS DIRETAS DA SUA EC2
# =====================================================
MYSQL_HOST = "54.164.64.84"
MYSQL_USER = "root"
MYSQL_PASSWORD = "321456Zion"
MYSQL_DATABASE = "api"
MYSQL_PORT = 3306 

def get_db_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        port=MYSQL_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}

def inicializar_tabela():
    """Garante que a tabela existe e possui todas as colunas necessárias na EC2."""
    print("Checking database structure and columns...")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ranking_local (
                id_deputado INT PRIMARY KEY,
                nome VARCHAR(255),
                partido VARCHAR(50),
                uf VARCHAR(10),
                url_foto VARCHAR(500)
            );
        """)
        conn.commit()
        
        colunas_necessarias = [
            ("total_gastos", "DECIMAL(15,2) DEFAULT 0.00"),
            ("total_presencas", "INT DEFAULT 0"),
            ("total_faltas", "INT DEFAULT 0")
        ]
        
        for coluna, tipo in colunas_necessarias:
            try:
                cur.execute(f"ALTER TABLE ranking_local ADD COLUMN {coluna} {tipo};")
                conn.commit()
            except Exception as e:
                if "1060" in str(e) or "Duplicate column" in str(e):
                    pass
                else:
                    print(f"  ⚠️ Alerta na coluna {coluna}: {e}")
                    
        cur.close()
        conn.close()
        print("Database structure verified successfully!\n")
    except Exception as e:
        print(f"❌ Erro crítico na inicialização do banco: {e}")
        sys.exit(1)

def processar_um_deputado(dep, idx, total):
    """Busca os gastos de um único deputado e salva no banco de dados."""
    id_dep = dep["id"]
    nome = dep["nome"]
    partido = dep["siglaPartido"]
    uf = dep["siglaUf"]
    foto = dep["urlFoto"]
    
    soma_gastos = 0.0
    erro_api = False
    
    # Consulta os anos de 2025 e 2026 na API da Câmara
    for ano in [2025, 2026]:
        if erro_api:
            break
        pagina = 1
        while True:
            url = f"{BASE_URL}/deputados/{id_dep}/despesas?ano={ano}&pagina={pagina}&itens=100"
            try:
                resp = requests.get(url, headers=HEADERS, timeout=10).json()
                dados_despesas = resp.get("dados", [])
                if not dados_despesas:
                    break
                
                for desp in dados_despesas:
                    soma_gastos += float(desp.get("valorLiquido", 0) or 0)
                    
                pagina += 1
                if pagina > 15:
                    break
            except Exception as e:
                erro_api = True
                break
                
    if erro_api:
        return f"[{idx}/{total}] ❌ {nome} ignorado por instabilidade na API."

    # Salva o resultado no banco da EC2 de forma isolada nesta thread
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        sql = """
            INSERT INTO ranking_local (id_deputado, nome, partido, uf, url_foto, total_gastos, total_presencas, total_faltas)
            VALUES (%s, %s, %s, %s, %s, %s, 12, 1) 
            ON DUPLICATE KEY UPDATE
                nome = VALUES(nome),
                partido = VALUES(partido),
                uf = VALUES(uf),
                url_foto = VALUES(url_foto),
                total_gastos = VALUES(total_gastos);
        """
        cur.execute(sql, (id_dep, nome, partido, uf, foto, soma_gastos))
        conn.commit()
        cur.close()
        conn.close()
        return f"[{idx}/{total}] ✅ {nome} ({partido}-{uf}) atualizado: R$ {soma_gastos:,.2f}"
    except Exception as e:
        return f"[{idx}/{total}] ❌ Erro de banco ao salvar {nome}: {e}"

def sincronizar_dados():
    inicializar_tabela()
    
    print("Fetching active deputies from Chamber API...")
    try:
        r = requests.get(f"{BASE_URL}/deputados?ordem=ASC&ordenarPor=nome", headers=HEADERS, timeout=15)
        deputados = r.json().get("dados", [])
    except Exception as e:
        print(f"❌ Error fetching deputies list: {e}")
        return

    if MODO_TESTE:
        print("⚠️ MODO_TESTE ATIVO: Limitando a carga aos 10 primeiros deputados.")
        deputados = deputados[:10]

    total_deputados = len(deputados)
    print(f"Starting parallel sync for {total_deputados} deputies using 10 parallel workers...\n")

    # Dispara a execução paralela (max_workers=10 processa 10 deputados simultaneamente)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(processar_um_deputado, dep, idx, total_deputados) 
            for idx, dep in enumerate(deputados, 1)
        ]
        
        for future in as_completed(futures):
            # Imprime o resultado assim que cada thread terminar sua tarefa
            print(future.result())

    print("\n🎉 Parallel synchronization cycle completed successfully!")

if __name__ == "__main__":
    sincronizar_dados()