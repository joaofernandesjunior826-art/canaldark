"""Bot do Telegram: entrega cada Short no seu celular e recebe seus pedidos (refazer, ajustar, novo)."""
import json
from pathlib import Path

import requests

from . import config


def ativo() -> bool:
    return bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID)


def html(texto: str) -> str:
    return str(texto).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def chamar(metodo: str, dados: dict | None = None, arquivos: dict | None = None, timeout: int = 60):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{metodo}"
    try:
        r = requests.post(url, data=dados, files=arquivos, timeout=timeout)
        resposta = r.json()
    except (requests.RequestException, ValueError) as e:
        print(f"Telegram ({metodo}) falhou: {e}")
        return None
    if not resposta.get("ok"):
        print(f"Telegram ({metodo}) recusou: {resposta.get('description')}")
        return None
    return resposta["result"]


def enviar_texto(texto: str, responder_a: int | None = None, botoes: list | None = None) -> int | None:
    if not ativo():
        return None
    dados = {"chat_id": config.TELEGRAM_CHAT_ID, "text": texto[:4096], "parse_mode": "HTML",
             "disable_web_page_preview": "true"}
    if responder_a:
        dados["reply_parameters"] = json.dumps({"message_id": responder_a, "allow_sending_without_reply": True})
    if botoes:
        dados["reply_markup"] = json.dumps({"inline_keyboard": botoes})
    resultado = chamar("sendMessage", dados)
    return resultado["message_id"] if resultado else None


def enviar_video(video: Path, legenda: str, botoes: list, duracao: float) -> int | None:
    if video.stat().st_size > 49_500_000:
        print("Vídeo grande demais para o Telegram (limite de 50 MB para bots).")
        return None
    with open(video, "rb") as f:
        resultado = chamar("sendVideo", {
            "chat_id": config.TELEGRAM_CHAT_ID, "caption": legenda[:1024], "parse_mode": "HTML",
            "supports_streaming": "true", "width": config.LARGURA, "height": config.ALTURA,
            "duration": int(round(duracao)), "reply_markup": json.dumps({"inline_keyboard": botoes}),
        }, {"video": (video.name, f, "video/mp4")}, timeout=600)
    return resultado["message_id"] if resultado else None


def ler_atualizacoes() -> list[dict]:
    resultado = chamar("getUpdates", {"timeout": 0, "allowed_updates": json.dumps(["message", "callback_query"])})
    return resultado or []


def confirmar_atualizacoes(ultimo_id: int) -> None:
    """Marca as mensagens como lidas, para não serem processadas de novo."""
    chamar("getUpdates", {"offset": ultimo_id + 1, "timeout": 0, "limit": 1})


def responder_botao(callback_id: str, texto: str) -> None:
    chamar("answerCallbackQuery", {"callback_query_id": callback_id, "text": texto})


def configurar_comandos() -> None:
    chamar("setMyCommands", {"commands": json.dumps([
        {"command": "novo", "description": "Vídeo extra (pode escrever o tema depois)"},
        {"command": "refazer", "description": "Refaz o último vídeo (pode escrever o ajuste)"},
        {"command": "status", "description": "Mostra a fila e o último vídeo"},
        {"command": "ajuda", "description": "Como usar"},
    ])})


# ---- Mensagens prontas ------------------------------------------------------
def entregar_short(video: Path, item: dict, roteiro: dict, duracao: float) -> list[int]:
    """Manda o Short com os botões e, em seguida, os textos prontos para copiar."""
    if not ativo():
        return []
    linhas = [f"🎬 <b>{html(roteiro['titulo'])}</b>",
              f"📖 {html(roteiro.get('referencia', ''))} · ⏱ {duracao:.0f} s"]
    if item.get("ajuste"):
        linhas.append(f"✏️ Ajuste aplicado: <i>{html(item['ajuste'][:200])}</i>")
    yt = item.get("youtube")
    if yt:
        quando = f"agendado para {yt['quando']}" if yt.get("quando") else f"como {yt['privacidade']}"
        linhas += ["", f"✅ Já foi para o YouTube ({quando}). Para mudar ou apagar: "
                       f"https://studio.youtube.com/video/{yt['id']}/edit"]
    else:
        linhas += ["", "✅ <b>Gostou?</b> Salve o vídeo e poste pelo app do YouTube "
                       "(os textos estão na mensagem abaixo)."]
    linhas.append("🔄 <b>Não gostou?</b> Toque em Refazer ou <b>responda a este vídeo</b> dizendo o que mudar.")
    botoes = [[{"text": "🔄 Refazer", "callback_data": f"refazer:{item['id']}"}]]

    ids = []
    msg_video = enviar_video(video, "\n".join(linhas), botoes, duracao)
    if msg_video:
        ids.append(msg_video)
    else:
        aviso = "\n\n⚠️ Não consegui anexar o vídeo aqui."
        if config.LINK_EXECUCAO:
            aviso += f" Baixe em Artifacts: {config.LINK_EXECUCAO}"
        msg = enviar_texto("\n".join(linhas) + aviso, botoes=botoes)
        if msg:
            ids.append(msg)

    titulo = roteiro["titulo"]
    if len(titulo) + 8 <= 100 and "#shorts" not in titulo.lower():
        titulo += " #Shorts"
    textos = (f"📋 <b>Textos para o YouTube</b> (toque no texto para copiar)\n\n"
              f"<b>Título</b>\n<code>{html(titulo)}</code>\n\n"
              f"<b>Descrição</b> (opcional)\n<code>{html(roteiro.get('descricao', ''))}</code>\n\n"
              f"📱 <b>Como postar:</b> abra o vídeo acima, toque em ⋮ › Salvar na galeria. "
              f"No app do YouTube: + › Enviar um vídeo › escolha o vídeo › cole o título › "
              f"Publicar (ou Programar).")
    if not yt:
        msg_textos = enviar_texto(textos, responder_a=ids[0] if ids else None)
        if msg_textos:
            ids.append(msg_textos)
    return ids


AJUDA = (
    "🤖 <b>Fábrica de Shorts</b>\n\n"
    "Todo dia chega aqui um Short novo. Se gostar, salve e poste no YouTube.\n\n"
    "<b>Pedidos</b>\n"
    "/novo — faz um vídeo extra com a próxima história da lista\n"
    "/novo <i>Sansão e Dalila</i> — vídeo extra sobre o tema que você escrever\n"
    "/refazer — refaz o último vídeo\n"
    "/refazer <i>mais curto e com mais suspense</i> — refaz com esse ajuste\n"
    "/status — mostra a fila e o último vídeo\n\n"
    "Você também pode <b>responder a um vídeo</b> dizendo o que mudar.\n\n"
    "⏱ Eu confiro as mensagens de hora em hora, das 7h às 23h."
)
