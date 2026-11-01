"""Pinturas clássicas de domínio público (Wikimedia Commons) para o fundo das cenas.
Grátis, sem chave e ligadas à própria história (Caravaggio, Rembrandt, Tissot, Doré...).

A Wikimedia limita pedidos seguidos, então a galeria pede com calma: guarda as buscas, espera
entre pedidos, respeita o "tente mais tarde" (erro 429) e usa só tamanhos de imagem padrão."""
import random
import time
from pathlib import Path

import requests

API = "https://commons.wikimedia.org/w/api.php"
CABECALHO = {"User-Agent": "CloverFabricaDeShorts/1.0 (https://github.com/joaofernandesjunior826-art/canaldark)"}
LARGURA_PADRAO = 1920  # um dos tamanhos padrão da Wikimedia (outros tamanhos são recusados)
LICENCAS_LIVRES = ("public domain", "cc0", "pdm")
# Evita imagens violentas demais para o YouTube (ex.: cabeças cortadas) e coisas que não são pinturas.
PALAVRAS_EVITADAS = ("head of", "beheading", "decapit", "severed", "cabeza", "tête", "testa di", "kopf",
                     "photograph", "photo of", "museum", "map of", "manuscript", "coin", "stamp", "sculpture",
                     "statue", "relief", "logo", "corpse", "massacre", "slaughter", "flaying")


class Galeria:
    def __init__(self, evitar: set):
        self.evitar = evitar          # chaves já usadas (neste vídeo e nos anteriores)
        self.buscas: dict[str, list] = {}
        self.ultimo_pedido = 0.0

    def _pedir(self, url: str, **kwargs) -> requests.Response:
        for tentativa in range(4):
            espera = 1.2 - (time.monotonic() - self.ultimo_pedido)
            if espera > 0:
                time.sleep(espera)
            self.ultimo_pedido = time.monotonic()
            r = requests.get(url, headers=CABECALHO, timeout=60, **kwargs)
            if r.status_code == 429 or r.status_code >= 500:
                pausa = r.headers.get("Retry-After", "")
                time.sleep(min(int(pausa) if pausa.isdigit() else 6 * (tentativa + 1), 40))
                continue
            r.raise_for_status()
            return r
        r.raise_for_status()
        return r

    def buscar(self, termo: str) -> list[dict]:
        if termo in self.buscas:
            return self.buscas[termo]
        params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                  "gsrlimit": 25, "gsrsearch": f"{termo} filetype:bitmap",
                  "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": LARGURA_PADRAO}
        paginas = sorted(self._pedir(API, params=params).json().get("query", {}).get("pages", {}).values(),
                         key=lambda p: p.get("index", 0))
        candidatos = []
        for p in paginas:
            info = (p.get("imageinfo") or [{}])[0]
            licenca = info.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "").lower()
            titulo = p.get("title", "").lower()
            if (not any(l in licenca for l in LICENCAS_LIVRES)
                    or any(palavra in titulo for palavra in PALAVRAS_EVITADAS)
                    or min(info.get("width", 0), info.get("height", 0)) < 900):
                continue
            candidatos.append({"chave": f"commons:{p.get('pageid')}", "url": info.get("thumburl") or info.get("url"),
                               "retrato": info["height"] >= info["width"] * 0.9})
        # Pinturas em pé combinam melhor com o vídeo vertical; sorteia entre as melhores para variar.
        candidatos.sort(key=lambda c: not c["retrato"])
        melhores = candidatos[:6]
        random.shuffle(melhores)
        self.buscas[termo] = melhores + candidatos[6:]
        return self.buscas[termo]

    def baixar(self, termos: list[str], destino: Path) -> str | None:
        """Tenta os termos em ordem e baixa a primeira pintura nova. Devolve a chave dela."""
        for termo in dict.fromkeys(t for t in termos if t):
            try:
                candidatos = [c for c in self.buscar(termo) if c["chave"] not in self.evitar]
            except (requests.RequestException, ValueError) as e:
                print(f"Wikimedia: busca '{termo}' falhou: {e}")
                continue
            for c in candidatos[:3]:
                try:
                    destino.write_bytes(self._pedir(c["url"]).content)
                except requests.RequestException as e:
                    print(f"Wikimedia: download falhou: {e}")
                    continue
                if destino.stat().st_size > 30_000:
                    self.evitar.add(c["chave"])
                    print(f"Pintura '{termo}': {c['chave']}")
                    return c["chave"]
        return None
