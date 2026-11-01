"""Etapa 3: busca vídeos verticais grátis no Pexels (ou Pixabay) para cada cena."""
import random
from pathlib import Path

import requests

from . import config

RESERVAS = ["dramatic sky clouds", "desert sunset", "ancient ruins", "light rays clouds",
            "ocean waves storm", "candle flame dark", "mountains fog", "starry night sky"]


def _pexels(busca: str, usados: set) -> str | None:
    if not config.PEXELS_API_KEY:
        return None
    r = requests.get("https://api.pexels.com/videos/search", timeout=30,
                     headers={"Authorization": config.PEXELS_API_KEY},
                     params={"query": busca, "orientation": "portrait", "per_page": 15})
    if r.status_code != 200:
        print(f"Pexels HTTP {r.status_code} para '{busca}'")
        return None
    for video in r.json().get("videos", []):
        if video["id"] in usados or video.get("duration", 0) < 3:
            continue
        arquivos = [a for a in video.get("video_files", [])
                    if a.get("height") and a.get("width") and a["height"] >= a["width"]
                    and a.get("file_type") == "video/mp4"]
        if not arquivos:
            continue
        # O mais próximo de 1920 de altura, sem baixar arquivos gigantes (4K).
        melhor = min(arquivos, key=lambda a: abs(a["height"] - 1920))
        usados.add(video["id"])
        return melhor["link"]
    return None


def _pixabay(busca: str, usados: set) -> str | None:
    if not config.PIXABAY_API_KEY:
        return None
    r = requests.get("https://pixabay.com/api/videos/", timeout=30,
                     params={"key": config.PIXABAY_API_KEY, "q": busca, "per_page": 20,
                             "safesearch": "true"})
    if r.status_code != 200:
        print(f"Pixabay HTTP {r.status_code} para '{busca}'")
        return None
    for video in r.json().get("hits", []):
        if f"px{video['id']}" in usados:
            continue
        variantes = video.get("videos", {})
        for tam in ("large", "medium", "small"):
            if variantes.get(tam, {}).get("url"):
                usados.add(f"px{video['id']}")
                return variantes[tam]["url"]
    return None


def baixar_cena(busca: str, destino: Path, usados: set) -> Path | None:
    """Baixa um vídeo para a cena. Devolve None se nada for encontrado (vira fundo animado)."""
    tentativas = [busca, " ".join(busca.split()[:2]), random.choice(RESERVAS)]
    for termo in tentativas:
        for fonte in (_pexels, _pixabay):
            try:
                link = fonte(termo, usados)
            except requests.RequestException as e:
                print(f"Erro buscando '{termo}': {e}")
                link = None
            if link:
                with requests.get(link, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    with open(destino, "wb") as f:
                        for bloco in r.iter_content(1 << 20):
                            f.write(bloco)
                print(f"Cena '{busca}' -> {fonte.__name__[1:]} ('{termo}')")
                return destino
    print(f"Nenhum vídeo para '{busca}'; usando fundo animado.")
    return None
