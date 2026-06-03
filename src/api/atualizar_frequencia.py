import requests
import pymysql
import os

# Configurações do Banco
MYSQL_HOST = os.environ.get("MYSQLHOST", "23.22.106.224")
MYSQL_USER = os.environ.get("MYSQLUSER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQLPASSWORD", "321456Zion")
MYSQL_DATABASE = os.environ.get("MYSQLDATABASE", "api_backup")

def get_db_connection():
    return pymysql.connect(
        host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE, cursorclass=pymysql.cursors.DictCursor
    )

def atualizar_dados():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Busca todos os IDs válidos já existentes na tabela 'deputados' para evitar o erro de Chave Estrangeira (IntegrityError 1452)
    cur.execute("SELECT id FROM deputados")
    deputados_no_banco = cur.fetchall()
    
    # Cria um conjunto (set) de IDs para uma checagem ultra rápida por causa do DictCursor
    ids_validos = {row['id'] for row in deputados_no_banco}
    
    # 2. Puxar todos os eventos de 2026 com paginação
    print("Buscando todos os eventos de 2026...")
    url = "https://dadosabertos.camara.leg.br/api/v2/eventos?dataInicio=2026-01-01&dataFim=2026-12-31&itens=100"
    
    frequencia = {}
    total_eventos_processados = 0
    
    while url:
        response = requests.get(url).json()
        eventos = response.get("dados", [])
        
        for evento in eventos:
            total_eventos_processados += 1
            ev_id = evento['id']
            # Buscar presenças no evento
            url_presencas = f"https://dadosabertos.camara.leg.br/api/v2/eventos/{ev_id}/deputados"
            try:
                pres_res = requests.get(url_presencas).json()
                for dep in pres_res.get("dados", []):
                    d_id = dep['id']
                    frequencia[d_id] = frequencia.get(d_id, 0) + 1
            except:
                continue
        
        # Lógica para pegar o link da próxima página
        links = response.get("links", [])
        url = next((l['href'] for l in links if l['rel'] == 'next'), None)
        print(f"Processados {total_eventos_processados} eventos...")

    # 3. Atualizar no banco filtrando IDs inexistentes
    print(f"Salvando dados de {len(frequencia)} deputados no banco...")
    deputados_pulados = 0
    
    for d_id, presencas in frequencia.items():
        # SE O ID NÃO EXISTIR NA TABELA DE DEPUTADOS, PULA ELE SILENCIOSAMENTE
        if d_id not in ids_validos:
            deputados_pulados += 1
            continue
            
        faltas = total_eventos_processados - presencas
        cur.execute("""
            INSERT INTO frequencia (deputado_id, presencas, faltas)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            presencas = VALUES(presencas),
            faltas = VALUES(faltas)
        """, (d_id, presencas, faltas))
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Sucesso! Processados {total_eventos_processados} eventos no total.")
    if deputados_pulados > 0:
        print(f"Aviso: {deputados_pulados} deputados foram ignorados/pulados por não estarem na tabela 'deputados'.")

if __name__ == "__main__":
    atualizar_dados()