from flask import Flask, render_template, jsonify, request
import pymysql
import requests
import os

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

# =====================================================
# MYSQL
# =====================================================

MYSQL_HOST = os.environ.get(
    "MYSQLHOST",
    "zephyr.proxy.rlwy.net"
)

MYSQL_USER = os.environ.get(
    "MYSQLUSER",
    "root"
)

MYSQL_PASSWORD = os.environ.get(
    "MYSQLPASSWORD",
    "YQCodGzkWryGhRAlbnILnomXpHaClwca"
)

MYSQL_DATABASE = os.environ.get(
    "MYSQLDATABASE",
    "railway"
)

MYSQL_PORT = int(
    os.environ.get(
        "MYSQLPORT",
        16652
    )
)

# =====================================================
# CONEXÃO
# =====================================================

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
# CRIAR TABELA FEEDBACKS
# =====================================================

def criar_tabela_feedbacks():

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedbacks (

                id INT AUTO_INCREMENT PRIMARY KEY,

                deputado_id INT NOT NULL,

                nome VARCHAR(100),

                nota INT,

                comentario TEXT,

                criado_em TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

            )
        """)

        conn.commit()

        cur.close()
        conn.close()

    except Exception as e:

        print("ERRO AO CRIAR TABELA:", e)

# =====================================================
# API CÂMARA
# =====================================================

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

HEADERS = {
    "accept": "application/json"
}

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

# =====================================================
# LISTA DE DEPUTADOS
# =====================================================

@app.route("/api/deputados")
def api_deputados():

    try:

        r = requests.get(
            f"{BASE_URL}/deputados?ordem=ASC&ordenarPor=nome",
            headers=HEADERS,
            timeout=15
        )

        return jsonify(r.json())

    except Exception as e:

        print("ERRO DEPUTADOS:", e)

        return jsonify({
            "dados": []
        })

# =====================================================
# PERFIL
# =====================================================

@app.route("/api/deputado/<int:id_dep>")
def deputado_info(id_dep):

    try:

        response = requests.get(
            f"{BASE_URL}/deputados/{id_dep}",
            headers=HEADERS,
            timeout=15
        )

        dados = response.json()["dados"]

        ultimo = dados.get(
            "ultimoStatus",
            {}
        )

        return jsonify({

            "id": id_dep,

            "nome": dados.get(
                "nomeCivil",
                "Desconhecido"
            ),

            "partido": ultimo.get(
                "siglaPartido",
                "-"
            ),

            "siglaPartido": ultimo.get(
                "siglaPartido",
                "-"
            ),

            "uf": ultimo.get(
                "siglaUf",
                "-"
            ),

            "siglaUf": ultimo.get(
                "siglaUf",
                "-"
            ),

            "foto": ultimo.get(
                "urlFoto",
                ""
            ),

            "urlFoto": ultimo.get(
                "urlFoto",
                ""
            )

        })

    except Exception as e:

        print("ERRO PERFIL:", e)

        return jsonify({
            "nome": "Erro",
            "partido": "-",
            "uf": "-",
            "foto": ""
        })

# =====================================================
# PROPOSIÇÕES
# =====================================================

@app.route("/api/proposicoes/<int:id_dep>")
def proposicoes(id_dep):

    ano = request.args.get("ano", "2025")

    try:

        r = requests.get(

            f"{BASE_URL}/proposicoes",

            params={
                "idDeputadoAutor": id_dep,
                "ano": ano,
                "ordem": "DESC",
                "ordenarPor": "id"
            },

            headers=HEADERS,
            timeout=15
        )

        return jsonify(r.json())

    except Exception as e:

        print("ERRO PROPOSIÇÕES:", e)

        return jsonify({
            "dados": []
        })

# =====================================================
# GASTOS
# =====================================================

@app.route("/api/gastos/<int:id_dep>")
def gastos(id_dep):

    try:

        lista = []

        for ano in [2025, 2026]:

            pagina = 1

            while True:

                url = (
                    f"{BASE_URL}/deputados/"
                    f"{id_dep}/despesas"
                    f"?ano={ano}"
                    f"&pagina={pagina}"
                    f"&itens=100"
                )

                r = requests.get(
                    url,
                    headers=HEADERS,
                    timeout=15
                )

                dados = r.json().get(
                    "dados",
                    []
                )

                if not dados:
                    break

                lista.extend(dados)

                pagina += 1

                if pagina > 50:
                    break

        return jsonify(lista)

    except Exception as e:

        print("ERRO GASTOS:", e)

        return jsonify([])

# =====================================================
# PRESENÇAS
# =====================================================

@app.route("/api/presencas/<int:id_dep>")
def presencas(id_dep):

    try:

        eventos = []

        total_presencas = 0
        total_faltas = 0

        for ano in [2025, 2026]:

            pagina = 1

            while True:

                r = requests.get(

                    f"{BASE_URL}/eventos",

                    params={
                        "dataInicio": f"{ano}-01-01",
                        "dataFim": f"{ano}-12-31",
                        "pagina": pagina,
                        "itens": 100
                    },

                    headers=HEADERS,
                    timeout=20
                )

                dados = r.json().get(
                    "dados",
                    []
                )

                if not dados:
                    break

                for evento in dados:

                    try:

                        detalhe = requests.get(

                            f"{BASE_URL}/eventos/{evento['id']}",

                            headers=HEADERS,
                            timeout=20

                        )

                        detalhe_json = detalhe.json().get(
                            "dados",
                            {}
                        )

                        deputados = detalhe_json.get(
                            "deputados",
                            []
                        )

                        presentes_ids = [
                            d.get("id")
                            for d in deputados
                        ]

                        status = "falta"

                        if id_dep in presentes_ids:

                            status = "presente"
                            total_presencas += 1

                        else:

                            total_faltas += 1

                        eventos.append({

                            "evento_id": evento["id"],

                            "descricao": evento.get(
                                "descricaoTipo",
                                "Evento"
                            ),

                            "data": evento.get(
                                "dataHoraInicio"
                            ),

                            "status": status

                        })

                    except Exception:
                        pass

                pagina += 1

        return jsonify({

            "deputado_id": id_dep,

            "total_eventos": len(eventos),

            "total_presencas": total_presencas,

            "total_faltas": total_faltas,

            "eventos": eventos

        })

    except Exception as e:

        print("ERRO PRESENÇAS:", e)

        return jsonify({

            "deputado_id": id_dep,

            "total_eventos": 0,

            "total_presencas": 0,

            "total_faltas": 0,

            "eventos": []

        })

# =====================================================
# FEEDBACK
# =====================================================

@app.route("/api/feedback", methods=["POST"])
def salvar_feedback():

    try:

        dados = request.get_json()

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""

            INSERT INTO feedbacks
            (
                deputado_id,
                nome,
                nota,
                comentario
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )

        """, (

            dados.get("deputado_id"),
            dados.get("nome"),
            dados.get("nota"),
            dados.get("comentario")

        ))

        conn.commit()

        cur.close()
        conn.close()

        return jsonify({
            "success": True
        })

    except Exception as e:

        print("ERRO FEEDBACK:", e)

        return jsonify({
            "success": False,
            "erro": str(e)
        })

# =====================================================
# LISTAR FEEDBACKS
# =====================================================

@app.route("/api/feedback/<int:id_dep>")
def feedbacks_deputado(id_dep):

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""

            SELECT *
            FROM feedbacks

            WHERE deputado_id = %s

            ORDER BY criado_em DESC

        """, (id_dep,))

        feedbacks = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify(feedbacks)

    except Exception as e:

        print("ERRO LISTAR:", e)

        return jsonify([])

# =====================================================
# TESTE MYSQL
# =====================================================

@app.route("/teste-mysql")
def teste_mysql():

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT 1")

        resultado = cur.fetchone()

        cur.close()
        conn.close()

        return jsonify({

            "success": True,
            "resultado": resultado,
            "mensagem": "MySQL conectado com sucesso"

        })

    except Exception as e:

        return jsonify({

            "success": False,
            "erro": str(e)

        })

# =====================================================
# START
# =====================================================

criar_tabela_feedbacks()

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
