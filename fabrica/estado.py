"""Memória da fábrica, guardada no próprio repositório (pasta dados/).

- historico.json: todos os vídeos feitos (para não repetir história e para achar o que refazer)
- estado.json: fila de pedidos, falhas do dia e vídeos de banco já usados
"""
import json
from datetime import datetime

from . import config

ARQ_HISTORICO = config.DADOS / "historico.json"
ARQ_ESTADO = config.DADOS / "estado.json"


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


def achar_video(video_id: str) -> dict | None:
    return next((v for v in historico() if v.get("id") == video_id), None)


def achar_por_mensagem(mensagem_id: int) -> dict | None:
    return next((v for v in reversed(historico()) if mensagem_id in v.get("telegram", [])), None)


def ultimo_video() -> dict | None:
    lista = historico()
    return lista[-1] if lista else None


# ---- Estado (fila, falhas, clipes usados) -----------------------------------
def ler_estado() -> dict:
    e = _ler(ARQ_ESTADO, {})
    e.setdefault("fila", [])
    e.setdefault("falhas", {"data": "", "n": 0})
    e.setdefault("clipes_usados", [])
    return e


def salvar_estado(e: dict) -> None:
    e["clipes_usados"] = e["clipes_usados"][-600:]
    _gravar(ARQ_ESTADO, e)


def falhas_hoje(e: dict) -> int:
    return e["falhas"]["n"] if e["falhas"].get("data") == hoje() else 0


def registrar_falha(e: dict) -> int:
    n = falhas_hoje(e) + 1
    e["falhas"] = {"data": hoje(), "n": n}
    return n
