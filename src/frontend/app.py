from flask import Flask, render_template, jsonify
import requests

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

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

        r = requests.get(

            f"{BASE_URL}/deputados/{id_dep}",

            headers=HEADERS,

            timeout=10

        ).json()["dados"]

        return jsonify({

            "nome":
            r.get("nomeCivil", "Desconhecido"),

            "partido":
            r.get(
                "ultimoStatus",
                {}
            ).get(
                "siglaPartido",
                "-"
            ),

            "uf":
            r.get(
                "ultimoStatus",
                {}
            ).get(
                "siglaUf",
                "-"
            ),

            "foto":
            r.get(
                "ultimoStatus",
                {}
            ).get(
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
# API - GASTOS
# =====================================================

@app.route("/api/gastos/<int:id_dep>")
def gastos(id_dep):

    try:

        lista = []

        anos = [2026, 2025]

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

                dados = r.get(
                    "dados",
                    []
                )

                if not dados:
                    break

                lista.extend(dados)

                pagina += 1

                # proteção
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

        # ==========================================
        # 2025 + 2026
        # ==========================================

        for ano in [2025, 2026]:

            pagina = 1

            while True:

                try:

                    r = requests.get(

                        f"{BASE_URL}/eventos",

                        params={

                            "dataInicio":
                            f"{ano}-01-01",

                            "dataFim":
                            f"{ano}-12-31",

                            "pagina":
                            pagina,

                            "itens":
                            100

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

                    # ==================================
                    # EVENTOS
                    # ==================================

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

                                "evento_id":
                                evento["id"],

                                "descricao":
                                evento.get(
                                    "descricaoTipo",
                                    "Evento"
                                ),

                                "data":
                                evento.get(
                                    "dataHoraInicio"
                                ),

                                "status":
                                status

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

        # ==========================================
        # RETORNO
        # ==========================================

        return jsonify({

            "deputado_id":
            id_dep,

            "total_eventos":
            len(eventos),

            "total_presencas":
            total_presencas,

            "total_faltas":
            total_faltas,

            "eventos":
            eventos

        })

    except Exception as e:

        print("ERRO PRESENÇAS:", e)

        return jsonify({

            "deputado_id":
            id_dep,

            "total_eventos":
            0,

            "total_presencas":
            0,

            "total_faltas":
            0,

            "eventos":
            []

        })


# =====================================================
# RUN LOCAL
# =====================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )from flask import Flask, render_template, jsonify, request
from flask_mysqldb import MySQL
import requests

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
app.config['MYSQL_PASSWORD'] = '123456'  # <-- Garante que esta é a tua senha local
app.config['MYSQL_DB'] = 'radarcidadao'

# DictCursor faz com que o MySQL retorne dados como dicionários: {'coluna': valor}
# Isto é essencial para o correto funcionamento da rota de listagem de feedbacks abaixo
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# =====================================================
# CONFIGURAÇÃO DA API CÂMARA
# =====================================================
BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {
    "accept": "application/json"
}

# =====================================================
# PÁGINAS (ROTAS HTML)
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
        return jsonify({"dados": []})

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

        # Retorna mapeado com ambas nomenclaturas (com e sem 'sigla')
        # para garantir compatibilidade com qualquer versão do teu HTML front-end
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
        anos = [2026, 2025]

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
                r = requests.get(url, headers=HEADERS, timeout=10).json()
                dados = r.get("dados", [])

                if not dados:
                    break

                lista.extend(dados)
                pagina += 1

                if pagina > 50:  # Proteção de segurança contra loop infinito
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
                            presentes_ids = [d.get("id") for d in deputados]

                            status = "falta"
                            if id_dep in presentes_ids:
                                status = "presente"
                                total_presencas += 1
                            else:
                                total_faltas += 1

                            eventos.append({
