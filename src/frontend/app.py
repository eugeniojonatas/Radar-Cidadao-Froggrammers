from flask import Flask, render_template, jsonify, request
import pymysql
import requests
import os
from dotenv import load_dotenv  # 1. Importa o load_dotenv

# 2. Carrega as variáveis apontando para a pasta exata onde este arquivo está salvo
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

# =====================================================
# CONFIGURAÇÃO MYSQL (Buscando do .env)
# =====================================================

MYSQL_HOST = os.environ.get("MYSQLHOST")
MYSQL_USER = os.environ.get("MYSQLUSER")
MYSQL_PASSWORD = os.environ.get("MYSQLPASSWORD")
MYSQL_DATABASE = os.environ.get("MYSQLDATABASE")
MYSQL_PORT = int(os.environ.get("MYSQLPORT", 3306))

def get_db_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        port=MYSQL_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

# =====================================================
# CONFIGURAÇÃO API CÂMARA
# =====================================================

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}

# =====================================================
# PÁGINAS
# =====================================================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/deputados.html")
def deputados():
    return render_template("deputados.html")

@app.route("/perfil.html")
def perfil():
    return render_template("perfil.html")

@app.route("/relatorios.html")
def relatorios():
    return render_template("relatorios.html")

@app.route("/graficos.html")
def graficos():
    return render_template("graficos.html")

@app.route("/ranking.html")
def ranking():
    return render_template("ranking.html")

# =====================================================
# API - DEPUTADOS E PERFIL
# =====================================================

@app.route("/api/deputados")
def api_deputados():
    try:
        r = requests.get(f"{BASE_URL}/deputados?ordem=ASC&ordenarPor=nome", headers=HEADERS, timeout=10)
        return jsonify(r.json())
    except:
        return jsonify({"dados": []})

@app.route("/api/deputado/<int:id_dep>")
def deputado_info(id_dep):
    try:
        response = requests.get(f"{BASE_URL}/deputados/{id_dep}", headers=HEADERS, timeout=10)
        dados = response.json()["dados"]
        ultimo = dados.get("ultimoStatus", {})
        return jsonify({
            "nome": dados.get("nomeCivil", "Desconhecido"),
            "partido": ultimo.get("siglaPartido", "-"),
            "siglaPartido": ultimo.get("siglaPartido", "-"),
            "uf": ultimo.get("siglaUf", "-"),
            "siglaUf": ultimo.get("siglaUf", "-"),
            "foto": ultimo.get("urlFoto", ""),
            "urlFoto": ultimo.get("urlFoto", "")
        })
    except:
        return jsonify({"nome": "Erro", "partido": "-", "uf": "-", "foto": ""})

# =====================================================
# API - GASTOS E PRESENÇAS
# =====================================================

@app.route("/api/gastos/<int:id_dep>")
def gastos(id_dep):
    try:
        lista = []
        for ano in [2025, 2026]:
            pagina = 1
            while True:
                url = f"{BASE_URL}/deputados/{id_dep}/despesas?ano={ano}&pagina={pagina}&itens=100"
                r = requests.get(url, headers=HEADERS, timeout=10).json()
                dados = r.get("dados", [])
                if not dados: break
                lista.extend(dados)
                pagina += 1
                if pagina > 50: break
        return jsonify(lista)
    except:
        return jsonify([])

@app.route("/api/presencas/<int:id_dep>")
def presencas(id_dep):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT presencas, faltas FROM frequencia WHERE deputado_id = %s", (id_dep,))
        res = cur.fetchone()
        cur.close()
        conn.close()
        
        if res:
            return jsonify({
                "deputado_id": id_dep,
                "total_presencas": res['presencas'],
                "total_faltas": res['faltas']
            })
        return jsonify({"deputado_id": id_dep, "total_presencas": 0, "total_faltas": 0})
    except:
        return jsonify({"deputado_id": id_dep, "total_presencas": 0, "total_faltas": 0})

# =====================================================
# API - FEEDBACKS
# =====================================================

@app.route("/api/feedback", methods=["POST"])
def salvar_feedback():
    dados = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO feedbacks (deputado_id, nome, nota, comentario) VALUES (%s, %s, %s, %s)",
                (dados.get("deputado_id"), dados.get("nome"), dados.get("nota"), dados.get("comentario")))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/feedback/<int:id_dep>")
def feedbacks_deputado(id_dep):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM feedbacks WHERE deputado_id = %s ORDER BY criado_em DESC", (id_dep,))
    res = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(res)

