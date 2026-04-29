import requests

def handler(request):
    try:
        r = requests.get(
            "https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome"
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": r.text
        }

    except:
        return {
            "statusCode": 500,
            "body": '{"erro": "falha ao buscar dados"}'
        }
