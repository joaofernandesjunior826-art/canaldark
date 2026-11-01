"""Memória da fábrica, guardada no próprio repositório (pasta dados/).

- historico.json: todos os vídeos feitos, com a situação de cada um (ver STATUS)
- estado.json: fila de pedidos, falhas do dia, vídeos de banco já usados e o que está configurado
- pedidos/: pedidos que chegam do painel (um arquivo por pedido, apagado depois de atendido)
"""
import json
from datetime import datetime

from . import config

ARQ_HISTORICO = config.DADOS / "historico.json"
ARQ_ESTADO = config.DADOS / "estado.json"
PASTA_PEDIDOS = config.DADOS / "pedidos"

STATUS = {
    "aguardando": "Aguardando aprovação",
    "aprovado": "Aprovado, pronto para postar",
    "programado": "Programado no YouTube",
    "publicado": "Publicado",
    "descartado": "Descartado",
    "substituido": "Substituído por uma versão nova",
}
# Reels do Instagram: "aguardando" = pronto para postar; "publicado" = já postado.


def agora() -> datetime:
    return datetime.now(config.FUSO)


def hoje() -> str:
    return agora().date().isoformat()


def _ler(arq, padrao):
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def _gravar(arq, dados) -> None:
    arq.parent.mkdir(parents=True, exist_ok=True)
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---- Histórico de vídeos ----------------------------------------------------
def historico() -> list[dict]:
    return _ler(ARQ_HISTORICO, [])


def adicionar_video(item: dict) -> None:
    lista = historico()
    lista.append(item)
    _gravar(ARQ_HISTORICO, lista)


def atualizar_video(video_id: str, **campos) -> dict | None:
    lista = historico()
    for v in lista:
        if v.get("id") == video_id:
            v.update(campos)
            _gravar(ARQ_HISTORICO, lista)
            return v
    return None


def achar_video(video_id: str) -> dict | None:
    return next((v for v in historico() if v.get("id") == video_id), None)


def achar_por_mensagem(mensagem_id: int) -> dict | None:
    return next((v for v in reversed(historico()) if mensagem_id in v.get("telegram", [])), None)


def ultimo_video() -> dict | None:
    lista = [v for v in historico() if v.get("tipo") not in ("teste", "instagram")]
    return lista[-1] if lista else None


# ---- Estado (fila, falhas, clipes usados, configuração) ---------------------
def ler_estado() -> dict:
    e = _ler(ARQ_ESTADO, {})
    e.setdefault("fila", [])
    e.setdefault("falhas", {"data": "", "n": 0})
    e.setdefault("clipes_usados", [])
    e.setdefault("config", {})
    return e


def salvar_estado(e: dict) -> None:
    e["clipes_usados"] = e["clipes_usados"][-600:]
    _gravar(ARQ_ESTADO, e)


def falhas_hoje(e: dict) -> int:
    return e["falhas"]["n"] if e["falhas"].get("data") == hoje() else 0


def registrar_falha(e: dict) -> int:
    n = falhas_hoje(e) + 1
    e["falhas"] = {"data": hoje(), "n": n, "quando": agora().isoformat(timespec="seconds")}
    return n


# ---- Pedidos do painel ------------------------------------------------------
def ler_pedidos_do_painel() -> list[tuple]:
    """Devolve [(arquivo, pedido)] em ordem de chegada. Arquivos com defeito são descartados."""
    if not PASTA_PEDIDOS.exists():
        return []
    saida = []
    for arq in sorted(PASTA_PEDIDOS.glob("*.json")):
        pedido = _ler(arq, None)
        if isinstance(pedido, dict) and pedido.get("acao"):
            saida.append((arq, pedido))
        else:
            arq.unlink(missing_ok=True)
    return saida
