from flask import Flask, jsonify, render_template, send_from_directory
import requests
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=base_dir,
    static_folder=base_dir,
    static_url_path=""
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/perfil.html")
def perfil():
    return render_template("perfil.html")

@app.route("/api/deputados")
def deputados():
    r = requests.get(
        "https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome"
    )
    return jsonify(r.json())

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(base_dir, filename)
