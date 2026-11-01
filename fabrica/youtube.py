"""Envio automático ao YouTube. OPCIONAL: só use depois que a Google aprovar a auditoria do seu
projeto. Antes disso, todo vídeo enviado pela API fica TRAVADO como privado, sem recurso
(https://support.google.com/youtube/answer/7300965). Por isso vem desligado."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config


def configurado() -> bool:
    return config.YT_ENVIO_AUTOMATICO and all(
        [config.YT_CLIENT_ID, config.YT_CLIENT_SECRET, config.YT_REFRESH_TOKEN])


def _proximo_horario() -> datetime | None:
    if not config.YT_HORARIO:
        return None
    hora, _, minuto = config.YT_HORARIO.partition(":")
    agora = datetime.now(config.FUSO)
    alvo = agora.replace(hour=int(hora), minute=int(minuto or 0), second=0, microsecond=0)
    if alvo < agora + timedelta(hours=1):
        alvo += timedelta(days=1)
    return alvo


def enviar(video: Path, capa: Path | None, roteiro: dict) -> dict:
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
    status = {"selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}
    quando = _proximo_horario()
    if quando:
        status.update(privacyStatus="private",
                      publishAt=quando.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    else:
        status["privacyStatus"] = config.YT_PRIVACIDADE
    corpo = {
        "snippet": {"title": roteiro["titulo"], "description": descricao, "tags": roteiro.get("tags", []),
                    "categoryId": "22", "defaultLanguage": "pt-BR", "defaultAudioLanguage": "pt-BR"},
        "status": status,
    }
    pedido = yt.videos().insert(part="snippet,status", body=corpo,
                                media_body=MediaFileUpload(str(video), chunksize=-1, resumable=True))
    resposta = None
    while resposta is None:
        _, resposta = pedido.next_chunk()
    video_id = resposta["id"]
    print(f"Enviado ao YouTube: https://youtube.com/shorts/{video_id}")

    if capa and capa.exists():
        try:  # só funciona em canais verificados por telefone; não é obrigatório
            yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(capa))).execute()
        except Exception as e:
            print(f"Capa não enviada (normal em canal não verificado): {e}")
    return {"id": video_id, "privacidade": status["privacyStatus"],
            "quando": quando.strftime("%d/%m às %H:%M") if quando else None}
