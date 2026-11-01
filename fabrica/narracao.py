"""Etapa 2: narração grátis com as vozes neurais da Microsoft (edge-tts), cena por cena."""
import asyncio
import os
import ssl
import time
from pathlib import Path

import edge_tts
import edge_tts.communicate

from . import config

# Permite rodar atrás de proxy com certificado próprio (não é necessário no GitHub).
if os.environ.get("SSL_CERT_FILE"):
    edge_tts.communicate._SSL_CTX = ssl.create_default_context(cafile=os.environ["SSL_CERT_FILE"])


async def _narrar(texto: str, destino: Path) -> list[dict]:
    """Gera o mp3 e devolve as palavras com início/fim em segundos."""
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


def narrar(texto: str, destino: Path) -> list[dict]:
    for tentativa in range(4):
        try:
            palavras = asyncio.run(_narrar(texto, destino))
            if destino.stat().st_size > 0:
                return palavras
        except Exception as e:  # serviço não oficial: tenta de novo antes de desistir
            print(f"edge-tts falhou (tentativa {tentativa + 1}): {e}")
        time.sleep(5 * (tentativa + 1))
    raise RuntimeError("A narração (edge-tts) não funcionou.")
