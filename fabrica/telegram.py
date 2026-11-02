"""Bot do Telegram (opcional): avisa no celular quando há vídeo esperando aprovação e recebe
pedidos rápidos (aprovar, refazer, ajustar, novo). O painel faz tudo isso também."""
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


def _botao_painel() -> list:
    return [[{"text": "📱 Abrir o painel", "url": config.PAINEL_URL}]] if config.PAINEL_URL else []


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
def avisar_novo(video: Path, item: dict) -> list[int]:
    """Vídeo novo esperando aprovação: manda o vídeo com os botões Aprovar e Refazer."""
    if not ativo():
        return []
    linhas = [f"🎬 <b>{html(item['titulo'])}</b>",
              f"📖 {html(item.get('referencia', ''))} · ⏱ {item.get('duracao_seg', 0)} s"]
    if item.get("postar_em"):
        linhas.append(f"📅 Postar às {item['postar_em'][11:16]} do dia {item['postar_em'][8:10]}/{item['postar_em'][5:7]}")
    if item.get("ajuste"):
        linhas.append(f"✏️ Ajuste aplicado: <i>{html(item['ajuste'][:200])}</i>")
    linhas += ["", "Esperando a sua aprovação. Aprove aqui ou no painel; se não gostou, toque em "
                   "Refazer ou <b>responda a este vídeo</b> dizendo o que mudar."]
    botoes = [[{"text": "✅ Aprovar", "callback_data": f"aprovar:{item['id']}"},
               {"text": "🔄 Refazer", "callback_data": f"refazer:{item['id']}"}]] + _botao_painel()
    msg = enviar_video(video, "\n".join(linhas), botoes, item.get("duracao_seg", 0))
    if not msg:
        aviso = "\n\n⚠️ Não consegui anexar o vídeo aqui; assista no painel."
        msg = enviar_texto("\n".join(linhas) + aviso, botoes=botoes)
    return [msg] if msg else []


def avisar_reels(video: Path, item: dict) -> list[int]:
    """Reels novo da Clover: manda o vídeo pronto para postar, com a legenda para copiar."""
    if not ativo():
        return []
    linhas = [f"📱 <b>Reels novo: {html(item['titulo'])}</b>", f"⏱ {item.get('duracao_seg', 30)} s · site-conceito"]
    if item.get("ajuste"):
        linhas.append(f"✏️ Ajuste aplicado: <i>{html(item['ajuste'][:200])}</i>")
    linhas += ["", "Baixe e poste no Instagram (escolha uma música em alta no app, se quiser). "
                   "A legenda vem logo abaixo, é só copiar."]
    botoes = [[{"text": "🔄 Refazer", "callback_data": f"refazer:{item['id']}"}]] + _botao_painel()
    msg = enviar_video(video, "\n".join(linhas), botoes, item.get("duracao_seg", 0))
    if not msg:
        msg = enviar_texto("\n".join(linhas) + "\n\n⚠️ Não consegui anexar o vídeo aqui; baixe no painel.", botoes=botoes)
    ids = [msg] if msg else []
    if item.get("legenda"):
        legenda = enviar_texto(f"<code>{html(item['legenda'][:3500])}</code>", responder_a=msg)
        if legenda:
            ids.append(legenda)
    return ids


def avisar_aprovado(item: dict | None) -> None:
    """Aprovado sem envio automático: manda os textos prontos e o passo a passo para postar."""
    if not ativo() or not item:
        return
    titulo = item["titulo"]
    if len(titulo) + 8 <= 100 and "#shorts" not in titulo.lower():
        titulo += " #Shorts"
    texto = (f"✅ <b>Aprovado!</b> Agora é só postar.\n\n"
             f"<b>Título</b> (toque para copiar)\n<code>{html(titulo)}</code>\n\n"
             f"<b>Descrição</b> (opcional)\n<code>{html(item.get('descricao', ''))}</code>\n\n"
             f"📱 <b>Como postar:</b> abra o vídeo, toque em ⋮ › Salvar na galeria. No app do YouTube: "
             f"+ › Enviar um vídeo › escolha o vídeo › cole o título › Publicar (ou Programar). "
             f"Depois marque como publicado no painel.")
    enviar_texto(texto, responder_a=(item.get("telegram") or [None])[0], botoes=_botao_painel())


def avisar_programado(item: dict) -> None:
    yt = item.get("youtube") or {}
    quando = yt.get("agendado_para")
    texto = (f"📅 <b>{html(item['titulo'])}</b> foi para o YouTube "
             + (f"e está programado para {quando[8:10]}/{quando[5:7]} às {quando[11:16]}." if quando
                else f"como {html(yt.get('privacidade', 'privado'))}.")
             + f"\nhttps://studio.youtube.com/video/{yt.get('id', '')}/edit")
    enviar_texto(texto, responder_a=(item.get("telegram") or [None])[0])


AJUDA = (
    "🤖 <b>Fábrica de Shorts</b>\n\n"
    "Todo dia chega aqui um Short novo para você aprovar. Tudo também pode ser feito pelo painel.\n\n"
    "<b>Pedidos</b>\n"
    "/novo — faz um vídeo extra com a próxima história da lista\n"
    "/novo <i>Sansão e Dalila</i> — vídeo extra sobre o tema que você escrever\n"
    "/refazer — refaz o último vídeo\n"
    "/refazer <i>mais curto e com mais suspense</i> — refaz com esse ajuste\n"
    "/status — mostra a fila e o último vídeo\n\n"
    "Você também pode <b>responder a um vídeo</b> dizendo o que mudar.\n\n"
    "⏱ Eu confiro as mensagens de hora em hora, das 7h às 23h. Pelo painel é na hora."
)
