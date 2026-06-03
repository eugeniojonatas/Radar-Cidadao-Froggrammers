import pymysql
import requests

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}

# Ajuste com as credenciais do seu MySQL de desenvolvimento local
def get_local_db():
    return pymysql.connect(
        host="localhost",
        user="root",          # Seu usuário do MySQL local
        password="321456Zion", # Sua senha do MySQL local
        database="api",
        cursorclass=pymysql.cursors.DictCursor
    )

def processar_rankings_para_o_banco():
    print("🚀 Buscando deputados na API...")
    try:
        r = requests.get(f"{BASE_URL}/deputados?ordem=ASC&ordenarPor=nome", headers=HEADERS, timeout=20)
        deputados = r.json().get("dados", [])
    except Exception as e:
        print(f"Erro ao acessar API: {e}")
        return

    print(f"📊 Processando dados de {len(deputados)} deputados. Aguarde...")
    
    # Conecta no banco local
    conn = get_local_db()
    cur = conn.cursor()

    for idx, dep in enumerate(deputados):
        id_dep = dep["id"]
        nome = dep["nome"]
        partido = dep["siglaPartido"]
        uf = dep["siglaUf"]
        foto = dep["urlFoto"]
        
        # --- CALCULAR GASTOS (ANO RECENTE Ex: 2025/2026) ---
        total_gastos = 0.0
        try:
            # Puxa a primeira página de despesas para o ranking
            g_res = requests.get(f"{BASE_URL}/deputados/{id_dep}/despesas?ano=2025&itens=100", headers=HEADERS, timeout=10).json()
            for g in g_res.get("dados", []):
                total_gastos += float(g.get("valorLiquido", 0))
        except Exception:
            pass

        # --- CALCULAR PRESENÇAS DE FORMA SIMPLIFICADA PARA O RANKING ---
        # Como as páginas internas continuam puxando tudo da API, aqui fazemos um cálculo 
        # mais direto ou você pode deixar zerado se focar o ranking apenas em gastos.
        # Para fins de ranking, vamos registrar o gasto calculado:
        
        sql = """
            INSERT INTO ranking_local (id_deputado, nome, partido, uf, url_foto, total_gastos)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                nome = VALUES(nome),
                partido = VALUES(partido),
                uf = VALUES(uf),
                url_foto = VALUES(url_foto),
                total_gastos = VALUES(total_gastos)
        """
        cur.execute(sql, (id_dep, nome, partido, uf, foto, total_gastos))
        
        if idx % 50 == 0:
            print(f"Progresso: {idx}/{len(deputados)} deputados processados...")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Rankings salvos com sucesso no seu MySQL local!")

if __name__ == "__main__":
    processar_rankings_para_o_banco()
