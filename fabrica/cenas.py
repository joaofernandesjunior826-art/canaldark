"""Etapa 3: busca vídeos verticais grátis no Pexels (ou Pixabay) para cada cena."""
import random
from pathlib import Path

import requests

from . import config

RESERVAS = ["dramatic sky clouds", "desert sunset", "ancient ruins", "light rays clouds",
            "ocean waves storm", "candle flame dark", "mountains fog", "starry night sky",
            "wheat field wind", "old stone wall", "sunrise over hills", "river flowing rocks"]


def _pexels(busca: str, evitar: set, min_dur: float) -> list[tuple[bool, str, str]]:
    if not config.PEXELS_API_KEY:
        return []
    r = requests.get("https://api.pexels.com/videos/search", timeout=30,
                     headers={"Authorization": config.PEXELS_API_KEY},
                     params={"query": busca, "orientation": "portrait", "size": "medium", "per_page": 30})
    if r.status_code != 200:
        print(f"Pexels HTTP {r.status_code} para '{busca}'")
        return []
    candidatos = []
    for video in r.json().get("videos", []):
        chave = f"pexels:{video['id']}"
        if chave in evitar:
            continue
        arquivos = [a for a in video.get("video_files", [])
                    if a.get("height") and a.get("width") and a["height"] > a["width"]
                    and a.get("file_type") == "video/mp4" and a.get("link")]
        if arquivos:
            # O mais perto de 1920 de altura: boa qualidade sem baixar arquivos 4K enormes.
            melhor = min(arquivos, key=lambda a: abs(a["height"] - 1920))
            candidatos.append((video.get("duration", 0) >= min_dur, chave, melhor["link"]))
    return candidatos


def _pixabay(busca: str, evitar: set, min_dur: float) -> list[tuple[bool, str, str]]:
    if not config.PIXABAY_API_KEY:
        return []
    r = requests.get("https://pixabay.com/api/videos/", timeout=30,
                     params={"key": config.PIXABAY_API_KEY, "q": busca[:100], "per_page": 30,
                             "video_type": "film", "safesearch": "true"})
    if r.status_code != 200:
        print(f"Pixabay HTTP {r.status_code} para '{busca}'")
        return []
    candidatos = []
    for video in r.json().get("hits", []):
        chave = f"pixabay:{video['id']}"
        if chave in evitar:
            continue
        variantes = video.get("videos", {})
        # 4K fica mais nítido no recorte vertical; se o arquivo for enorme, usa o Full HD.
        for tamanho in ("large", "medium", "small"):
            v = variantes.get(tamanho) or {}
            if v.get("url") and (tamanho != "large" or 0 < v.get("size", 0) < 70_000_000):
                candidatos.append((video.get("duration", 0) >= min_dur, chave, v["url"]))
                break
    return candidatos


def _baixar(url: str, destino: Path) -> bool:
    try:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(destino, "wb") as f:
                for bloco in r.iter_content(1 << 20):
                    f.write(bloco)
        return destino.stat().st_size > 100_000
    except requests.RequestException as e:
        print(f"Download falhou: {e}")
        return False


def baixar_cena(busca: str, destino: Path, evitar: set, min_dur: float) -> str | None:
    """Baixa um vídeo para a cena e devolve a chave dele (para não repetir em outros vídeos).
    Devolve None se nada for encontrado; a cena vira um fundo animado."""
    termos = [busca, " ".join(busca.split()[:2]), random.choice(RESERVAS)]
    for termo in dict.fromkeys(termos):
        for fonte in (_pexels, _pixabay):
            try:
                candidatos = fonte(termo, evitar, min_dur)
            except (requests.RequestException, ValueError) as e:
                print(f"Erro buscando '{termo}': {e}")
                continue
            # Prefere vídeos que cobrem a cena inteira e sorteia entre os melhores (mais variedade).
            melhores = ([c for c in candidatos if c[0]] or candidatos)[:6]
            random.shuffle(melhores)
            for _, chave, url in melhores:
                if _baixar(url, destino):
                    evitar.add(chave)
                    print(f"Cena '{busca}': {chave} (busca '{termo}')")
                    return chave
    print(f"Nenhum vídeo para '{busca}'; usando fundo animado.")
    return None
