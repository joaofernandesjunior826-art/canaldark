"""Envio automático ao YouTube. OPCIONAL: só funciona de verdade depois que a Google aprovar a
auditoria do seu projeto. Antes disso, todo vídeo enviado pela API fica TRAVADO como privado,
sem recurso (https://support.google.com/youtube/answer/7300965). Por isso vem desligado."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config


def configurado() -> bool:
    return config.YT_ENVIO_AUTOMATICO and all(
        [config.YT_CLIENT_ID, config.YT_CLIENT_SECRET, config.YT_REFRESH_TOKEN])


def proximo_horario(ocupados: set[str]) -> datetime | None:
    """Próximo horário livre de publicação (YT_HORARIO), a pelo menos 1 hora de agora."""
    if not config.YT_HORARIOS:
        return None
    agora = datetime.now(config.FUSO)
    for dias in range(0, 60):
        for texto in sorted(config.YT_HORARIOS):
            hora, _, minuto = texto.partition(":")
            if not hora.isdigit():
                continue
            alvo = (agora + timedelta(days=dias)).replace(hour=int(hora) % 24, minute=int(minuto or 0) % 60,
                                                         second=0, microsecond=0)
            if alvo >= agora + timedelta(hours=1) and alvo.isoformat(timespec="minutes") not in ocupados:
                return alvo
    return None


def enviar(video: Path, capa: Path | None, item: dict, ocupados: set[str]) -> dict:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    cred = Credentials(None, refresh_token=config.YT_REFRESH_TOKEN,
                       token_uri="https://oauth2.googleapis.com/token",
                       client_id=config.YT_CLIENT_ID, client_secret=config.YT_CLIENT_SECRET,
                       scopes=["https://www.googleapis.com/auth/youtube.upload"])
    yt = build("youtube", "v3", credentials=cred, cache_discovery=False)

    descricao = item.get("descricao", "")
    if "#shorts" not in descricao.lower():
        descricao += "\n\n#Shorts"
    status = {"selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}
    quando = None
    if item.get("postar_em"):  # o horário da agenda de postagem, se ainda não passou
        marcado = datetime.fromisoformat(item["postar_em"])
        if marcado > datetime.now(timezone.utc) + timedelta(minutes=20):
            quando = marcado
    quando = quando or proximo_horario(ocupados)
    if quando:
        status.update(privacyStatus="private",
                      publishAt=quando.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    else:
        status["privacyStatus"] = config.YT_PRIVACIDADE
    corpo = {
        "snippet": {"title": item["titulo"], "description": descricao, "tags": item.get("tags", []),
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
            "agendado_para": quando.isoformat(timespec="minutes") if quando else None}
