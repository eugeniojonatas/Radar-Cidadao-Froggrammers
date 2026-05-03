import requests
import json

def handler(request):
    try:
        url = "https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome"
        r = requests.get(url)
        data = r.json()

        deputados = data.get("dados", [])

        lista = []

        for d in deputados:
            lista.append({
                "id": d.get("id"),
                "nome": d.get("nome"),
                "partido": d.get("siglaPartido"),
                "uf": d.get("siglaUf"),
                "foto": d.get("urlFoto")
            })

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(lista, ensure_ascii=False)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "erro": "falha ao buscar dados",
                "detalhe": str(e)
            })
        }
