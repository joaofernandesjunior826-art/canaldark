"""Configurações lidas das variáveis de ambiente (no GitHub ficam em Secrets e Variables)."""
import os
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
MUSICA = RAIZ / "musica"
SAIDA = Path(os.environ.get("SAIDA_DIR") or RAIZ / "saida").resolve()
FUSO = ZoneInfo("America/Sao_Paulo")


def _env(nome: str, padrao: str = "") -> str:
    valor = os.environ.get(nome, "").strip()
    return valor or padrao


def _numero(nome: str, padrao: float) -> float:
    """Lê um número tolerando erros de digitação (ex.: "60s", "0,2"); se não der, usa o padrão."""
    texto = _env(nome).replace(",", ".")
    numero = "".join(c for c in texto if c.isdigit() or c == ".")
    try:
        return float(numero) if numero else padrao
    except ValueError:
        print(f"Aviso: valor inválido em {nome} ({texto!r}); usando {padrao}.")
        return padrao


def _chave(nome: str) -> str:
    """Secret do GitHub com esse nome ou, se não houver, a chave guardada no cofre do painel."""
    return _env(nome) or _env(f"PAINEL_{nome}")


# ---- Chaves gratuitas -------------------------------------------------------
GEMINI_API_KEY = _chave("GEMINI_API_KEY")
PEXELS_API_KEY = _chave("PEXELS_API_KEY")
PIXABAY_API_KEY = _chave("PIXABAY_API_KEY")

# ---- Telegram: onde os vídeos chegam para você aprovar ----------------------
TELEGRAM_BOT_TOKEN = _chave("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _chave("TELEGRAM_CHAT_ID")

# ---- Agenda de postagem no YouTube ------------------------------------------
# Os horários (de Brasília) em que você posta um Short: um vídeo por horário. A fábrica deixa cada
# vídeo pronto para aprovação com antecedência. Padrão: os 15 melhores horários para Shorts no
# Brasil (picos de manhã, almoço, fim de tarde e noite). Para mudar: variável POSTAGEM.
POSTAGEM_PADRAO = "06:30,08:00,09:30,11:00,12:00,13:00,14:30,16:00,17:30,18:30,19:30,20:30,21:15,22:00,23:00"


def _horarios(texto: str) -> list[tuple[int, int]]:
    saida = set()
    for parte in texto.replace(" ", "").replace("h", ":").split(","):
        hora, _, minuto = parte.partition(":")
        if hora.isdigit() and int(hora) < 24 and (not minuto or (minuto.isdigit() and int(minuto) < 60)):
            saida.add((int(hora), int(minuto or 0)))
    return sorted(saida)


POSTAGEM = _horarios(_env("POSTAGEM", POSTAGEM_PADRAO)) or _horarios(POSTAGEM_PADRAO)
ANTECEDENCIA_HORAS = min(max(_numero("ANTECEDENCIA_HORAS", 16), 2), 36)  # quanto antes o vídeo fica pronto
MAX_FALHAS_POR_DIA = 10    # depois disso a fábrica para até o dia seguinte
MANTER_PREVIAS = 60        # quantos vídeos recentes ficam guardados para o painel

# ---- Roteiro ----------------------------------------------------------------
# Modelos gratuitos tentados em ordem. "gemini-flash-latest" aponta sempre para o Flash mais novo.
GEMINI_MODELOS = [m.strip() for m in _env(
    "GEMINI_MODELO", "gemini-3.8-flash,gemini-flash-latest,gemini-3.5-flash-lite"
).split(",") if m.strip()]
NOME_CANAL = _env("NOME_CANAL", "Histórias da Bíblia")
DURACAO_ALVO = int(min(max(_numero("DURACAO_ALVO_SEG", 60), 20), 170))  # Shorts aceitam até 180 s

# ---- Voz e música -----------------------------------------------------------
VOZ = _env("VOZ", "pt-BR-AntonioNeural")  # outras: pt-BR-FranciscaNeural, pt-BR-ThalitaMultilingualNeural
VELOCIDADE_VOZ = _env("VELOCIDADE_VOZ", "+8%").replace(" ", "").rstrip("%") + "%"
if VELOCIDADE_VOZ[0] not in "+-":
    VELOCIDADE_VOZ = "+" + VELOCIDADE_VOZ
if not VELOCIDADE_VOZ[1:-1].isdigit():
    VELOCIDADE_VOZ = "+8%"
VOLUME_MUSICA = min(_numero("VOLUME_MUSICA", 0.15), 1.0)  # 0 desliga a música

# ---- YouTube automático (opcional; só depois da auditoria da Google, veja o README) ----
YT_ENVIO_AUTOMATICO = _env("YT_ENVIO_AUTOMATICO").lower() in ("sim", "true", "1")
YT_CLIENT_ID = _env("YT_CLIENT_ID")
YT_CLIENT_SECRET = _env("YT_CLIENT_SECRET")
YT_REFRESH_TOKEN = _env("YT_REFRESH_TOKEN")
YT_PRIVACIDADE = _env("YT_PRIVACIDADE", "private")  # usado quando não há YT_HORARIO
# Horários de publicação no YouTube, ex.: "18:00" ou "12:00,18:00". Cada vídeo aprovado
# vai para o próximo horário livre.
YT_HORARIOS = [h.strip() for h in _env("YT_HORARIO").split(",") if h.strip()]

# ---- GitHub (preenchido automaticamente dentro do GitHub Actions) -----------
GITHUB_TOKEN = _env("GITHUB_TOKEN")
GITHUB_REPOSITORY = _env("GITHUB_REPOSITORY")
RELEASE_PREVIAS = "previas"  # onde ficam os vídeos para o painel assistir e baixar

# ---- Reels da Clover para o Instagram (sites-conceito) -----------------------
INSTAGRAM_CTA = _env("INSTAGRAM_CTA", "Peça o seu site")         # botão do cartão final
INSTAGRAM_ARROBA = _env("INSTAGRAM_ARROBA", "@_clover.sd_")       # aparece embaixo do botão

# ---- Painel (site com a fábrica e a fila de aprovação) ----------------------
PAINEL_URL = _env("PAINEL_URL", "https://clover-fabrica.vercel.app")

# ---- Link desta execução no GitHub (para baixar o vídeo se o Telegram recusar) ----
LINK_EXECUCAO = (f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}"
                 f"/actions/runs/{os.environ['GITHUB_RUN_ID']}"
                 if os.environ.get("GITHUB_RUN_ID") else "")

LARGURA, ALTURA, FPS = 1080, 1920, 30
