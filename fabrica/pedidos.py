"""Lê o que você mandou para o bot do Telegram e transforma em ações (aprovar, refazer, novo...)."""
from . import acoes, config, estado, telegram


def _status(e: dict) -> str:
    videos = estado.historico()
    aguardando = sum(1 for v in videos if v.get("status") == "aguardando")
    aprovados = sum(1 for v in videos if v.get("status") in ("aprovado", "programado"))
    horas = ", ".join(f"{h}h" for h in config.HORARIOS)
    linhas = [f"⏳ Esperando aprovação: {aguardando}",
              f"✅ Aprovados ou programados: {aprovados}",
              f"📋 Pedidos na fila: {len(e['fila'])}",
              f"🕘 Vídeo novo todo dia às {horas} (horário de Brasília)"]
    ultimo = estado.ultimo_video()
    if ultimo:
        linhas.append(f"🎬 Último: “{telegram.html(ultimo['titulo'])}” em {ultimo['data'][:16].replace('T', ' ')}")
    if estado.falhas_hoje(e):
        linhas.append(f"⚠️ Falhas hoje: {estado.falhas_hoje(e)} de {config.MAX_FALHAS_POR_DIA}")
    return "\n".join(linhas)


def _tratar(atualizacao: dict, e: dict) -> None:
    if "callback_query" in atualizacao:
        botao = atualizacao["callback_query"]
        if str(botao.get("message", {}).get("chat", {}).get("id")) != config.TELEGRAM_CHAT_ID:
            return
        acao, _, video_id = botao.get("data", "").partition(":")
        resultado = acoes.aplicar(e, {"acao": acao, "id": video_id})
        telegram.responder_botao(botao["id"], resultado[:190])
        telegram.enviar_texto("📝 " + telegram.html(resultado))
        return

    msg = atualizacao.get("message") or {}
    if str(msg.get("chat", {}).get("id")) != config.TELEGRAM_CHAT_ID:
        return  # só obedece o seu chat
    texto = (msg.get("text") or "").strip()
    if not texto:
        return
    comando, _, resto = texto.partition(" ")
    comando, resto = comando.split("@")[0].lower(), resto.strip()

    if comando in ("/start", "/ajuda", "/help"):
        telegram.enviar_texto(telegram.AJUDA, botoes=telegram._botao_painel())
        return
    if comando == "/status":
        telegram.enviar_texto(_status(e), botoes=telegram._botao_painel())
        return
    if comando == "/novo":
        resultado = acoes.aplicar(e, {"acao": "produzir", "tema": resto})
    elif comando == "/refazer":
        ultimo = estado.ultimo_video()
        resultado = acoes.aplicar(e, {"acao": "refazer", "id": ultimo["id"] if ultimo else "", "ajuste": resto})
    elif msg.get("reply_to_message") and not texto.startswith("/"):
        video = estado.achar_por_mensagem(msg["reply_to_message"].get("message_id"))
        if not video:
            telegram.enviar_texto("Não achei esse vídeo. Use /refazer para refazer o último.")
            return
        resultado = acoes.aplicar(e, {"acao": "refazer", "id": video["id"], "ajuste": texto})
    else:
        telegram.enviar_texto("Não entendi. 🙂\n\n" + telegram.AJUDA)
        return
    telegram.enviar_texto("📝 " + telegram.html(resultado))


def processar(e: dict) -> int:
    """Lê as mensagens novas, responde e aplica os pedidos. Devolve quantas mensagens tratou."""
    atualizacoes = telegram.ler_atualizacoes()
    if not atualizacoes:
        return 0
    telegram.configurar_comandos()
    for atualizacao in atualizacoes:
        try:
            _tratar(atualizacao, e)
        except Exception as erro:  # uma mensagem estranha não pode travar a fábrica
            print(f"Não consegui tratar a mensagem {atualizacao.get('update_id')}: {erro}")
    telegram.confirmar_atualizacoes(max(a["update_id"] for a in atualizacoes))
    return len(atualizacoes)
