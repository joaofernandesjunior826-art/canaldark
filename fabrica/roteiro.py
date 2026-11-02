"""Etapa 1: escolhe a história e escreve o roteiro com a API gratuita do Gemini."""
import json
import time
import unicodedata

import requests

from . import config, estado

URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"

PROMPT = """Você é roteirista de um canal brasileiro de YouTube Shorts chamado "{canal}",
que conta histórias da Bíblia de forma envolvente, respeitosa e fiel ao texto bíblico.

Escreva o roteiro de um Short sobre: "{titulo}"{ref_txt}.

Regras:
- Narração em português do Brasil, para ser lida em voz alta em cerca de {duracao} segundos
  (aproximadamente {palavras} palavras no total, somando todas as cenas).
- A primeira frase é um gancho forte que prende nos 2 primeiros segundos (pergunta intrigante,
  fato surpreendente ou momento de tensão). Não comece com "Olá", "Você sabia" nem com o nome do canal.
- Conte a história em ordem, com tensão e emoção, em frases curtas e fáceis de ouvir.
- Seja fiel ao texto bíblico: não invente fatos, nomes nem falas que não estejam na Bíblia.
- Mencione a referência bíblica uma vez, de forma natural.
- Escreva números e referências por extenso, do jeito que devem ser falados
  (ex.: "Primeiro Samuel, capítulo dezessete"; "trezentos homens").
- Termine com uma lição curta e uma chamada simples para seguir o canal.
- Divida a narração em {cenas} cenas, cada uma com 1 ou 2 frases.
- Para cada cena, escolha o fundo em "visual":
  - "pintura" quando a cena mostra personagens ou um momento da história. Em "arte", escreva de 2 a 5
    palavras EM INGLÊS para achar uma pintura clássica desse momento (ex.: "David slingshot Goliath
    painting", "Moses parting Red Sea painting", "Noah ark animals painting"). Nada violento demais.
  - "paisagem" para cenas de clima, natureza ou reflexão. Em "busca", escreva de 2 a 4 palavras EM
    INGLÊS para um vídeo de banco de imagens (céu, deserto, mar, fogo, cidade antiga, luz, silhuetas).
  Use "pintura" em pelo menos metade das cenas e preencha sempre "arte" e "busca" (servem de reserva).
- "arte_geral": de 2 a 4 palavras EM INGLÊS com o nome da história, para buscar pinturas (ex.: "David and Goliath").
- "titulo": até 70 caracteres, chamativo e verdadeiro, sem caixa alta exagerada e sem hashtags.
- "descricao": 2 ou 3 frases resumindo a história, com a referência bíblica e de 3 a 5 hashtags
  no final (inclua #Shorts e #Bíblia).
- "tags": de 5 a 10 palavras-chave, sem "#".
- "capa": até 4 palavras de impacto, que aparecem no topo do vídeo nos primeiros segundos.
- "referencia": a passagem bíblica, no formato "1 Samuel 17".
{extra}
Responda APENAS com JSON neste formato:
{{"titulo": "...", "descricao": "...", "tags": ["..."], "capa": "...", "referencia": "...", "arte_geral": "...",
  "cenas": [{{"texto": "...", "visual": "pintura", "arte": "...", "busca": "..."}}]}}"""

SEGURANCA = [{"category": c, "threshold": "BLOCK_ONLY_HIGH"} for c in (
    "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")]


# ---- Escolha da história ----------------------------------------------------
def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def lista_de_historias() -> list[tuple[str, str]]:
    historias = []
    for linha in (config.DADOS / "historias.txt").read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#"):
            titulo, _, ref = linha.partition("|")
            historias.append((titulo.strip(), ref.strip()))
    return historias


def achar_historia(tema: str) -> tuple[str, str] | None:
    """Procura o tema na lista (sem ligar para acentos). Devolve (título, referência)."""
    alvo = _normalizar(tema)
    for titulo, ref in lista_de_historias():
        if alvo == _normalizar(titulo) or (len(alvo) >= 5 and alvo in _normalizar(titulo)):
            return titulo, ref
    return None


def proxima_historia() -> tuple[str, str]:
    historias = lista_de_historias()
    feitos = [v.get("historia") for v in estado.historico()]
    for titulo, ref in historias:
        if titulo not in feitos:
            return titulo, ref
    # A lista acabou: recomeça pela história feita há mais tempo (com roteiro novo).
    print("Todas as histórias da lista já viraram vídeo; recomeçando pela mais antiga.")
    ultima_vez = {t: max((i for i, f in enumerate(feitos) if f == t), default=-1) for t, _ in historias}
    return min(historias, key=lambda h: ultima_vez[h[0]])


