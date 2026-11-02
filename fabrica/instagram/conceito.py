"""O conceito do site: o Gemini inventa uma marca fictícia do segmento pedido e escreve tudo
(textos, cores, fontes, buscas de fotos e a legenda do Instagram). As fotos vêm de bancos grátis.
"""
import json
import random
import time
import unicodedata
from pathlib import Path

import requests

from .. import config, roteiro
from . import sites

SEGMENTOS = [
    "Barbearia", "Clínica odontológica", "Academia", "Imobiliária", "Pet shop", "Estética automotiva",
    "Advocacia", "Doceria", "Restaurante", "Cafeteria", "Salão de beleza", "Arquitetura", "Psicologia",
    "Escola de idiomas", "Hamburgueria", "Joalheria", "Clínica de estética", "Contabilidade",
    "Oficina mecânica", "Floricultura", "Personal trainer", "Pousada", "Fotografia", "Pizzaria",
    "Estúdio de yoga", "Nutricionista", "Estúdio de tatuagem", "Loja de roupas", "Coworking", "Energia solar",
]

GANCHOS = [
    ("Cliente: “quero um site”", "O site:"),
    ("Cliente: “quero um site”", "A Clover:"),
    ("Cliente: “faz um site simples”", "O site:"),
    ("Cliente: “só um site básico”", "O site:"),
]

UA = {"User-Agent": "clover-fabrica/1.0 (https://github.com/joaofernandesjunior826-art/canaldark)"}

PROMPT = """Você é diretor de criação de uma agência brasileira de sites premium chamada Clover.
Crie o conceito de um site para um negócio FICTÍCIO do segmento: "{segmento}".
Ele vai aparecer num vídeo de 15 segundos no Instagram da Clover, rolando na tela de um notebook,
então precisa impressionar à primeira vista: marca forte, frases curtas, cara de site caro.

Regras:
- Tudo em português do Brasil, com preços em reais quando fizer sentido.
- A marca é inventada (não use nome de empresa real), curta e memorável: até 20 caracteres.
- Respeite os limites de tamanho de cada campo (o texto precisa caber no layout).
- "titulo" do hero: 2 linhas separadas por "|", cada linha com até 13 caracteres. Coloque UMA palavra
  entre asteriscos para destacar (ex.: "Corte de|*respeito.*").
- Cores em hexadecimal com bom contraste. "fundo" pode ser claro (creme, off-white) ou escuro (quase
  preto, verde-floresta, azul-noite); "destaque" é a cor da marca; "superficie" é um tom próximo do
  fundo, para cartões.
- "fonte_titulo" uma destas: {fontes_titulo}. "fonte_texto" uma destas: {fontes_texto}.
- "modelo": "editorial" (claro, elegante), "luxo" (escuro, sofisticado), "impacto" (cores fortes,
  letras gigantes), "minimal" (limpo, centralizado), "revista" (estilo jornal/revista) ou "neon"
  (escuro e tecnológico). Escolha o que combina com o segmento.
- "imagens": buscas EM INGLÊS, de 2 a 4 palavras, por fotos reais e bonitas de banco de imagens que
  combinem com o segmento (pessoas trabalhando, produto, ambiente). Nada de logotipo ou texto.
- "legenda": legenda para o post do Instagram da Clover (até 500 caracteres): uma primeira linha que
  prende, 2 ou 3 frases sobre o site criado para esse segmento, diga que é um projeto conceito da
  Clover e termine com uma chamada para pedir um site (ex.: "Quer um site assim? Chama no direct").
- "hashtags": de 8 a 12, começando com #, em português (inclua #criacaodesites e #webdesign).
{extra}
Responda APENAS com JSON neste formato:
{{"marca": "...", "modelo": "editorial", "cores": {{"fundo": "#...", "texto": "#...", "destaque": "#...", "superficie": "#..."}},
 "fonte_titulo": "...", "fonte_texto": "...", "menu": ["...", "...", "...", "..."],
 "botao": "até 18 caracteres", "botao2": "até 16 caracteres",
 "hero": {{"selo": "até 34 caracteres", "titulo": "linha 1|linha 2", "subtitulo": "até 120 caracteres",
   "prova": "até 30 caracteres, ex.: 4,9 de 860 avaliações", "destaque": "até 7 caracteres", "destaque_sub": "até 18 caracteres",
   "selo_giratorio": "até 18 caracteres"}},
 "palavras": ["4 ou 5 serviços/produtos curtos para uma faixa animada, até 18 caracteres cada"],
 "secao_itens": {{"selo": "até 18 caracteres", "titulo": "até 30 caracteres", "texto": "até 110 caracteres"}},
 "itens": [{{"nome": "até 20 caracteres", "texto": "até 60 caracteres", "preco": "até 16 caracteres"}}, "... 3 itens"],
 "numeros": [{{"valor": "número curto, ex.: 12, 4,9, 98%, 18.000", "rotulo": "até 22 caracteres"}}, "... 4 números"],
 "sobre": {{"selo": "até 18 caracteres", "titulo": "até 34 caracteres", "texto": "até 160 caracteres", "pontos": ["3 itens, até 30 caracteres cada"]}},
 "depoimento": {{"texto": "até 110 caracteres", "autor": "nome e detalhe, até 34 caracteres"}},
 "cta": {{"titulo": "até 36 caracteres", "texto": "até 70 caracteres", "botao": "até 18 caracteres"}},
 "cidade": "cidade, UF",
 "imagens": {{"hero": "...", "itens": ["...", "...", "..."], "sobre": ["...", "..."]}},
 "legenda": "...", "hashtags": ["#..."]}}"""


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def escolher_segmento(pedido: str, recentes: list[str]) -> str:
    """O segmento pedido no painel; sem pedido, um da lista que não saiu nos últimos vídeos."""
    pedido = (pedido or "").strip()
    if pedido:
        for s in SEGMENTOS:
            if _sem_acento(s) == _sem_acento(pedido):
                return s
        return pedido[:60]
    usados = {_sem_acento(r) for r in recentes}
    livres = [s for s in SEGMENTOS if _sem_acento(s) not in usados] or SEGMENTOS
    return random.choice(livres)


