"""Roda a fábrica inteira: python -m fabrica

Opções:
  --historia "Davi e Golias"   força uma história específica (precisa estar em dados/historias.txt)
  --sem-enviar                 só gera o vídeo, sem YouTube/Telegram
"""
import argparse
import json
import sys
import traceback
from datetime import datetime, timezone

from . import cenas, config, montagem, narracao, publicar, roteiro


def produzir(historia: str | None, enviar: bool) -> None:
    if historia:
        linhas = (config.DADOS / "historias.txt").read_text(encoding="utf-8").splitlines()
        achada = next((l for l in linhas if l.split("|")[0].strip().lower() == historia.lower()), None)
        if not achada:
            sys.exit(f"História '{historia}' não está em dados/historias.txt")
        titulo, ref = (p.strip() for p in achada.split("|"))
    else:
        titulo, ref = roteiro.proxima_historia()
    print(f"== História: {titulo} ({ref})")

    carimbo = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    pasta = (config.SAIDA / carimbo).resolve()
    pasta.mkdir(parents=True, exist_ok=True)

    print("== 1/5 Roteiro")
    texto = roteiro.gerar_roteiro(titulo, ref)
    (pasta / "roteiro.json").write_text(json.dumps(texto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Título: {texto['titulo']}  |  {len(texto['cenas'])} cenas")

    print("== 2/5 Narração e 3/5 Cenas")
    usados: set = set()
    partes = []
    for i, cena in enumerate(texto["cenas"]):
        audio = pasta / f"voz_{i:02d}.mp3"
        palavras = narracao.narrar(cena["texto"], audio)
        video = cenas.baixar_cena(cena.get("busca") or "dramatic sky", pasta / f"cena_{i:02d}.mp4", usados)
        partes.append({"audio": audio, "palavras": palavras, "video": video})

    print("== 4/5 Montagem")
    short = montagem.montar(partes, pasta)
    dur = montagem.duracao(short)
    capa = montagem.capa(pasta / "video_mudo.mp4", texto.get("capa") or titulo, pasta / "capa.jpg")
    print(f"Short pronto: {short} ({dur:.0f} s)")
    if dur > 180:
        print("ATENÇÃO: passou de 3 minutos; o YouTube não vai tratar como Short.")

    video_id = None
    if enviar:
        print("== 5/5 Publicação")
        if publicar.youtube_configurado():
            video_id = publicar.enviar_youtube(short, capa, texto)
        else:
            print("YouTube não configurado; o vídeo fica só no Telegram e nos artefatos do GitHub.")
        publicar.avisar_telegram(short, texto, video_id)

    roteiro.registrar_historico({
        "historia": titulo, "titulo": texto["titulo"], "data": carimbo,
        "duracao_seg": round(dur), "youtube_id": video_id,
    })
    for temporario in pasta.glob("clipe_*.mp4"):
        temporario.unlink()
    (pasta / "video_mudo.mp4").unlink(missing_ok=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--historia")
    p.add_argument("--sem-enviar", action="store_true")
    args = p.parse_args()
    try:
        produzir(args.historia, enviar=not args.sem_enviar)
    except Exception:
        erro = traceback.format_exc()
        print(erro)
        if not args.sem_enviar:
            publicar.avisar_erro(erro[-1500:])
        sys.exit(1)


if __name__ == "__main__":
    main()
