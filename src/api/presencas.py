from flask import Blueprint, jsonify
import requests

presencas_bp = Blueprint(
    "presencas",
    __name__
)

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

HEADERS = {
    "accept": "application/json"
}

# =====================================================
# API PRESENÇAS
# =====================================================

@presencas_bp.route(
    "/api/presencas/<int:dep_id>"
)
def buscar_presencas(dep_id):

    eventos = []

    total_presencas = 0

    total_faltas = 0

    # ==========================================
    # ANOS
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

                        if dep_id in presentes_ids:

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
                            "Erro evento:",
                            erro_evento
                        )

                pagina += 1

            except Exception as erro_pagina:

                print(
                    "Erro página:",
                    erro_pagina
                )

                break

    # ==========================================
    # RETORNO
    # ==========================================

    return jsonify({

        "deputado_id":
        dep_id,

        "total_eventos":
        len(eventos),

        "total_presencas":
        total_presencas,

        "total_faltas":
        total_faltas,

        "eventos":
        eventos

    })
