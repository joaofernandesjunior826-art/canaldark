"""Etapa 2: narração grátis com as vozes neurais da Microsoft (edge-tts), cena por cena."""
import asyncio
import os
import ssl
import subprocess
import time
from pathlib import Path

import edge_tts
import edge_tts.communicate

from . import config

# Permite rodar atrás de proxy com certificado próprio (no GitHub não é necessário).
if os.environ.get("SSL_CERT_FILE"):
    edge_tts.communicate._SSL_CTX = ssl.create_default_context(cafile=os.environ["SSL_CERT_FILE"])


async def _narrar(texto: str, destino: Path) -> list[dict]:
    """Gera o mp3 e devolve as palavras com início/fim em segundos (para a legenda)."""
    com = edge_tts.Communicate(texto, config.VOZ, rate=config.VELOCIDADE_VOZ,
                               boundary="WordBoundary", proxy=os.environ.get("HTTPS_PROXY"))
    palavras = []
    with open(destino, "wb") as f:
        async for parte in com.stream():
            if parte["type"] == "audio":
                f.write(parte["data"])
            elif parte["type"] == "WordBoundary":
                ini = parte["offset"] / 1e7
                palavras.append({"texto": parte["text"], "ini": ini,
                                 "fim": ini + parte["duration"] / 1e7})
    return palavras


def _duracao(arq: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(arq)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _estimar_tempos(texto: str, duracao: float) -> list[dict]:
    """Se o serviço não mandar o tempo de cada palavra, distribui pelo tamanho das palavras."""
    palavras = texto.split()
    pesos = [len(p) + 2 for p in palavras]
    total, t, saida = sum(pesos), 0.05, []
    for p, peso in zip(palavras, pesos):
        d = max(duracao - 0.1, 0.5) * peso / total
        saida.append({"texto": p.strip(".,;:!?…\"'“”()"), "ini": t, "fim": t + d * 0.9})
        t += d
    return saida


def narrar(texto: str, destino: Path) -> list[dict]:
    ultimo_erro = None
    for tentativa in range(4):
        try:
            palavras = asyncio.run(_narrar(texto, destino))
            if destino.stat().st_size > 0:
                return palavras or _estimar_tempos(texto, _duracao(destino))
        except Exception as e:  # serviço não oficial: tenta de novo antes de desistir
            ultimo_erro = e
            print(f"edge-tts falhou (tentativa {tentativa + 1}): {e}")
        time.sleep(5 * (tentativa + 1))
    raise RuntimeError(f"A narração (edge-tts) não funcionou: {ultimo_erro}")