# ---- ficha do site ------------------------------------------------------------
def _corta(texto, limite: int) -> str:
    texto = " ".join(str(texto or "").split())
    if len(texto) <= limite:
        return texto
    corte = texto[:limite + 1].rsplit(" ", 1)[0].rstrip(",;:-–")
    return corte if len(corte) >= limite * 0.6 else texto[:limite].rstrip()


def _lista(valor, n: int, padrao: list) -> list:
    itens = [x for x in (valor if isinstance(valor, list) else []) if x]
    return (itens + padrao)[:n] if len(itens) < n else itens[:n]


def validar(f: dict, segmento: str) -> dict:
    """Completa o que faltar e corta o que passar do tamanho (para nada quebrar o layout)."""
    ex = ficha_exemplo()
    g = lambda chave: f.get(chave) if isinstance(f.get(chave), dict) else {}
    hero, sec, sobre, dep, cta = g("hero"), g("secao_itens"), g("sobre"), g("depoimento"), g("cta")
    titulo = str(hero.get("titulo") or ex["hero"]["titulo"])
    if "|" not in titulo:  # sem quebra: divide no meio
        palavras = titulo.split()
        meio = max(1, len(palavras) // 2)
        titulo = " ".join(palavras[:meio]) + "|" + " ".join(palavras[meio:])
    titulo = "|".join(_corta(p, 16) for p in titulo.split("|")[:2])
    itens = []
    for i, it in enumerate(_lista(f.get("itens"), 3, ex["itens"])):
        it = it if isinstance(it, dict) else {}
        itens.append({"nome": _corta(it.get("nome") or ex["itens"][i]["nome"], 22),
                      "texto": _corta(it.get("texto") or "", 70), "preco": _corta(it.get("preco") or "", 18)})
    numeros = []
    for i, n in enumerate(_lista(f.get("numeros"), 4, ex["numeros"])):
        n = n if isinstance(n, dict) else {}
        valor = _corta(n.get("valor") or ex["numeros"][i]["valor"], 8)
        numeros.append({"valor": valor, "rotulo": _corta(n.get("rotulo") or "", 24)})
    imagens = f.get("imagens") if isinstance(f.get("imagens"), dict) else {}
    hashtags = [("#" + h.lstrip("#")).replace(" ", "") for h in f.get("hashtags") or [] if str(h).strip()][:12]
    for h in ("#criacaodesites", "#webdesign"):
        if h not in hashtags:
            hashtags.append(h)
    modelo = f.get("modelo") if f.get("modelo") in sites.MODELOS else "editorial"
    return {
        "segmento": segmento,
        "marca": _corta(f.get("marca") or "Marca Nova", 22),
        "modelo": modelo,
        "cores": f.get("cores") if isinstance(f.get("cores"), dict) else ex["cores"],
        "fonte_titulo": f.get("fonte_titulo"), "fonte_texto": f.get("fonte_texto"),
        "menu": [_corta(m, 14) for m in _lista(f.get("menu"), 4, ex["menu"])],
        "botao": _corta(f.get("botao") or "Fale conosco", 20),
        "botao2": _corta(f.get("botao2") or "Saiba mais", 18),
        "hero": {"selo": _corta(hero.get("selo") or segmento, 36), "titulo": titulo,
                 "subtitulo": _corta(hero.get("subtitulo") or "", 130), "prova": _corta(hero.get("prova") or "", 32),
                 "destaque": _corta(hero.get("destaque") or "24h", 8), "destaque_sub": _corta(hero.get("destaque_sub") or "", 20),
                 "selo_giratorio": _corta(hero.get("selo_giratorio") or f.get("marca") or "", 20)},
        "palavras": [_corta(p, 20) for p in _lista(f.get("palavras"), 5, ex["palavras"])],
        "secao_itens": {"selo": _corta(sec.get("selo") or "Serviços", 20), "titulo": _corta(sec.get("titulo") or "", 34),
                        "texto": _corta(sec.get("texto") or "", 120)},
        "itens": itens, "numeros": numeros,
        "sobre": {"selo": _corta(sobre.get("selo") or "Sobre", 20), "titulo": _corta(sobre.get("titulo") or "", 38),
                  "texto": _corta(sobre.get("texto") or "", 170),
                  "pontos": [_corta(p, 32) for p in _lista(sobre.get("pontos"), 3, ex["sobre"]["pontos"])]},
        "depoimento": {"texto": _corta(dep.get("texto") or ex["depoimento"]["texto"], 120),
                       "autor": _corta(dep.get("autor") or "Cliente", 36)},
        "cta": {"titulo": _corta(cta.get("titulo") or "Vamos começar?", 40), "texto": _corta(cta.get("texto") or "", 80),
                "botao": _corta(cta.get("botao") or f.get("botao") or "Fale conosco", 20)},
        "cidade": _corta(f.get("cidade") or "São Paulo, SP", 30),
        "imagens": {"hero": str(imagens.get("hero") or segmento),
                    "itens": [str(x) for x in _lista(imagens.get("itens"), 3, [segmento] * 3)],
                    "sobre": [str(x) for x in _lista(imagens.get("sobre"), 2, [segmento] * 2)]},
        "legenda": str(f.get("legenda") or "").strip()[:900],
        "hashtags": hashtags,
    }


def ficha_exemplo() -> dict:
    return json.loads((Path(__file__).with_name("ficha_exemplo.json")).read_text(encoding="utf-8"))


def gerar_ficha(segmento: str, ajuste: str = "", recentes: list[str] | None = None) -> dict:
    extra = []
    if recentes:
        extra.append("- Não repita estas marcas já usadas: " + "; ".join(recentes[-10:]) + ".")
    if ajuste:
        extra.append(f"- PEDIDO DE AJUSTE (siga com prioridade): {ajuste}")
    prompt = PROMPT.format(segmento=segmento, fontes_titulo=", ".join(sites.FONTES_TITULO),
                           fontes_texto=", ".join(sites.FONTES_TEXTO), extra="\n".join(extra))
    return validar(roteiro._chamar_gemini(prompt), segmento)


# ---- fotos --------------------------------------------------------------------
def _pixabay(busca: str, vertical: bool, usados: set) -> str | None:
    r = requests.get("https://pixabay.com/api/", timeout=30, params={
        "key": config.PIXABAY_API_KEY, "q": busca[:100], "image_type": "photo", "safesearch": "true",
        "orientation": "vertical" if vertical else "horizontal", "per_page": 30, "min_width": 1000})
    if r.status_code != 200:
        print(f"Pixabay respondeu {r.status_code} para “{busca}”.")
        return None
    fotos = [h for h in r.json().get("hits", []) if f"pixabay:{h['id']}" not in usados]
    if not fotos:
        return None
    foto = random.choice(fotos[:6])
    usados.add(f"pixabay:{foto['id']}")
    return foto.get("largeImageURL") or foto.get("webformatURL")


def _pexels(busca: str, vertical: bool, usados: set) -> str | None:
    r = requests.get("https://api.pexels.com/v1/search", timeout=30, headers={"Authorization": config.PEXELS_API_KEY},
                     params={"query": busca[:100], "orientation": "portrait" if vertical else "landscape", "per_page": 20})
    if r.status_code != 200:
        print(f"Pexels respondeu {r.status_code} para “{busca}”.")
        return None
    fotos = [f for f in r.json().get("photos", []) if f"pexels:{f['id']}" not in usados]
    if not fotos:
        return None
    foto = random.choice(fotos[:6])
    usados.add(f"pexels:{foto['id']}")
    return foto["src"].get("large2x") or foto["src"].get("large")


def _openverse(busca: str, vertical: bool, usados: set) -> str | None:
    """Fotos de bancos com licença livre (StockSnap, Nappy, Rawpixel), sem precisar de chave."""
    r = requests.get("https://api.openverse.org/v1/images/", timeout=(6, 15), headers=UA, params={
        "q": busca[:100], "license": "cc0,pdm", "source": "stocksnap,nappy,rawpixel", "page_size": 20,
        "mature": "false", "aspect_ratio": "tall" if vertical else "wide"})
    if r.status_code != 200:
        raise requests.RequestException(f"Openverse respondeu {r.status_code}")
    fotos = [f for f in r.json().get("results", []) if f.get("url") and f"ov:{f['id']}" not in usados
             and (f.get("width") or 0) >= 900]
    if not fotos:
        return None
    foto = random.choice(fotos[:5])
    usados.add(f"ov:{foto['id']}")
    return foto["url"]


def _baixar(url: str, destino: Path) -> bool:
    try:
        r = requests.get(url, timeout=60, headers=UA)
        if r.status_code == 200 and len(r.content) > 20_000 and r.content[:3] in (b"\xff\xd8\xff", b"\x89PN"):
            destino.write_bytes(r.content)
            return True
    except requests.RequestException as e:
        print(f"Não consegui baixar uma foto: {e}")
    return False


def baixar_imagens(ficha: dict, pasta: Path, segmento_en: str = "") -> dict:
    """Baixa as fotos do site para pasta/img/. Devolve {vaga: "img/arquivo.jpg"} (vagas sem foto ficam de fora)."""
    (pasta / "img").mkdir(exist_ok=True)
    buscas = ficha["imagens"]
    vagas = [("hero", buscas["hero"], True)] + \
            [(f"item{i}", b, False) for i, b in enumerate(buscas["itens"])] + \
            [("sobre0", buscas["sobre"][0], True), ("sobre1", buscas["sobre"][1], False)]
    fontes = []
    if config.PIXABAY_API_KEY:
        fontes.append(("Pixabay", _pixabay))
    if config.PEXELS_API_KEY:
        fontes.append(("Pexels", _pexels))
    fontes.append(("Openverse", _openverse))
    usados, saida, origem, fora = set(), {}, {}, set()
    limite = time.time() + 150  # no máximo 2,5 minutos procurando fotos
    for vaga, busca, vertical in vagas:
        reservas = [busca, " ".join(busca.split()[:2]), segmento_en or busca.split()[0]]
        for nome, fonte in fontes:
            if nome in fora or time.time() > limite:
                continue
            url = None
            for termo in dict.fromkeys(t for t in reservas if t):
                try:
                    url = fonte(termo, vertical, usados)
                except (requests.RequestException, ValueError, KeyError) as e:
                    print(f"{nome} não respondeu ({str(e)[:120]}); sigo sem ele.")
                    fora.add(nome)  # banco fora do ar: não insiste nas outras fotos
                    break
                if url:
                    break
            arquivo = pasta / "img" / f"{vaga}.jpg"
            if url and _baixar(url, arquivo):
                saida[vaga] = f"img/{vaga}.jpg"
                origem[nome] = origem.get(nome, 0) + 1
                break
    print(f"Fotos do site: {len(saida)} de {len(vagas)} ({', '.join(f'{n} {q}' for n, q in origem.items()) or 'nenhuma'})")
    return saida


def legenda_completa(ficha: dict) -> str:
    texto = ficha.get("legenda") or (f"Um site para {ficha['segmento'].lower()} que vende sozinho. "
                                     f"Projeto conceito da Clover para a marca fictícia {ficha['marca']}.\n\n"
                                     "Quer um site assim para o seu negócio? Chama no direct.")
    tags = " ".join(ficha.get("hashtags") or [])
    return f"{texto}\n\n{tags}".strip()


def busca_em_ingles(segmento: str) -> str:
    """Tradução simples do segmento para a busca de fotos de reserva."""
    mapa = {"barbearia": "barbershop", "clinica odontologica": "dentist", "academia": "gym", "imobiliaria": "real estate",
            "pet shop": "pet grooming", "estetica automotiva": "car detailing", "advocacia": "lawyer office",
            "doceria": "pastry", "restaurante": "restaurant", "cafeteria": "coffee shop", "salao de beleza": "hair salon",
            "arquitetura": "architecture interior", "psicologia": "therapy", "escola de idiomas": "language class",
            "hamburgueria": "burger", "joalheria": "jewelry", "clinica de estetica": "skincare spa",
            "contabilidade": "accounting office", "oficina mecanica": "car mechanic", "floricultura": "flower shop",
            "personal trainer": "personal trainer", "pousada": "boutique hotel", "fotografia": "photographer",
            "pizzaria": "pizza", "estudio de yoga": "yoga", "nutricionista": "healthy food", "estudio de tatuagem": "tattoo",
            "loja de roupas": "fashion store", "coworking": "coworking", "energia solar": "solar panels"}
    return mapa.get(_sem_acento(segmento), "")


def gancho(semente: int | None = None) -> tuple[str, str]:
    return random.Random(semente).choice(GANCHOS)


def recentes_do_historico(historico: list[dict]) -> tuple[list[str], list[str]]:
    """(segmentos, marcas) dos últimos Reels, para variar."""
    reels = [v for v in historico if v.get("tipo") == "instagram"][-12:]
    return [v.get("segmento", "") for v in reels], [v.get("marca", "") for v in reels]

