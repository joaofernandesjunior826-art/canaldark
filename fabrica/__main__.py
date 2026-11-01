"""Fábrica de Shorts. Comandos:

  python -m fabrica planejar   lê os pedidos do Telegram e vê se está na hora do vídeo do dia
  python -m fabrica executar   produz o que estiver na fila e entrega no Telegram
  python -m fabrica teste      produz um vídeo na pasta saida/ sem enviar nada (para testar)
      --tema "Davi e Golias"     tema ou história (opcional)
      --roteiro arquivo.json     usa um roteiro pronto em vez de chamar o Gemini
"""
import argparse
import json
import os
import shutil
import sys
import traceback

from . import cenas, config, estado, montagem, narracao, pedidos, roteiro, telegram, youtube


# ---- Planejamento -----------------------------------------------------------
def video_do_dia_pendente(e: dict) -> bool:
    agora = estado.agora()
    previstos = sum(1 for h in config.HORARIOS if agora.hour >= h)
    feitos = sum(1 for v in estado.historico()
                 if v.get("tipo") == "novo" and v.get("data", "")[:10] == estado.hoje())
    na_fila = sum(1 for t in e["fila"] if t["tipo"] == "novo")
    return feitos + na_fila < previstos


def planejar(forcar: bool, tema: str) -> None:
    e = estado.ler_estado()
    mudou = pedidos.processar(e) > 0 if telegram.ativo() else False
    novos = []

    if not config.GEMINI_API_KEY:
        print("Falta cadastrar GEMINI_API_KEY nos Secrets do GitHub; nada será produzido.")
    elif forcar:  # botão "Run workflow" no GitHub
        tipo = "novo" if video_do_dia_pendente(e) else "extra"
        novos.append({"tipo": tipo, "tema": tema})
    elif estado.falhas_hoje(e) >= config.MAX_FALHAS_POR_DIA:
        print("Muitas falhas hoje; a fábrica volta amanhã.")
    elif video_do_dia_pendente(e):
        novos.append({"tipo": "novo"})

    if novos or mudou:
        e["fila"].extend(novos)
        estado.salvar_estado(e)
    tem = bool(e["fila"]) and bool(config.GEMINI_API_KEY)
    print(f"Pedidos na fila: {len(e['fila'])}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"tarefas={'sim' if tem else 'nao'}\n")


# ---- Produção ---------------------------------------------------------------
def produzir(tarefa: dict, e: dict, enviar: bool = True, roteiro_pronto: dict | None = None) -> dict:
    ajuste = tarefa.get("ajuste", "")
    if tarefa["tipo"] == "refazer":
        original = estado.achar_video(tarefa["origem"])
        if not original:
            raise RuntimeError("Não achei o vídeo original para refazer.")
        titulo, ref = original["historia"], original.get("referencia", "")
    elif tarefa.get("tema"):
        titulo, ref = roteiro.achar_historia(tarefa["tema"]) or (tarefa["tema"], "")
    else:
        titulo, ref = roteiro.proxima_historia()
    print(f"== {tarefa['tipo'].upper()}: {titulo} {f'({ref})' if ref else ''}"
          f"{f' | ajuste: {ajuste}' if ajuste else ''}")

    video_id = estado.agora().strftime("%Y%m%d-%H%M%S")
    pasta = config.SAIDA / video_id
    pasta.mkdir(parents=True, exist_ok=True)

    print("== 1/4 Roteiro")
    recentes = [v["titulo"] for v in estado.historico()[-8:] if v.get("titulo")]
    texto = roteiro_pronto or roteiro.gerar_roteiro(titulo, ref, ajuste, recentes)
    (pasta / "roteiro.json").write_text(json.dumps(texto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Título: {texto['titulo']}")

    print("== 2/4 Narração e cenas")
    evitar = set(e["clipes_usados"])
    partes = []
    for i, cena in enumerate(texto["cenas"]):
        audio = pasta / f"voz_{i:02d}.mp3"
        palavras = narracao.narrar(cena["texto"], audio)
        dur = montagem.duracao(audio) + montagem.PAUSA
        arquivo = pasta / f"cena_{i:02d}.mp4"
        chave = cenas.baixar_cena(cena["busca"], arquivo, evitar, dur)
        partes.append({"audio": audio, "palavras": palavras, "dur": dur,
                       "video": arquivo if chave else None})
    e["clipes_usados"] = list(dict.fromkeys(e["clipes_usados"] + sorted(evitar)))

    print("== 3/4 Montagem")
    short = montagem.montar(partes, texto.get("capa", ""), pasta)
    dur = montagem.duracao(short)
    capa = montagem.capa(pasta / "video_mudo.mp4", texto.get("capa") or texto["titulo"], pasta / "capa.jpg")
    print(f"Short pronto: {short} ({dur:.0f} s, {short.stat().st_size / 1e6:.1f} MB)")

    item = {"id": video_id, "tipo": tarefa["tipo"], "historia": titulo,
            "referencia": texto.get("referencia") or ref, "titulo": texto["titulo"],
            "data": estado.agora().isoformat(timespec="seconds"), "duracao_seg": round(dur)}
    if ajuste:
        item["ajuste"] = ajuste
    if tarefa.get("origem"):
        item["origem"] = tarefa["origem"]

    if enviar:
        print("== 4/4 Entrega")
        if youtube.configurado():
            item["youtube"] = youtube.enviar(short, capa, texto)
        item["telegram"] = telegram.entregar_short(short, item, texto, dur)
        estado.adicionar_video(item)

    for temporario in [*pasta.glob("clipe_*.mp4"), *pasta.glob("cena_*.mp4"), *pasta.glob("voz_*.mp3"),
                       pasta / "video_mudo.mp4", pasta / "clipes.txt"]:
        temporario.unlink(missing_ok=True)
    return item


def _resumo_erro(erro: Exception) -> str:
    return (str(erro).strip().splitlines() or [type(erro).__name__])[-1][:400]


def executar() -> int:
    e = estado.ler_estado()
    if not e["fila"]:
        print("Nada na fila.")
        return 0
    falhou = False
    for _ in range(config.MAX_POR_EXECUCAO):
        if not e["fila"]:
            break
        tarefa = e["fila"].pop(0)
        estado.salvar_estado(e)  # tira da fila antes: um erro não vira repetição infinita
        try:
            produzir(tarefa, e)
        except Exception as erro:
            falhou = True
            traceback.print_exc()
            resumo = telegram.html(_resumo_erro(erro))
            if tarefa["tipo"] == "novo":
                n = estado.registrar_falha(e)
                if n >= config.MAX_FALHAS_POR_DIA:
                    msg = f"⚠️ Não consegui fazer o vídeo de hoje ({n} tentativas). Paro por hoje e volto amanhã."
                else:
                    msg = f"⚠️ Não consegui fazer o vídeo de hoje (tentativa {n} de {config.MAX_FALHAS_POR_DIA}). Tento de novo na próxima hora."
            else:
                msg = "⚠️ Não consegui atender o seu pedido. Pode pedir de novo daqui a pouco."
            if config.LINK_EXECUCAO:
                msg += f"\n\nDetalhes: {config.LINK_EXECUCAO}"
            telegram.enviar_texto(f"{msg}\n\nErro: <code>{resumo}</code>")
        estado.salvar_estado(e)
    return 1 if falhou else 0


def teste(tema: str, arquivo_roteiro: str | None) -> None:
    pronto = json.loads(open(arquivo_roteiro, encoding="utf-8").read()) if arquivo_roteiro else None
    if pronto and not tema:
        tema = pronto.get("historia", "")
    item = produzir({"tipo": "extra", "tema": tema}, estado.ler_estado(), enviar=False, roteiro_pronto=pronto)
    print(f"Pronto: {config.SAIDA / item['id'] / 'short.mp4'}")


def main() -> None:
    p = argparse.ArgumentParser(description="Fábrica de Shorts")
    p.add_argument("acao", choices=["planejar", "executar", "teste"])
    p.add_argument("--forcar", action="store_true", help="planejar: pede um vídeo agora")
    p.add_argument("--tema", default=os.environ.get("TEMA", ""), help="tema ou história")
    p.add_argument("--roteiro", help="teste: arquivo JSON com um roteiro pronto")
    args = p.parse_args()
    if not shutil.which("ffmpeg") and args.acao != "planejar":
        sys.exit("O ffmpeg não está instalado.")
    if args.acao == "planejar":
        planejar(args.forcar, args.tema.strip())
    elif args.acao == "executar":
        sys.exit(executar())
    else:
        teste(args.tema.strip(), args.roteiro)


if __name__ == "__main__":
    main()