# =====================================================
# API - RANKINGS (CORRIGIDO E SEPARADO)
# =====================================================
@app.route("/api/rankings")
def rankings():
    tipo = request.args.get("tipo", "maiores_gastos")

    queries = {
        "maiores_gastos": """
            SELECT d.id, d.nome, d.partido, d.uf, d.url_foto AS foto, SUM(g.valor) AS valor
            FROM deputados d
            INNER JOIN gastos g ON d.id = g.deputado_id
            GROUP BY d.id, d.nome, d.partido, d.uf, d.url_foto
            ORDER BY valor DESC LIMIT 10
        """,

        "menores_gastos": """
            SELECT d.id, d.nome, d.partido, d.uf, d.url_foto AS foto, SUM(g.valor) AS valor
            FROM deputados d
            INNER JOIN gastos g ON d.id = g.deputado_id
            GROUP BY d.id, d.nome, d.partido, d.uf, d.url_foto
            HAVING SUM(g.valor) > 0
            ORDER BY valor ASC LIMIT 10
        """,

        "presencas": """
            SELECT d.id, d.nome, d.partido, d.uf, d.url_foto AS foto, f.presencas AS valor
            FROM deputados d
            INNER JOIN frequencia f ON d.id = f.deputado_id
            ORDER BY f.presencas DESC LIMIT 10
        """,

        "faltas": """
            SELECT d.id, d.nome, d.partido, d.uf, d.url_foto AS foto, f.faltas AS valor
            FROM deputados d
            INNER JOIN frequencia f ON d.id = f.deputado_id
            ORDER BY f.faltas DESC LIMIT 10
        """,

        "avaliacoes": """
            SELECT d.id, d.nome, d.partido, d.uf, d.url_foto AS foto, IFNULL(AVG(fb.nota), 0) AS valor
            FROM deputados d
            LEFT JOIN feedbacks fb ON d.id = fb.deputado_id
            GROUP BY d.id, d.nome, d.partido, d.uf, d.url_foto
            ORDER BY valor DESC, d.nome ASC LIMIT 10
        """,

        "feedbacks": """
            SELECT d.id, d.nome, d.partido, d.uf, d.url_foto AS foto, COUNT(fb.id) AS valor
            FROM deputados d
            LEFT JOIN feedbacks fb ON d.id = fb.deputado_id
            GROUP BY d.id, d.nome, d.partido, d.uf, d.url_foto
            ORDER BY valor DESC, d.nome ASC LIMIT 10
        """
    }

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        sql = queries.get(tipo)

        if not sql:
            return jsonify([])

        cur.execute(sql)
        dados = cur.fetchall()

        resultado = []

        for d in dados:
            valor_num = float(d["valor"] or 0)

            if tipo in ["maiores_gastos", "menores_gastos"]:
                valor = f"R$ {valor_num:,.2f}"
                valor = valor.replace(",", "X").replace(".", ",").replace("X", ".")
            elif tipo == "feedbacks":  
                valor = f"{int(valor_num)} avaliações"
            elif tipo == "avaliacoes":
                valor = f"{valor_num:.2f}"
            else:
                valor = round(valor_num, 2)

            resultado.append({
                "id": d["id"],
                "nome": d["nome"],
                "partido": d["partido"],
                "uf": d["uf"],
                "foto": d["foto"],
                "valor": valor
            })

        cur.close()
        conn.close()

        return jsonify(resultado)

    except Exception as e:
        print("ERRO RANKING:", str(e))
        return jsonify({"erro": str(e)}), 500

# # =====================================================
# API - GRÁFICOS (EXCLUSIVO PARA O BANCO DE DADOS)
# =====================================================

@app.route("/api/graficos")
def graficos_camara_macro():
    try:
        tipo = request.args.get('tipo', 'maiores_categorias')
        ano = request.args.get('ano', 'todos')
        
        queries = {
            "maiores_categorias": """
                SELECT tipo_despesa AS rotulo, SUM(valor_liquido) AS total 
                FROM gastos_globais 
                {onde}
                GROUP BY tipo_despesa 
                ORDER BY total DESC LIMIT 5
            """,
            "menores_categorias": """
                SELECT tipo_despesa AS rotulo, SUM(valor_liquido) AS total 
                FROM gastos_globais 
                {onde}
                GROUP BY tipo_despesa 
                ORDER BY total ASC LIMIT 5
            """,
            "maiores_partidos": """
                SELECT partido AS rotulo, SUM(valor_liquido) AS total 
                FROM gastos_globais 
                {onde}
                GROUP BY partido 
                ORDER BY total DESC LIMIT 5
            """,
            "menores_partidos": """
                SELECT partido AS rotulo, SUM(valor_liquido) AS total 
                FROM gastos_globais 
                {onde}
                GROUP BY partido 
                ORDER BY total ASC LIMIT 5
            """
        }
        
        sql_base = queries.get(tipo)
        if not sql_base:
            return jsonify([])

        # Tratamento flexível: Filtra comparando string e inteiro, ou buscando em data_emissao se a coluna ano falhar
        if ano and ano != "todos":
            sql = sql_base.format(onde="WHERE ano = %s OR CAST(ano AS VARCHAR) = %s OR data_emissao LIKE %s")
            params = (int(ano), str(ano), f"{ano}%")
        else:
            sql = sql_base.format(onde="")
            params = ()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        dados = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(dados)
        
    except Exception as e:
        print("ERRO GRÁFICOS MACRO:", str(e))
        return jsonify([])
# =====================================================
# INICIALIZAÇÃO DO SERVIDOR
# =====================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
