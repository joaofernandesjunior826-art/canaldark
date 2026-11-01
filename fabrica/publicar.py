"""Etapa 5: envia o Short ao YouTube (como privado, para você aprovar) e avisa no Telegram."""
from pathlib import Path

import requests

from . import config


def youtube_configurado() -> bool:
    return all([config.YT_CLIENT_ID, config.YT_CLIENT_SECRET, config.YT_REFRESH_TOKEN])


def enviar_youtube(video: Path, capa: Path | None, roteiro: dict) -> str:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    cred = Credentials(None, refresh_token=config.YT_REFRESH_TOKEN,
                       token_uri="https://oauth2.googleapis.com/token",
                       client_id=config.YT_CLIENT_ID, client_secret=config.YT_CLIENT_SECRET,
                       scopes=["https://www.googleapis.com/auth/youtube.upload"])
    yt = build("youtube", "v3", credentials=cred, cache_discovery=False)

    descricao = roteiro.get("descricao", "")
    if "#shorts" not in descricao.lower():
        descricao += "\n\n#Shorts"
    corpo = {
        "snippet": {
            "title": roteiro["titulo"],
            "description": descricao,
            "tags": roteiro.get("tags", []),
            "categoryId": "22",  # Pessoas e blogs
            "defaultLanguage": "pt-BR",
            "defaultAudioLanguage": "pt-BR",
        },
        "status": {
            "privacyStatus": config.YT_PRIVACIDADE,
            "selfDeclaredMadeForKids": False,
            # Conteúdo com voz e imagens sintéticas: declarado como alterado/sintético.
            "containsSyntheticMedia": True,
        },
    }
    pedido = yt.videos().insert(part="snippet,status", body=corpo,
                                media_body=MediaFileUpload(str(video), chunksize=-1, resumable=True))
    resposta = None
    while resposta is None:
        _, resposta = pedido.next_chunk()
    video_id = resposta["id"]
    print(f"Enviado ao YouTube: https://youtube.com/shorts/{video_id} ({config.YT_PRIVACIDADE})")

    if capa and capa.exists():
        try:  # só funciona em canais verificados por telefone; não é obrigatório
            yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(capa))).execute()
        except Exception as e:
            print(f"Capa não enviada (normal em canal não verificado): {e}")
    return video_id


def avisar_telegram(video: Path, roteiro: dict, video_id: str | None) -> None:
    if not (config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID):
        print("Telegram não configurado; pulando aviso.")
        return
    base = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"
    if video_id:
        acao = (f"Já está no YouTube como PRIVADO.\n"
                f"Aprovar: abra o YouTube Studio e mude para Público ou Programado.\n"
                f"https://studio.youtube.com/video/{video_id}/edit")
    else:
        acao = "Não foi enviado ao YouTube (credenciais não configuradas). Baixe e poste manualmente."
    legenda = (f"🎬 Novo Short pronto\n\n<b>{_html(roteiro['titulo'])}</b>\n"
               f"{_html(roteiro.get('referencia', ''))}\n\n{_html(acao)}")
    tamanho_mb = video.stat().st_size / 1e6
    if tamanho_mb < 49:
        with open(video, "rb") as f:
            r = requests.post(f"{base}/sendVideo", timeout=300,
                              data={"chat_id": config.TELEGRAM_CHAT_ID, "caption": legenda[:1024],
                                    "parse_mode": "HTML", "supports_streaming": "true"},
                              files={"video": (video.name, f, "video/mp4")})
    else:
        r = requests.post(f"{base}/sendMessage", timeout=60,
                          data={"chat_id": config.TELEGRAM_CHAT_ID, "parse_mode": "HTML",
                                "text": legenda + f"\n\n(Vídeo com {tamanho_mb:.0f} MB, grande demais para o Telegram.)"})
    if r.status_code != 200:
        print(f"Telegram falhou: HTTP {r.status_code} {r.text[:300]}")
    else:
        print("Aviso enviado no Telegram.")


def avisar_erro(mensagem: str) -> None:
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
                      data={"chat_id": config.TELEGRAM_CHAT_ID,
                            "text": f"⚠️ A fábrica de Shorts falhou:\n{mensagem[:3500]}"}, timeout=30)


def _html(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
