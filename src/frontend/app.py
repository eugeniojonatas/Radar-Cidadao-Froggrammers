from flask import Flask, render_template, jsonify, request
import pymysql
import requests
import os

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

# =====================================================
# CONFIGURAÇÃO MYSQL
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
    os.environ.get("MYSQLPORT", 16652)
)

# =====================================================
# FUNÇÃO CONEXÃO MYSQL
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
# CONFIGURAÇÃO API CÂMARA
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

@app.route("/ranking.html")
def ranking():
    return render_template("ranking.html")

# =====================================================
# API - LISTA DE DEPUTADOS
# =====================================================

@app.route("/api/deputados")
def api_deputados():

    try:

        r = requests.get(
            f"{BASE_URL}/deputados?ordem=ASC&ordenarPor=nome",
            headers=HEADERS,
            timeout=10
        )

        return jsonify(r.json())

    except Exception as e:

        print("ERRO DEPUTADOS:", e)

        return jsonify({
            "dados": []
        })

# =====================================================
# API - PERFIL DO DEPUTADO
# =====================================================

@app.route("/api/deputado/<int:id_dep>")
def deputado_info(id_dep):

    try:

        response = requests.get(
            f"{BASE_URL}/deputados/{id_dep}",
            headers=HEADERS,
            timeout=10
        )

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

    except Exception as e:

        print("ERRO PERFIL:", e)

        return jsonify({

            "nome": "Erro",

            "partido": "-",

            "siglaPartido": "-",

            "uf": "-",

            "siglaUf": "-",

            "foto": "",

            "urlFoto": ""

        })

# =====================================================
# API - GASTOS
# =====================================================

@app.route("/api/gastos/<int:id_dep>")
def gastos(id_dep):

    try:

        lista = []

        anos = [2025, 2026]

        for ano in anos:

            pagina = 1

            while True:

                url = (
                    f"{BASE_URL}/"
                    f"deputados/{id_dep}/despesas"
                    f"?ano={ano}"
                    f"&pagina={pagina}"
                    f"&itens=100"
                )

                r = requests.get(
                    url,
                    headers=HEADERS,
                    timeout=10
                ).json()

                dados = r.get("dados", [])

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
# API - PRESENÇAS
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

                try:

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

                    dados = r.json().get("dados", [])

                    if not dados:
                        break

                    for evento in dados:

                        try:

                            detalhe = requests.get(

                                f"{BASE_URL}/eventos/{evento['id']}",

                                headers=HEADERS,

                                timeout=20

                            )

                            detalhe_json = detalhe.json().get("dados", {})

                            deputados = detalhe_json.get("deputados", [])

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

                        except Exception as erro_evento:

                            print(
                                "ERRO EVENTO:",
                                erro_evento
                            )

                    pagina += 1

                except Exception as erro_pagina:

                    print(
                        "ERRO PÁGINA:",
                        erro_pagina
                    )

                    break

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
# API - SALVAR FEEDBACK
# =====================================================

@app.route("/api/feedback", methods=["POST"])
def salvar_feedback():

    try:

        dados = request.get_json()

        deputado_id = dados.get("deputado_id")
        nome = dados.get("nome")
        nota = dados.get("nota")
        comentario = dados.get("comentario")

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO feedbacks
            (deputado_id, nome, nota, comentario)

            VALUES (%s, %s, %s, %s)
            """,
            (deputado_id, nome, nota, comentario)
        )

        conn.commit()

        cur.close()

        conn.close()

        return jsonify({
            "success": True,
            "message": "Feedback enviado!"
        })

    except Exception as e:

        print("ERRO FEEDBACK:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        })

# =====================================================
# API - LISTAR FEEDBACKS
# =====================================================

@app.route("/api/feedback/<int:id_dep>")
def feedbacks_deputado(id_dep):

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM feedbacks
            WHERE deputado_id = %s
            ORDER BY criado_em DESC
            """,
            (id_dep,)
        )

        feedbacks = cur.fetchall()

        cur.close()

        conn.close()

        return jsonify(feedbacks)

    except Exception as e:

        print("ERRO LISTAR FEEDBACKS:", e)

        return jsonify([])

@app.route("/api/rankings")
def rankings():

    try:

        tipo = request.args.get(
            "tipo",
            "avaliacoes"
        )

        # ===================================
        # RANKING DE AVALIAÇÕES
        # ===================================

        if tipo == "avaliacoes":

            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    deputado_id,
                    ROUND(AVG(nota),2) AS valor,
                    COUNT(*) AS total
                FROM feedbacks
                GROUP BY deputado_id
                ORDER BY valor DESC
                LIMIT 20
            """)

            dados = cur.fetchall()

            cur.close()
            conn.close()

        # ===================================
        # MAIS FEEDBACKS
        # ===================================

        elif tipo == "feedbacks":

            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    deputado_id,
                    COUNT(*) AS valor
                FROM feedbacks
                GROUP BY deputado_id
                ORDER BY valor DESC
                LIMIT 20
            """)

            dados = cur.fetchall()

            cur.close()
            conn.close()

        # ===================================
        # MAIORES GASTOS
        # ===================================

        elif tipo == "gastos":

            deputados = requests.get(
                f"{BASE_URL}/deputados",
                headers=HEADERS,
                timeout=20
            ).json()["dados"]

            ranking = []

            for dep in deputados:

                try:

                    total = 0

                    gastos = requests.get(
                        f"{BASE_URL}/deputados/{dep['id']}/despesas?ano=2025&itens=100",
                        headers=HEADERS,
                        timeout=10
                    ).json()

                    for g in gastos.get("dados", []):

                        total += float(
                            g.get("valorLiquido", 0)
                        )

                    ranking.append({
                        "deputado_id": dep["id"],
                        "valor": total
                    })

                except:
                    pass

            ranking.sort(
                key=lambda x: x["valor"],
                reverse=True
            )

            dados = ranking[:20]

        else:

            return jsonify([])

        resultado = []

        for dep in dados:

            try:

                response = requests.get(
                    f"{BASE_URL}/deputados/{dep['deputado_id']}",
                    headers=HEADERS,
                    timeout=10
                )

                info = response.json()["dados"]

                ultimo = info.get(
                    "ultimoStatus",
                    {}
                )

                if tipo == "avaliacoes":

                    valor_formatado = (
                        f"{dep['valor']} ⭐"
                    )

                elif tipo == "feedbacks":

                    valor_formatado = (
                        f"{dep['valor']} avaliações"
                    )

                else:

                    valor_formatado = (
                        f"R$ {dep['valor']:,.2f}"
                    )

                resultado.append({

                    "id": dep["deputado_id"],

                    "nome": info.get(
                        "nomeCivil",
                        "Desconhecido"
                    ),

                    "foto": ultimo.get(
                        "urlFoto",
                        ""
                    ),

                    "partido": ultimo.get(
                        "siglaPartido",
                        "-"
                    ),

                    "uf": ultimo.get(
                        "siglaUf",
                        "-"
                    ),

                    "valor": dep["valor"],

                    "valor_formatado":
                        valor_formatado

                })

            except Exception as erro:

                print(
                    "ERRO DEPUTADO:",
                    erro
                )

        return jsonify(resultado)

    except Exception as e:

        print(
            "ERRO RANKING:",
            e
        )

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
            "mensagem": "MySQL conectado com sucesso!"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "erro": str(e)
        })

# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
