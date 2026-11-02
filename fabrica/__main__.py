"""Fábrica de Shorts. Comandos:

  python -m fabrica chaves          abre as chaves guardadas no cofre do painel (no GitHub Actions)
  python -m fabrica planejar        lê os pedidos (painel, Telegram, GitHub) e vê se está na hora do vídeo
  python -m fabrica etapa <nome>    roda uma estação: pauta, roteiro, narracao, cenas, montagem,
                                    shorts, thumbnail, agenda
  python -m fabrica falha           registra e avisa que um passo falhou
  python -m fabrica teste           produz um vídeo na pasta saida/ sem enviar nada (para testar)
      --tema "Davi e Golias"          tema ou história (opcional)
      --roteiro arquivo.json          usa um roteiro pronto em vez de chamar o Gemini
"""
import argparse
import json
import os
import shutil
import sys

from . import acoes, chaves, config, estado, etapas, pedidos, telegram, youtube


def _config_atual() -> dict:
    """O que está configurado (sem revelar nenhuma chave), para o painel mostrar o que falta."""
    return {"gemini": bool(config.GEMINI_API_KEY), "pexels": bool(config.PEXELS_API_KEY),
            "pixabay": bool(config.PIXABAY_API_KEY), "telegram": telegram.ativo(),
            "youtube_auto": youtube.configurado(), "postagem": [f"{h:02d}:{m:02d}" for h, m in config.POSTAGEM],
            "yt_horarios": config.YT_HORARIOS, "duracao_alvo": config.DURACAO_ALVO, "voz": config.VOZ,
            "instagram_cta": config.INSTAGRAM_CTA, "instagram_arroba": config.INSTAGRAM_ARROBA}


def planejar() -> None:
    e = estado.ler_estado()
    antes = json.dumps(e, sort_keys=True)
    e["config"] = _config_atual()

    # 1) Pedidos do painel (um arquivo por pedido em dados/pedidos/)
    for arquivo, pedido in estado.ler_pedidos_do_painel():
        print(f"Painel: {pedido.get('acao')} {pedido.get('id', '')} -> {acoes.aplicar(e, pedido)}")
        arquivo.unlink(missing_ok=True)

    # 2) Botão "Run workflow" do GitHub
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        pedido = {"acao": os.environ.get("ACAO") or "produzir", "id": os.environ.get("VIDEO_ID", ""),
                  "tema": os.environ.get("TEMA", ""), "ajuste": os.environ.get("AJUSTE", "")}
        print(f"GitHub: {pedido['acao']} -> {acoes.aplicar(e, pedido)}")

    # 3) Mensagens do Telegram
    if telegram.ativo():
        pedidos.processar(e)

    # 4) Agenda de postagem: um vídeo pronto para cada horário das próximas horas
    if not config.GEMINI_API_KEY:
        print("Falta cadastrar GEMINI_API_KEY nos Secrets do GitHub; nada novo será produzido.")
    elif estado.falhas_hoje(e) >= config.MAX_FALHAS_POR_DIA:
        print("Muitas falhas hoje; a fábrica volta amanhã.")
    else:
        novos = acoes.preparar_agenda(e)
        if novos:
            print(f"Agenda: {novos} horário(s) de postagem sem vídeo; entraram na fila.")

    # 5) Escolhe o próximo vídeo a produzir (um por execução; o resto espera a próxima)
    producao, tipo = False, "shorts"
    if not etapas.ler_trabalho():
        for tarefa in sorted(e["fila"], key=acoes.prioridade):
            pode = config.GEMINI_API_KEY or tarefa["tipo"] == "teste" or tarefa.get("exemplo")
            if tarefa["tipo"] in acoes.TAREFAS_DE_PRODUCAO and pode:
                e["fila"].remove(tarefa)
                etapas.iniciar(tarefa)
                producao = True
                tipo = "instagram" if tarefa["tipo"] == "instagram" else "shorts"
                print(f"Produzindo agora: {tarefa}")
                break
    publicar = youtube.configurado() and any(t["tipo"] == "publicar" for t in e["fila"])

    if json.dumps(e, sort_keys=True) != antes:
        estado.salvar_estado(e)
    print(f"Pedidos na fila: {len(e['fila'])}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"producao={'sim' if producao else 'nao'}\npublicar={'sim' if publicar else 'nao'}\ntipo={tipo}\n")


def tem_fila() -> bool:
    """Ainda há vídeo pedido que dá para produzir agora? (mesma regra do planejar)"""
    e = estado.ler_estado()
    if estado.falhas_hoje(e) >= config.MAX_FALHAS_POR_DIA:
        return False
    return any(t["tipo"] in acoes.TAREFAS_DE_PRODUCAO and
               (config.GEMINI_API_KEY or t["tipo"] == "teste" or t.get("exemplo")) for t in e["fila"])


def teste(tema: str, arquivo_roteiro: str | None) -> None:
    """Sem tema nem roteiro, usa o roteiro de exemplo (não precisa de nenhuma chave)."""
    pronto = json.loads(open(arquivo_roteiro, encoding="utf-8").read()) if arquivo_roteiro else None
    if pronto:
        tarefa = {"tipo": "extra", "tema": pronto.get("historia", "")}
    elif tema:
        tarefa = {"tipo": "extra", "tema": tema}
    else:
        tarefa = {"tipo": "teste"}
    t = etapas.produzir_tudo(tarefa, enviar=False, roteiro_pronto=pronto)
    print(f"Pronto: {t['pasta']}/short.mp4")


def main() -> None:
    p = argparse.ArgumentParser(description="Fábrica de Shorts")
    p.add_argument("acao", choices=["chaves", "planejar", "etapa", "falha", "teste", "fila"])
    p.add_argument("nome", nargs="?", help="etapa: nome da estação")
    p.add_argument("--tema", default="", help="teste: tema ou história")
    p.add_argument("--roteiro", help="teste: arquivo JSON com um roteiro pronto")
    args = p.parse_args()
    precisa_ffmpeg = args.acao == "teste" or (args.acao == "etapa" and args.nome != "agenda")
    if precisa_ffmpeg and not shutil.which("ffmpeg"):
        sys.exit("O ffmpeg não está instalado.")
    if args.acao == "chaves":
        chaves.carregar()
    elif args.acao == "planejar":
        planejar()
    elif args.acao == "etapa":
        etapas.executar_etapa(args.nome)
    elif args.acao == "falha":
        etapas.registrar_falha()
    elif args.acao == "fila":
        print("sim" if tem_fila() else "nao")
    else:
        teste(args.tema.strip(), args.roteiro)


if __name__ == "__main__":
    main()