# ---- Gemini -----------------------------------------------------------------
def _chamar_gemini(prompt: str) -> dict:
    if not config.GEMINI_API_KEY:
        raise RuntimeError("Falta cadastrar o segredo GEMINI_API_KEY no GitHub.")
    corpo = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
        "safetySettings": SEGURANCA,
    }
    ultimo_erro = "nenhum modelo configurado"
    for modelo in config.GEMINI_MODELOS:
        for tentativa in range(3):
            try:
                r = requests.post(URL.format(modelo=modelo), json=corpo, timeout=180,
                                  headers={"x-goog-api-key": config.GEMINI_API_KEY})
            except requests.RequestException as e:
                ultimo_erro = f"{modelo}: {e}"
                time.sleep(10)
                continue
            if r.status_code == 200:
                try:
                    candidato = r.json()["candidates"][0]
                    texto = "".join(p.get("text", "") for p in candidato["content"]["parts"]).strip()
                    texto = texto.removeprefix("```json").removeprefix("```").removesuffix("```")
                    roteiro = json.loads(texto)
                    print(f"Roteiro escrito pelo {modelo}.")
                    return roteiro
                except (KeyError, IndexError, ValueError) as e:
                    ultimo_erro = f"{modelo}: resposta inválida ({e})"
                    print(ultimo_erro)
                    continue  # pede de novo ao mesmo modelo
            ultimo_erro = f"{modelo}: HTTP {r.status_code} {r.text[:300]}"
            print("Gemini falhou:", ultimo_erro)
            if r.status_code == 429 and "limit: 0" not in r.text and tentativa == 0:
                time.sleep(30)  # limite por minuto: espera um pouco e tenta de novo
                continue
            if r.status_code in (500, 502, 503, 504) and tentativa == 0:
                time.sleep(8)  # modelo sobrecarregado: tenta mais uma vez e depois passa para o próximo
                continue
            break  # sem cota, sobrecarregado, modelo inexistente ou chave errada: tenta o próximo modelo
    raise RuntimeError(f"O Gemini não conseguiu escrever o roteiro. Último erro: {ultimo_erro}")


def gerar_roteiro(titulo: str, referencia: str, ajuste: str = "", recentes: list[str] | None = None) -> dict:
    palavras = int(config.DURACAO_ALVO * 2.6)
    cenas = max(6, min(16, config.DURACAO_ALVO // 5))
    extra = []
    if recentes:
        extra.append("- Para o canal não ficar repetitivo, use um gancho e uma estrutura diferentes "
                     "destes títulos recentes: " + "; ".join(f'"{t}"' for t in recentes) + ".")
    if ajuste:
        extra.append(f'- PEDIDO DE AJUSTE DO REVISOR (prioridade máxima, aplique sem fugir da Bíblia): "{ajuste}"')
    prompt = PROMPT.format(
        canal=config.NOME_CANAL, titulo=titulo,
        ref_txt=f" ({referencia})" if referencia else " (identifique a passagem bíblica certa)",
        duracao=config.DURACAO_ALVO, palavras=palavras, cenas=cenas, extra="\n".join(extra))
    roteiro = _chamar_gemini(prompt)

    cenas_ok = []
    for c in roteiro.get("cenas") or []:
        if isinstance(c, dict) and str(c.get("texto", "")).strip():
            cenas_ok.append({"texto": str(c["texto"]).strip(),
                             "visual": "paisagem" if str(c.get("visual", "")).lower().startswith("pais") else "pintura",
                             "arte": str(c.get("arte") or "").strip()[:80],
                             "busca": str(c.get("busca") or "dramatic sky clouds").strip()[:80]})
    if not cenas_ok:
        raise RuntimeError("O Gemini devolveu um roteiro sem cenas.")
    total = sum(len(c["texto"].split()) for c in cenas_ok)
    print(f"Roteiro com {len(cenas_ok)} cenas e {total} palavras (alvo ~{palavras}).")

    titulo_video = str(roteiro.get("titulo") or titulo).replace("<", "").replace(">", "").strip()
    tags = [str(t).lstrip("#").strip() for t in (roteiro.get("tags") or []) if str(t).strip()]
    return {
        "historia": titulo,
        "referencia": str(roteiro.get("referencia") or referencia).strip(),
        "titulo": titulo_video[:100],
        "descricao": str(roteiro.get("descricao") or "").replace("<", "").replace(">", "").strip(),
        "tags": tags[:15],
        "capa": str(roteiro.get("capa") or "").strip()[:40],
        "arte_geral": str(roteiro.get("arte_geral") or "").strip()[:60],
        "cenas": cenas_ok,
    }
