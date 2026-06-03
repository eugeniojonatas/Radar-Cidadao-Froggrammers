import requests
import json

def handler(request):
    try:
        id_dep = request.query.get("id")

        if not id_dep:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"erro": "id não informado"})
            }

        todos = []

        for ano in [2025, 2026]:
            pagina = 1

            while True:
                url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_dep}/despesas?ano={ano}&pagina={pagina}&itens=100"

                res = requests.get(url)
                data = res.json()
                lista = data.get("dados", [])

                if not lista:
                    break

                for g in lista:
                    todos.append({
                        "data": g.get("dataDocumento"),
                        "tipo": g.get("tipoDespesa"),
                        "valor": g.get("valorDocumento", 0)
                    })

                pagina += 1

        todos.sort(
            key=lambda x: x["data"] if x["data"] else "",
            reverse=True
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(todos, ensure_ascii=False)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "erro": "falha ao buscar gastos",
                "detalhe": str(e)
            })
        }
