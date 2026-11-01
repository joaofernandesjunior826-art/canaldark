"""Busca as chaves guardadas no cofre do painel (criptografadas) para esta execução da fábrica.

A fábrica se identifica com um token OIDC assinado pelo GitHub; o painel confere que o pedido vem
deste repositório e só então devolve as chaves. Os valores ficam mascarados nos registros e vão
para as próximas etapas como PAINEL_<NOME>. Um Secret do GitHub com o mesmo nome tem prioridade."""
import json
import os

import requests

from . import config

ARQUIVO = config.DADOS / "chaves.json"
AUDIENCIA = "clover-fabrica"


def carregar() -> None:
    url_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    pedido_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    destino = os.environ.get("GITHUB_ENV")
    if not (url_token and pedido_token and destino):
        print("Fora do GitHub Actions: usando só as variáveis de ambiente.")
        return
    try:
        cofre = json.loads(ARQUIVO.read_text(encoding="utf-8")) if ARQUIVO.exists() else {}
        jwt = requests.get(f"{url_token}&audience={AUDIENCIA}", timeout=30,
                           headers={"Authorization": f"Bearer {pedido_token}"}).json()["value"]
        r = requests.post(f"{config.PAINEL_URL}/api/fabrica-chaves", timeout=30,
                          json={"chaves": cofre.get("chaves", {})}, headers={"Authorization": f"Bearer {jwt}"})
        r.raise_for_status()
        resposta = r.json()
    except Exception as erro:  # sem cofre a fábrica segue com os Secrets do GitHub
        print(f"Não consegui abrir o cofre do painel: {erro}")
        return
    carregadas = []
    with open(destino, "a", encoding="utf-8") as f:
        for nome, valor in resposta.get("chaves", {}).items():
            if not valor or "\n" in valor or os.environ.get(nome):
                continue
            print(f"::add-mask::{valor}")
            f.write(f"PAINEL_{nome}={valor}\n")
            carregadas.append(nome)
    print("Chaves do cofre:", ", ".join(carregadas) or "nenhuma")
    if resposta.get("falhas"):
        print("Chaves que não abriram (cole de novo no painel):", ", ".join(resposta["falhas"]))
