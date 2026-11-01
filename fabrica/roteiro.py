"""Etapa 1: escolhe a história e escreve o roteiro com a API gratuita do Gemini."""
import json
import time

import requests

from . import config

URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"

PROMPT = """Você é roteirista de um canal brasileiro de YouTube Shorts chamado "{canal}",
que conta histórias da Bíblia de forma envolvente, respeitosa e fiel ao texto bíblico.

Escreva o roteiro de um Short sobre: "{titulo}" ({referencia}).

Regras:
- Narração em português do Brasil, para ser lida em voz alta em cerca de {duracao} segundos
  (aproximadamente {palavras} palavras no total).
- A primeira frase é um gancho forte que prende nos 2 primeiros segundos (pergunta, fato
  surpreendente ou momento de tensão). Não comece com "Olá" nem com o nome do canal.
- Conte a história em ordem, com tensão e emoção, frases curtas e fáceis de ouvir.
- Seja fiel ao texto bíblico; não invente fatos. Cite a referência ({referencia}) de forma natural.
- Termine com uma lição curta e uma chamada simples (ex.: "Siga para mais histórias da Bíblia").
- Divida a narração em {cenas} cenas. Cada cena tem 1 a 3 frases.
- Para cada cena, dê "busca": 2 a 4 palavras EM INGLÊS para buscar um vídeo de banco de imagens
  que combine com o clima (paisagens, natureza, céu, deserto, mar, fogo, cidade antiga, luz,
  mãos, silhuetas). Evite pedir rostos, pessoas específicas ou coisas modernas.
- Título com até 70 caracteres, chamativo e verdadeiro, sem caixa alta exagerada.
- Descrição com 2 a 3 frases, a referência bíblica e 3 a 5 hashtags (inclua #Shorts e #Bíblia).
- "capa": até 4 palavras de impacto para a capa do vídeo.

Responda APENAS com JSON neste formato:
{{
  "titulo": "...",
  "descricao": "...",
  "tags": ["...", "..."],
  "capa": "...",
  "cenas": [{{"texto": "...", "busca": "..."}}]
}}"""


def proxima_historia() -> tuple[str, str]:
    historico = carregar_historico()
    usadas = {h["historia"] for h in historico}
    linhas = (config.DADOS / "historias.txt").read_text(encoding="utf-8").splitlines()
    historias = []
    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        titulo, _, ref = linha.partition("|")
        historias.append((titulo.strip(), ref.strip()))
    for titulo, ref in historias:
        if titulo not in usadas:
            return titulo, ref
    # Acabou a lista: recomeça pela história usada há mais tempo.
    print("Todas as histórias já foram usadas; recomeçando pela mais antiga.")
    mais_antiga = historico[0]["historia"]
    return next((t, r) for t, r in historias if t == mais_antiga)


def carregar_historico() -> list:
    arq = config.DADOS / "historico.json"
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else []


def registrar_historico(item: dict) -> None:
    historico = [h for h in carregar_historico() if h["historia"] != item["historia"]]
    historico.append(item)
    (config.DADOS / "historico.json").write_text(
        json.dumps(historico, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _chamar_gemini(prompt: str) -> dict:
    if not config.GEMINI_API_KEY:
        raise RuntimeError("Falta o segredo GEMINI_API_KEY.")
    corpo = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9},
    }
    ultimo_erro = None
    for modelo in config.GEMINI_MODELOS:
        for tentativa in range(3):
            r = requests.post(URL.format(modelo=modelo), json=corpo, timeout=120,
                              headers={"x-goog-api-key": config.GEMINI_API_KEY})
            if r.status_code == 200:
                partes = r.json()["candidates"][0]["content"]["parts"]
                texto = "".join(p.get("text", "") for p in partes).strip()
                texto = texto.removeprefix("```json").removeprefix("```").removesuffix("```")
                print(f"Roteiro gerado com {modelo}.")
                return json.loads(texto)
            ultimo_erro = f"{modelo}: HTTP {r.status_code} {r.text[:300]}"
            print("Gemini falhou:", ultimo_erro)
            if r.status_code in (429, 500, 503):
                time.sleep(20 * (tentativa + 1))
                continue
            break  # modelo inexistente ou erro de chave: tenta o próximo modelo
    raise RuntimeError(f"Não consegui gerar o roteiro. Último erro: {ultimo_erro}")


def gerar_roteiro(titulo: str, referencia: str) -> dict:
    palavras = int(config.DURACAO_ALVO * 2.6)
    cenas = max(5, min(14, config.DURACAO_ALVO // 6))
    prompt = PROMPT.format(canal=config.NOME_CANAL, titulo=titulo, referencia=referencia,
                           duracao=config.DURACAO_ALVO, palavras=palavras, cenas=cenas)
    roteiro = _chamar_gemini(prompt)
    roteiro["cenas"] = [c for c in roteiro.get("cenas", []) if c.get("texto", "").strip()]
    if not roteiro["cenas"]:
        raise RuntimeError("O Gemini devolveu um roteiro sem cenas.")
    tags = roteiro.get("tags") or []
    roteiro["tags"] = [t.lstrip("#") for t in tags][:15]
    roteiro["titulo"] = (roteiro.get("titulo") or titulo)[:100]
    roteiro["historia"] = titulo
    roteiro["referencia"] = referencia
    return roteiro
