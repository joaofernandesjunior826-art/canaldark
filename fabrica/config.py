"""Configurações lidas das variáveis de ambiente (no GitHub ficam em Secrets/Variables)."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
MUSICA = RAIZ / "musica"
SAIDA = Path(os.environ.get("SAIDA_DIR", RAIZ / "saida"))


def _env(nome: str, padrao: str = "") -> str:
    valor = os.environ.get(nome, "").strip()
    return valor or padrao


# Chaves (todas gratuitas)
GEMINI_API_KEY = _env("GEMINI_API_KEY")
PEXELS_API_KEY = _env("PEXELS_API_KEY")
PIXABAY_API_KEY = _env("PIXABAY_API_KEY")

# YouTube (OAuth). Sem isso, o vídeo é só gerado e enviado ao Telegram.
YT_CLIENT_ID = _env("YT_CLIENT_ID")
YT_CLIENT_SECRET = _env("YT_CLIENT_SECRET")
YT_REFRESH_TOKEN = _env("YT_REFRESH_TOKEN")
# private (padrão), unlisted ou public. Projetos não verificados pela Google sobem sempre como private.
YT_PRIVACIDADE = _env("YT_PRIVACIDADE", "private")

# Telegram (aviso com o vídeo para você aprovar)
TELEGRAM_BOT_TOKEN = _env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _env("TELEGRAM_CHAT_ID")

# Ajustes do vídeo
# "gemini-flash-latest" aponta sempre para o Flash mais novo; os outros são reserva.
GEMINI_MODELOS = [m.strip() for m in _env(
    "GEMINI_MODELO", "gemini-flash-latest,gemini-2.5-flash,gemini-flash-lite-latest"
).split(",") if m.strip()]
VOZ = _env("VOZ", "pt-BR-AntonioNeural")  # outras: pt-BR-FranciscaNeural, pt-BR-ThalitaMultilingualNeural
VELOCIDADE_VOZ = _env("VELOCIDADE_VOZ", "+8%")
DURACAO_ALVO = int(_env("DURACAO_ALVO_SEG", "70"))  # Shorts aceitam até 180 s
VOLUME_MUSICA = float(_env("VOLUME_MUSICA", "0.12"))
NOME_CANAL = _env("NOME_CANAL", "Histórias da Bíblia")

LARGURA, ALTURA, FPS = 1080, 1920, 30
