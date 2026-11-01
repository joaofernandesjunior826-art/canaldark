"""Guarda os vídeos prontos no próprio GitHub (numa "release" chamada previas), para o painel
mostrar e para baixar na hora de postar. Usa o token que o GitHub Actions já fornece."""
from pathlib import Path

import requests

from . import config

API = "https://api.github.com"


def ativo() -> bool:
    return bool(config.GITHUB_TOKEN and config.GITHUB_REPOSITORY)


def _cabecalhos(extra: dict | None = None) -> dict:
    h = {"Authorization": f"Bearer {config.GITHUB_TOKEN}", "Accept": "application/vnd.github+json",
         "X-GitHub-Api-Version": "2022-11-28"}
    h.update(extra or {})
    return h


def _release() -> dict:
    """Busca (ou cria) a release onde ficam as prévias."""
    url = f"{API}/repos/{config.GITHUB_REPOSITORY}/releases/tags/{config.RELEASE_PREVIAS}"
    r = requests.get(url, headers=_cabecalhos(), timeout=30)
    if r.status_code == 200:
        return r.json()
    if r.status_code != 404:
        r.raise_for_status()
    r = requests.post(f"{API}/repos/{config.GITHUB_REPOSITORY}/releases", headers=_cabecalhos(), timeout=30,
                      json={"tag_name": config.RELEASE_PREVIAS, "name": "Prévias da fábrica",
                            "body": "Vídeos feitos pela fábrica, para o painel mostrar. Gerado automaticamente.",
                            "prerelease": True})
    r.raise_for_status()
    return r.json()


def _todos_assets(release: dict) -> list[dict]:
    assets, pagina = [], 1
    while True:
        r = requests.get(f"{API}/repos/{config.GITHUB_REPOSITORY}/releases/{release['id']}/assets",
                         headers=_cabecalhos(), params={"per_page": 100, "page": pagina}, timeout=30)
        r.raise_for_status()
        lote = r.json()
        assets += lote
        if len(lote) < 100:
            return assets
        pagina += 1


def enviar_previas(video_id: str, arquivos: list[tuple[Path, str]]) -> None:
    """arquivos: [(caminho, tipo)] -> sobem como <video_id>.mp4 / <video_id>.jpg."""
    release = _release()
    existentes = {a["name"]: a for a in _todos_assets(release)}
    for caminho, tipo in arquivos:
        nome = f"{video_id}{caminho.suffix}"
        if nome in existentes:
            requests.delete(existentes[nome]["url"], headers=_cabecalhos(), timeout=30)
        with open(caminho, "rb") as f:
            r = requests.post(
                f"https://uploads.github.com/repos/{config.GITHUB_REPOSITORY}/releases/{release['id']}/assets",
                headers=_cabecalhos({"Content-Type": tipo}), params={"name": nome}, data=f, timeout=600)
        r.raise_for_status()
        print(f"Prévia guardada: {nome}")


def baixar_previa(nome: str, destino: Path) -> Path:
    release = _release()
    asset = next((a for a in _todos_assets(release) if a["name"] == nome), None)
    if not asset:
        raise RuntimeError(f"Não achei a prévia {nome} no GitHub.")
    with requests.get(asset["url"], headers=_cabecalhos({"Accept": "application/octet-stream"}),
                      stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(destino, "wb") as f:
            for bloco in r.iter_content(1 << 20):
                f.write(bloco)
    return destino


def limpar_previas(manter: set[str]) -> None:
    """Apaga prévias de vídeos que não estão mais em uso (mantém os ids informados)."""
    try:
        release = _release()
        for asset in _todos_assets(release):
            if asset["name"].rsplit(".", 1)[0] not in manter:
                requests.delete(asset["url"], headers=_cabecalhos(), timeout=30)
                print(f"Prévia antiga apagada: {asset['name']}")
    except requests.RequestException as e:
        print(f"Não consegui limpar prévias antigas: {e}")
