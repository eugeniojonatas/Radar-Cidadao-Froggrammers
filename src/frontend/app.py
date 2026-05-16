from flask import Flask, render_template, jsonify
import requests

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

# =========================
# PÁGINAS
# =========================
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


# =========================
# API - LISTA DE DEPUTADOS
# =========================
@app.route("/api/deputados")
def api_deputados():
    try:
        r = requests.get(
            "https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome",
            timeout=10
        )

        return jsonify(r.json())

    except Exception as e:
        print("ERRO DEPUTADOS:", e)

        return jsonify({
            "dados": []
        })


# =========================
# API - PERFIL DO DEPUTADO
# =========================
@app.route("/api/deputado/<int:id_dep>")
def deputado_info(id_dep):
    try:
        r = requests.get(
            f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_dep}",
            timeout=10
        ).json()["dados"]

        return jsonify({
            "nome": r.get("nomeCivil", "Desconhecido"),
            "partido": r.get("ultimoStatus", {}).get("siglaPartido", "-"),
            "uf": r.get("ultimoStatus", {}).get("siglaUf", "-"),
            "foto": r.get("ultimoStatus", {}).get("urlFoto", "")
        })

    except Exception as e:
        print("ERRO PERFIL:", e)

        return jsonify({
            "nome": "Erro",
            "partido": "-",
            "uf": "-",
            "foto": ""
        })


# =========================
# API - GASTOS COMPLETOS
# =========================
@app.route("/api/gastos/<int:id_dep>")
def gastos(id_dep):
    try:
        lista = []

        anos = [2026, 2025]

        for ano in anos:

            pagina = 1

            while True:

                url = (
                    f"https://dadosabertos.camara.leg.br/api/v2/"
                    f"deputados/{id_dep}/despesas"
                    f"?ano={ano}&pagina={pagina}&itens=100"
                )

                r = requests.get(url, timeout=10).json()

                dados = r.get("dados", [])

                if not dados:
                    break

                lista.extend(dados)

                pagina += 1

                # proteção contra loop infinito
                if pagina > 50:
                    break

        return jsonify(lista)

    except Exception as e:
        print("ERRO GASTOS:", e)

        return jsonify([])


# =========================
# RUN LOCAL
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
