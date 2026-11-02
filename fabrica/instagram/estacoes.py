"""As 8 estações quando o pedido é um Reels da Clover para o Instagram.

São os mesmos 8 passos do GitHub Actions dos Shorts (o painel mostra ao vivo), com outro trabalho:
  1 Pauta     escolhe o segmento (barbearia, academia...)
  2 Roteiro   o Gemini cria a marca fictícia e escreve o site e a legenda
  3 Narração  aqui vira a trilha: batida lo-fi gerada na hora (sem narração)
  4 Cenas     baixa as fotos e monta o site
  5 Montagem  desenha o notebook 3D e o cartão final da Clover
  6 Shorts    grava o site rolando na tela e monta o Reels de 20 s
  7 Thumbnail capa
  8 Agenda    guarda a prévia e avisa
"""
import hashlib
import json
import random
import shutil
import subprocess
from pathlib import Path

from .. import config, estado, github, telegram
from . import conceito, sites, trilha
from .gravacao import DURACAO, INICIO_FINAL, INICIO_SITE, Estudio

MARCA_CLOVER = config.RAIZ / "painel" / "marca.png"


def _semente(t: dict) -> int:
    return int(hashlib.sha1(t["id"].encode()).hexdigest()[:8], 16)


def _salvar(t: dict, nome: str, dados) -> None:
    Path(t["pasta"], nome).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def pauta(t: dict) -> None:
    tarefa = t["tarefa"]
    original = estado.achar_video(tarefa["origem"]) if tarefa.get("origem") else None
    segmentos, _ = conceito.recentes_do_historico(estado.historico())
    segmento = conceito.escolher_segmento(tarefa.get("tema") or (original or {}).get("segmento", ""), segmentos)
    t.update(segmento=segmento, ajuste=tarefa.get("ajuste", ""))
    t["gancho"] = list(conceito.gancho(_semente(t)))
    print(f"Pauta: Reels de um site para {segmento}")


def roteiro(t: dict) -> None:
    tarefa = t["tarefa"]
    if tarefa.get("exemplo") or not config.GEMINI_API_KEY:
        ficha = conceito.validar(conceito.ficha_exemplo(), "Barbearia")
        t["segmento"] = "Barbearia"
        print("Usando o site de exemplo (sem Gemini).")
    else:
        _, marcas = conceito.recentes_do_historico(estado.historico())
        ficha = conceito.gerar_ficha(t["segmento"], t.get("ajuste", ""), marcas)
    ficha["modelo"] = _modelo_da_vez(ficha.get("modelo"), _semente(t))
    t["ficha"] = ficha
    _salvar(t, "ficha.json", ficha)
    print(f"Conceito: {ficha['marca']} ({ficha['modelo']}, {ficha['fonte_titulo']})")


def _modelo_da_vez(preferido: str | None, semente: int) -> str:
    """Rodízio dos modelos de site: nunca repete nenhum dos últimos (todos os Reels ficam diferentes)."""
    reels = [v for v in estado.historico() if v.get("tipo") == "instagram"]
    recentes = [v.get("modelo") for v in reels[-(len(sites.MODELOS) - 1):]]
    if preferido in sites.MODELOS and preferido not in recentes:
        return preferido
    livres = [m for m in sites.MODELOS if m not in recentes] or sites.MODELOS
    return random.Random(semente).choice(livres)


def narracao(t: dict) -> None:
    arquivo = Path(t["pasta"], "trilha.wav")
    trilha.gerar(arquivo, DURACAO, entrada_bateria=INICIO_SITE, fim_bateria=INICIO_FINAL, semente=_semente(t))
    t["trilha"] = str(arquivo)
    print("Trilha lo-fi pronta (gerada na hora, sem direitos autorais).")


def cenas(t: dict) -> None:
    pasta = Path(t["pasta"])
    ficha = t["ficha"]
    imagens = conceito.baixar_imagens(ficha, pasta, conceito.busca_em_ingles(t["segmento"]))
    (pasta / "site.html").write_text(sites.montar_site(ficha, imagens), encoding="utf-8")
    t["imagens"] = imagens


def montagem(t: dict) -> None:
    pasta = Path(t["pasta"])
    if MARCA_CLOVER.exists():
        shutil.copy(MARCA_CLOVER, pasta / "marca.png")
    rnd = random.Random(_semente(t))
    paleta = sites.paleta(t["ficha"].get("cores", {}))
    lado = rnd.choice([-1, 1])
    opcoes = {
        "semente": _semente(t), "marca": "marca.png" if MARCA_CLOVER.exists() else "",
        "gancho1": t["gancho"][0], "gancho2": t["gancho"][1],
        "corTela": paleta["fundo"],
        "camera": {"az": lado * rnd.uniform(14, 22), "alt": rnd.uniform(11.5, 15), "fov": 38},
        "frase": "Seu site pode ser <em>assim</em>.",
        "cta": config.INSTAGRAM_CTA, "sub": config.INSTAGRAM_ARROBA or "link na bio",
    }
    estudio = Estudio(pasta)
    try:
        t["medidas"] = estudio.fotografar_cena(opcoes)
    finally:
        estudio.fechar()


def shorts(t: dict) -> None:
    pasta = Path(t["pasta"])
    estudio = Estudio(pasta)
    try:
        video = estudio.gravar(t["medidas"], Path(t["trilha"]) if t.get("trilha") else None, pasta / "reels.mp4")
    finally:
        estudio.fechar()
    t["short"] = str(video)
    t["duracao"] = DURACAO
    print(f"Reels pronto: {video.stat().st_size / 1e6:.1f} MB")


def thumbnail(t: dict) -> None:
    capa = Path(t["pasta"], "capa.jpg")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", "2.7", "-i", t["short"],
                    "-frames:v", "1", "-q:v", "3", str(capa)], check=True)
    t["capa"] = str(capa)


def agenda(t: dict, enviar: bool) -> None:
    ficha, tarefa = t["ficha"], t["tarefa"]
    item = {"id": t["id"], "tipo": "instagram", "status": "aguardando", "segmento": t["segmento"],
            "marca": ficha["marca"], "titulo": f"{ficha['marca']} · {t['segmento']}",
            "legenda": conceito.legenda_completa(ficha), "modelo": ficha["modelo"],
            "data": estado.agora().isoformat(timespec="seconds"), "duracao_seg": round(t["duracao"])}
    if tarefa.get("exemplo"):
        item["titulo"] = "[TESTE] " + item["titulo"]
    if t.get("ajuste"):
        item["ajuste"] = t["ajuste"]
    if tarefa.get("origem"):
        item["origem"] = tarefa["origem"]
    if not enviar:
        return
    if github.ativo():
        github.enviar_previas(t["id"], [(Path(t["short"]), "video/mp4"), (Path(t["capa"]), "image/jpeg")])
        item["previa"] = True
    item["telegram"] = telegram.avisar_reels(Path(t["short"]), item)
    estado.adicionar_video(item)
    if tarefa.get("origem"):
        estado.atualizar_video(tarefa["origem"], status="substituido", substituido_por=t["id"])


ESTACOES = {"pauta": pauta, "roteiro": roteiro, "narracao": narracao, "cenas": cenas,
            "montagem": montagem, "shorts": shorts, "thumbnail": thumbnail}
ROTULOS = {"pauta": "Pauta", "roteiro": "Roteiro", "narracao": "Trilha", "cenas": "Site",
           "montagem": "Notebook", "shorts": "Gravação", "thumbnail": "Capa", "agenda": "Entrega"}
