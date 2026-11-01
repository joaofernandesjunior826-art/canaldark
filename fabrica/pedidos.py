"""Lê o que você mandou para o bot do Telegram e transforma em pedidos na fila."""
from . import config, estado, telegram


def _video_curto(v: dict) -> str:
    return f"“{v.get('titulo') or v.get('historia')}”"


def _status(e: dict) -> str:
    ultimo = estado.ultimo_video()
    horas = ", ".join(f"{h}h" for h in config.HORARIOS)
    linhas = [f"📋 Pedidos na fila: {len(e['fila'])}",
              f"🕘 Vídeo novo todo dia às {horas} (horário de Brasília)"]
    if ultimo:
        linhas.append(f"🎬 Último vídeo: {telegram.html(_video_curto(ultimo))} "
                      f"em {ultimo['data'][:16].replace('T', ' ')}")
    if estado.falhas_hoje(e):
        linhas.append(f"⚠️ Falhas hoje: {estado.falhas_hoje(e)} de {config.MAX_FALHAS_POR_DIA}")
    return "\n".join(linhas)


def _pedido_refazer(video: dict | None, ajuste: str, pode_produzir: bool) -> list[tuple]:
    if not video:
        telegram.enviar_texto("Não achei esse vídeo no histórico. Use /refazer para refazer o último.")
        return []
    if not pode_produzir:
        telegram.enviar_texto("⚠️ Falta cadastrar a chave GEMINI_API_KEY nos Secrets do GitHub.")
        return []
    detalhe = f" com o ajuste: <i>{telegram.html(ajuste)}</i>" if ajuste else ""
    return [({"tipo": "refazer", "origem": video["id"], "ajuste": ajuste},
             f"📝 Anotado! Vou refazer {telegram.html(_video_curto(video))}{detalhe}. Chega em alguns minutos.")]


def _tratar(atualizacao: dict, e: dict, pode_produzir: bool) -> list[tuple]:
    """Devolve [(pedido, mensagem de confirmação)]; respostas simples já são enviadas aqui."""
    if "callback_query" in atualizacao:
        botao = atualizacao["callback_query"]
        chat = str(botao.get("message", {}).get("chat", {}).get("id"))
        if chat != config.TELEGRAM_CHAT_ID:
            return []
        telegram.responder_botao(botao["id"], "Pedido anotado")
        acao, _, video_id = botao.get("data", "").partition(":")
        if acao == "refazer":
            return _pedido_refazer(estado.achar_video(video_id), "", pode_produzir)
        return []

    msg = atualizacao.get("message") or {}
    if str(msg.get("chat", {}).get("id")) != config.TELEGRAM_CHAT_ID:
        return []  # só obedece o seu chat
    texto = (msg.get("text") or "").strip()
    if not texto:
        return []
    comando, _, resto = texto.partition(" ")
    comando, resto = comando.split("@")[0].lower(), resto.strip()

    if comando in ("/start", "/ajuda", "/help"):
        telegram.enviar_texto(telegram.AJUDA)
        return []
    if comando == "/status":
        telegram.enviar_texto(_status(e))
        return []
    if comando == "/novo":
        if not pode_produzir:
            telegram.enviar_texto("⚠️ Falta cadastrar a chave GEMINI_API_KEY nos Secrets do GitHub.")
            return []
        sobre = f"sobre <i>{telegram.html(resto)}</i>" if resto else "com a próxima história da lista"
        return [({"tipo": "extra", "tema": resto},
                 f"📝 Anotado! Vou fazer um vídeo extra {sobre}. Chega em alguns minutos.")]
    if comando == "/refazer":
        return _pedido_refazer(estado.ultimo_video(), resto, pode_produzir)
    resposta_a = msg.get("reply_to_message", {}).get("message_id")
    if resposta_a and not texto.startswith("/"):
        return _pedido_refazer(estado.achar_por_mensagem(resposta_a), texto, pode_produzir)
    telegram.enviar_texto("Não entendi. 🙂\n\n" + telegram.AJUDA)
    return []


def processar(e: dict) -> int:
    """Lê as mensagens novas, responde e põe os pedidos na fila. Devolve quantos entraram."""
    atualizacoes = telegram.ler_atualizacoes()
    if not atualizacoes:
        return 0
    telegram.configurar_comandos()
    pode_produzir = bool(config.GEMINI_API_KEY)
    novos = 0
    for atualizacao in atualizacoes:
        try:
            for pedido, confirmacao in _tratar(atualizacao, e, pode_produzir):
                if pedido in e["fila"]:
                    telegram.enviar_texto("👍 Esse pedido já está na fila.")
                    continue
                e["fila"].append(pedido)
                novos += 1
                telegram.enviar_texto(confirmacao)
        except Exception as erro:  # uma mensagem estranha não pode travar a fábrica
            print(f"Não consegui tratar a mensagem {atualizacao.get('update_id')}: {erro}")
    telegram.confirmar_atualizacoes(max(a["update_id"] for a in atualizacoes))
    return novos
