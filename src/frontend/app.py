from flask import Flask, render_template, jsonify, request
from flask_mysqldb import MySQL
import requests
import os

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

# =====================================================
# CONFIGURAÇÃO DO MYSQL
# =====================================================

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'radarcidadao'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

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
# API - FEEDBACKS
# =====================================================

@app.route("/api/feedback", methods=["POST"])
def salvar_feedback():

    try:

        dados = request.get_json()

        nome = dados.get("nome")
        mensagem = dados.get("mensagem")

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO feedbacks (nome, mensagem)
            VALUES (%s, %s)
            """,
            (nome, mensagem)
        )

        mysql.connection.commit()

        cur.close()

        return jsonify({
            "success": True,
            "message": "Feedback enviado!"
        })

    except Exception as e:

        print("ERRO FEEDBACK:", e)

        return jsonify({
            "success": False,
            "message": "Erro ao salvar feedback"
        })


@app.route("/api/feedbacks")
def listar_feedbacks():

    try:

        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT *
            FROM feedbacks
            ORDER BY id DESC
        """)

        feedbacks = cur.fetchall()

        cur.close()

        return jsonify(feedbacks)

    except Exception as e:

        print("ERRO LISTAR FEEDBACKS:", e)

        return jsonify([])


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
