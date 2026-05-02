from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

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

@app.route("/api/deputados")
def api_deputados():
    r = requests.get(
        "https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome"
    )
    return jsonify(r.json())

if __name__ == "__main__":
    app.run(debug=True)