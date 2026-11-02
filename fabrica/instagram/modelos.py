"""Mais quatro modelos de site, bem diferentes entre si (os dois primeiros estão em sites.py).

impacto    fundo colorido, letras gigantes em caixa alta, foto em pílula, grade de blocos (bento)
minimal    claro e centralizado, vitrine de foto grande, recursos com ícones e passos
revista    jornal/revista: manchete enorme, faixa de fotos, colunas numeradas e citação
neon       escuro e tecnológico: brilhos, painel de app com gráfico, cartões de vidro
"""
from .sites import _e, _estrelas, _img, _linhas_titulo, _rico

ICONES_EXTRA = {
    "raio": '<path d="M13 2.5L5 13.5h6l-1 8 8-11h-6z"/>',
    "escudo": '<path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.3-7.5 9.5-4.3-1.2-7.5-4.9-7.5-9.5V6z"/><path d="M8.8 12.2l2.3 2.3 4.3-4.6"/>',
    "coracao": '<path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0112 7.3 4.3 4.3 0 0119.5 10c0 5.4-7.5 10-7.5 10z"/>',
    "grafico": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
}


def _ic(nome: str) -> str:
    from .sites import _ICONES
    caminho = ICONES_EXTRA.get(nome) or _ICONES.get(nome, "")
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{caminho}</svg>')


def _partes_titulo(texto: str) -> list[str]:
    return [p.strip() for p in str(texto).split("|") if p.strip()] or [str(texto)]


def _letreiro(s: dict, separador: str = "✦") -> str:
    return "".join(f"<span>{_e(p)}</span><b>{separador}</b>" for p in s["palavras"]) * 4


# ==== impacto ==================================================================
CSS_IMPACTO = """
.nav{background:var(--destaque);color:var(--sobre-destaque);border-bottom:2px solid color-mix(in srgb,var(--sobre-destaque) 25%,transparent)}
.nav nav{color:color-mix(in srgb,var(--sobre-destaque) 75%,transparent)} .nav nav a:first-child{color:var(--sobre-destaque)}
.nav .logo i{background:var(--sobre-destaque);color:var(--destaque)} .nav .botao{background:var(--texto);color:var(--fundo)}
h1,h2,h3,.num{text-transform:uppercase}
.imp-hero{position:relative;overflow:hidden;background:var(--destaque);color:var(--sobre-destaque);height:calc(100vh - 87px);
  display:flex;flex-direction:column;justify-content:center;padding:0 56px}
.imp-hero h1{font-size:136px;line-height:.9;letter-spacing:-.055em}
.imp-hero h1 em{color:var(--texto);font-style:normal}
.pilula{display:inline-block;width:250px;height:112px;border-radius:999px;overflow:hidden;vertical-align:middle;margin:0 18px 14px 0;border:4px solid var(--sobre-destaque)}
.imp-hero .rodape{display:flex;justify-content:space-between;align-items:flex-end;gap:40px;margin-top:36px}
.imp-hero p{max-width:470px;font-size:20px;opacity:.92}
.imp-hero .botao{background:var(--texto);color:var(--fundo);font-size:18px;padding:20px 34px}
.adesivo{position:absolute;right:64px;top:46px;width:178px;height:178px;border-radius:50%;background:var(--texto);color:var(--fundo);
  display:grid;place-items:center;text-align:center;font-weight:800;font-size:21px;line-height:1.05;text-transform:uppercase;padding:18px}
.adesivo b{display:block;font-family:var(--f-titulo);font-size:44px}
.letreiro.escuro{background:var(--texto);color:var(--fundo)}
.letreiro.escuro div{text-transform:uppercase;font-size:40px}
.bento{padding:64px 56px 40px;display:grid;grid-template-columns:1.25fr 1fr 1fr;grid-template-rows:290px 290px;gap:18px}
.bento .t{position:relative;overflow:hidden;border-radius:30px;padding:28px;display:flex;flex-direction:column;justify-content:flex-end}
.bento .t.foto{padding:0}.bento .t.alto{grid-row:span 2}
.bento .t.cor{background:var(--destaque);color:var(--sobre-destaque)}
.bento .t.escuro{background:var(--texto);color:var(--fundo)}
.bento .t.claro{background:var(--superficie)}
.bento .t .rotulo{position:absolute;left:22px;bottom:22px;z-index:1;background:var(--fundo);color:var(--texto);font-weight:800;text-transform:uppercase;
  padding:10px 18px;border-radius:999px;font-size:16px}
.bento .num{font-size:92px;line-height:.9}
.bento h3{font-size:34px;line-height:.95}
.bento p{opacity:.8;margin-top:8px;font-size:16px}
.lista-num{padding:56px 56px 40px}
.lista-num h2{font-size:92px;letter-spacing:-.05em;line-height:.9;margin-bottom:26px}
.item-num{display:grid;grid-template-columns:110px 1fr auto;align-items:center;gap:26px;padding:24px 0;border-top:3px solid var(--texto)}
.item-num .n{font-family:var(--f-titulo);font-size:54px;font-weight:800;color:var(--destaque)}
.item-num h3{font-size:44px;letter-spacing:-.03em}
.item-num p{color:var(--suave);font-size:16px;margin-top:4px}
.item-num .preco{font-family:var(--f-titulo);font-size:30px;font-weight:800;background:var(--destaque);color:var(--sobre-destaque);padding:10px 20px;border-radius:999px}
.imp-depo{background:var(--texto);color:var(--fundo);padding:96px 56px}
.imp-depo blockquote{font-family:var(--f-titulo);font-size:64px;line-height:1.02;text-transform:uppercase;letter-spacing:-.045em;font-weight:800;max-width:1120px}
.imp-depo cite{display:block;margin-top:26px;font-style:normal;opacity:.7}
.imp-cta{padding:80px 56px 90px;text-align:center;position:relative;overflow:hidden}
.imp-cta h2{font-size:118px;letter-spacing:-.06em;line-height:.88;max-width:1100px;margin:0 auto 34px}
.imp-cta .botao{font-size:20px;padding:22px 40px}
"""


def impacto(s: dict, img: dict) -> str:
    h = s["hero"]
    l1, *resto = _partes_titulo(h["titulo"])
    l2 = " ".join(resto)
    i0, i1 = s["itens"][0], s["itens"][1]
    n = s["numeros"]
    itens = "".join(
        f'<div class="item-num alvo" data-revela="esquerda" data-atraso="{i * 0.12:.2f}"><span class="n">{i + 1:02d}</span>'
        f'<div><h3>{_e(it["nome"])}</h3><p>{_e(it["texto"])}</p></div><span class="preco">{_e(it.get("preco", ""))}</span></div>'
        for i, it in enumerate(s["itens"][:3]))
    return f"""
<section class="imp-hero" data-parada="0">
  <div class="adesivo" data-revela="zoom" data-atraso=".5"><span><b>{_e(n[2]["valor"])}</b>{_e(n[2]["rotulo"])}</span></div>
  <h1><span class="linha"><span data-revela="linha" data-atraso=".05">{_rico(l1)}</span></span>
    <span class="linha"><span data-revela="linha" data-atraso=".2"><span class="pilula">{_img(img, "hero", alt=s["marca"], extra="data-kenburns")}</span>{_rico(l2)}</span></span></h1>
  <div class="rodape"><p data-revela="sobe" data-atraso=".45">{_e(h["subtitulo"])}</p>
    <a class="botao" data-revela="zoom" data-atraso=".6">{_e(s["botao"])} {_ic("seta")}</a></div>
</section>
<div class="letreiro escuro"><div data-letreiro="90">{_letreiro(s, "●")}</div></div>
<section class="bento" data-parada="0">
  <div class="t foto alto alvo" data-revela="imagem">{_img(img, "item0", alt=i0["nome"], extra="data-paralaxe")}<span class="rotulo">{_e(i0["nome"])}</span></div>
  <div class="t cor alvo" data-revela="3d" data-atraso=".1"><div class="num" data-conta="{_e(n[0]["valor"])}">{_e(n[0]["valor"])}</div><p>{_e(n[0]["rotulo"])}</p></div>
  <div class="t foto alvo" data-revela="imagem" data-atraso=".2">{_img(img, "item1", alt=i1["nome"], extra="data-paralaxe")}<span class="rotulo">{_e(i1["nome"])}</span></div>
  <div class="t escuro alvo" data-revela="3d" data-atraso=".25"><h3>{_rico(s["sobre"]["titulo"])}</h3><p>{_e(s["sobre"]["texto"][:90])}</p></div>
  <div class="t claro alvo" data-revela="3d" data-atraso=".35"><div class="num" data-conta="{_e(n[1]["valor"])}">{_e(n[1]["valor"])}</div><p>{_e(n[1]["rotulo"])}</p></div>
</section>
<section class="lista-num" data-parada="0">
  <h2 data-revela="palavras">{_rico(s["secao_itens"]["titulo"])}</h2>{itens}
</section>
<section class="imp-depo" data-parada="0">
  <blockquote data-revela="palavras">{_e(s["depoimento"]["texto"])}</blockquote>
  <cite data-revela="sobe" data-atraso=".3">{_estrelas()} {_e(s["depoimento"]["autor"])}</cite>
</section>
<section class="imp-cta" data-parada="40">
  <h2 data-revela="palavras">{_rico(s["cta"]["titulo"])}</h2>
  <a class="botao" data-revela="zoom" data-atraso=".3">{_e(s["cta"].get("botao") or s["botao"])} {_ic("seta")}</a>
</section>"""


# ==== minimal ==================================================================
CSS_MINIMAL = """
.nav{background:color-mix(in srgb,var(--fundo) 88%,transparent)}
.min-hero{text-align:center;padding:64px 64px 0}
.selo-pilula{display:inline-flex;align-items:center;gap:10px;padding:9px 18px;border-radius:999px;background:var(--superficie);font-size:15px;font-weight:600}
.selo-pilula i{width:9px;height:9px;border-radius:50%;background:var(--destaque);box-shadow:0 0 0 5px color-mix(in srgb,var(--destaque) 22%,transparent)}
.min-hero h1{font-size:100px;letter-spacing:-.05em;line-height:.95;margin:26px auto 20px;max-width:1020px}
.min-hero .lead{font-size:21px;color:var(--suave);max-width:640px;margin:0 auto}
.min-hero .acoes{display:flex;justify-content:center;gap:14px;margin-top:30px}
.vitrine{position:relative;margin:46px auto 0;width:1060px;height:440px;border-radius:34px;overflow:hidden;box-shadow:0 50px 90px -50px rgba(0,0,0,.55)}
.vitrine .cartao-flut{position:absolute;left:28px;bottom:28px;z-index:1;background:var(--fundo);border-radius:20px;padding:16px 20px;display:flex;gap:14px;
  align-items:center;box-shadow:0 20px 40px -20px rgba(0,0,0,.5);text-align:left;font-size:15px}
.vitrine .cartao-flut b{display:block;font-family:var(--f-titulo);font-size:24px}
.marcas{display:flex;justify-content:center;flex-wrap:wrap;gap:20px 56px;padding:46px 64px;color:var(--suave);font-weight:800;font-size:20px;
  letter-spacing:.14em;text-transform:uppercase;border-bottom:1px solid var(--linha)}
.recursos{padding:76px 64px 56px}
.recursos .cabeca-c{text-align:center;margin-bottom:40px}
.recursos h2{font-size:70px;letter-spacing:-.045em;max-width:900px;margin:12px auto 0}
.recursos .grade{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.recurso{padding:34px 30px;border-radius:28px;border:1px solid var(--linha);background:var(--fundo)}
.recurso .ic{width:58px;height:58px;border-radius:18px;background:color-mix(in srgb,var(--destaque) 15%,transparent);color:var(--destaque);
  display:grid;place-items:center;margin-bottom:22px}
.recurso .ic svg{width:28px;height:28px}
.recurso h3{font-size:30px;letter-spacing:-.03em;margin-bottom:10px}
.recurso p{color:var(--suave);font-size:16.5px}
.recurso .preco{display:inline-block;margin-top:16px;font-weight:700;color:var(--destaque)}
.alterna{padding:56px 64px;display:grid;grid-template-columns:1.05fr .95fr;gap:64px;align-items:center}
.alterna .foto{height:540px;border-radius:34px;overflow:hidden}
.alterna h2{font-size:66px;letter-spacing:-.045em;margin:14px 0 18px}
.alterna p{color:var(--suave);font-size:19px}
.passos{display:grid;gap:14px;margin-top:28px}
.passo{display:flex;gap:16px;align-items:center;padding:16px 18px;border-radius:18px;background:var(--superficie);font-weight:600;font-size:18px}
.passo b{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;background:var(--texto);color:var(--fundo);font-size:16px}
.min-numeros{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin:20px 64px;text-align:center}
.min-numeros .num{font-size:72px;letter-spacing:-.05em}
.min-numeros p{color:var(--suave)}
.min-cta{margin:50px 64px 80px;padding:84px 60px;border-radius:44px;background:var(--texto);color:var(--fundo);text-align:center}
.min-cta h2{font-size:80px;letter-spacing:-.05em;max-width:900px;margin:0 auto 16px}
.min-cta p{opacity:.75;font-size:19px;margin-bottom:30px}
"""


def minimal(s: dict, img: dict) -> str:
    h = s["hero"]
    icones = ["raio", "escudo", "coracao"]
    recursos = "".join(
        f'<div class="recurso alvo" data-revela="3d" data-atraso="{i * 0.12:.2f}"><div class="ic">{_ic(icones[i % 3])}</div>'
        f'<h3>{_e(it["nome"])}</h3><p>{_e(it["texto"])}</p><span class="preco">{_e(it.get("preco", ""))}</span></div>'
        for i, it in enumerate(s["itens"][:3]))
    passos = "".join(f'<div class="passo alvo" data-revela="direita" data-atraso="{0.25 + i * 0.12:.2f}"><b>{i + 1}</b>{_e(p)}</div>'
                     for i, p in enumerate(s["sobre"]["pontos"][:3]))
    numeros = "".join(f'<div data-revela="sobe" data-atraso="{i * 0.1:.2f}"><div class="num" data-conta="{_e(n["valor"])}">{_e(n["valor"])}</div>'
                      f'<p>{_e(n["rotulo"])}</p></div>' for i, n in enumerate(s["numeros"][:4]))
    marcas = "".join(f'<span data-revela="sobe" data-atraso="{i * 0.08:.2f}">{_e(p)}</span>' for i, p in enumerate(s["palavras"][:5]))
    titulo = " ".join(_partes_titulo(h["titulo"]))
    return f"""
<section class="min-hero" data-parada="0">
  <span class="selo-pilula" data-revela="zoom"><i></i>{_e(h["selo"])}</span>
  <h1 data-revela="palavras" data-atraso=".1">{_rico(titulo)}</h1>
  <p class="lead" data-revela="sobe" data-atraso=".45">{_e(h["subtitulo"])}</p>
  <div class="acoes" data-revela="sobe" data-atraso=".6"><a class="botao">{_e(s["botao"])} {_ic("seta")}</a>
    <a class="botao vazado">{_e(s.get("botao2") or "Saiba mais")}</a></div>
  <div class="vitrine" data-revela="3d" data-atraso=".5">{_img(img, "hero", alt=s["marca"], extra="data-paralaxe")}
    <div class="cartao-flut alvo" data-flutua="8">{_ic("relogio")}<span><b>{_e(h.get("destaque", ""))}</b>{_e(h.get("destaque_sub", ""))}</span></div></div>
</section>
<div class="marcas">{marcas}</div>
<section class="recursos" data-parada="0">
  <div class="cabeca-c"><p class="eyebrow" data-revela="sobe">{_e(s["secao_itens"]["selo"])}</p>
    <h2 data-revela="palavras" data-atraso=".1">{_rico(s["secao_itens"]["titulo"])}</h2></div>
  <div class="grade">{recursos}</div>
</section>
<section class="alterna" data-parada="0">
  <div class="foto" data-revela="imagem">{_img(img, "sobre0", alt=s["marca"], extra="data-paralaxe")}</div>
  <div><p class="eyebrow" data-revela="sobe">{_e(s["sobre"]["selo"])}</p>
    <h2 data-revela="palavras" data-atraso=".1">{_rico(s["sobre"]["titulo"])}</h2>
    <p data-revela="sobe" data-atraso=".2">{_e(s["sobre"]["texto"])}</p><div class="passos">{passos}</div></div>
</section>
<section class="min-numeros" data-parada="120">{numeros}</section>
<section class="min-cta" data-revela="3d" data-parada="40">
  <h2 data-revela="palavras">{_rico(s["cta"]["titulo"])}</h2><p>{_e(s["cta"].get("texto", ""))}</p>
  <a class="botao">{_e(s["cta"].get("botao") or s["botao"])} {_ic("seta")}</a>
</section>"""


# ==== revista ==================================================================
CSS_REVISTA = """
.nav{background:var(--fundo);border-bottom:2px solid var(--texto)}
.rev-hero{padding:26px 56px 30px}
.rev-faixa-topo{display:flex;justify-content:space-between;font-weight:700;font-size:13px;letter-spacing:.2em;text-transform:uppercase;
  padding-bottom:12px;border-bottom:1px solid var(--texto)}
.rev-hero h1{font-size:150px;line-height:.86;letter-spacing:-.045em;margin:22px 0 22px;font-weight:var(--peso-titulo)}
.rev-hero h1 em{font-style:italic}
.rev-fotos{display:grid;grid-template-columns:1.5fr 1fr 1fr;gap:14px;height:248px}
.rev-fotos>div{overflow:hidden;border-radius:6px;position:relative}
.rev-fotos small{position:absolute;left:12px;bottom:10px;z-index:1;color:#fff;font-size:13px;font-weight:600;text-shadow:0 1px 6px rgba(0,0,0,.6)}
.rev-intro{display:grid;grid-template-columns:.8fr 2fr;gap:56px;padding:64px 56px;border-bottom:1px solid var(--linha)}
.rev-intro .lado{font-size:15px;color:var(--suave);border-top:3px solid var(--destaque);padding-top:16px}
.rev-intro .lado b{display:block;font-family:var(--f-titulo);font-size:40px;color:var(--texto);line-height:1;margin:8px 0}
.rev-intro .texto-grande{font-family:var(--f-titulo);font-size:48px;line-height:1.12;letter-spacing:-.02em}
.rev-intro .texto-grande::first-letter{float:left;font-size:150px;line-height:.78;margin:6px 16px 0 0;color:var(--destaque)}
.rev-colunas{display:grid;grid-template-columns:repeat(3,1fr);padding:56px 56px 40px}
.rev-col{padding:0 30px;border-left:1px solid var(--linha)}
.rev-col:first-child{border-left:0;padding-left:0}
.rev-col .nro{font-size:14px;font-weight:700;letter-spacing:.2em;color:var(--destaque)}
.rev-col h3{font-size:44px;line-height:1;margin:14px 0 14px;letter-spacing:-.02em}
.rev-col .foto{height:200px;border-radius:6px;overflow:hidden;margin-bottom:16px}
.rev-col p{color:var(--suave);font-size:16px}
.rev-col .preco{display:inline-block;margin-top:14px;font-family:var(--f-titulo);font-size:28px;font-style:italic}
.rev-citacao{display:grid;grid-template-columns:1fr 1.15fr;min-height:620px}
.rev-citacao .foto{overflow:hidden}
.rev-citacao .lado{background:var(--destaque);color:var(--sobre-destaque);padding:70px 60px;display:flex;flex-direction:column;justify-content:center}
.rev-citacao blockquote{font-family:var(--f-titulo);font-style:italic;font-size:54px;line-height:1.08;letter-spacing:-.02em}
.rev-citacao cite{font-style:normal;margin-top:26px;opacity:.85;font-size:17px}
.rev-numeros{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid var(--linha);border-top:1px solid var(--linha);margin:0 56px}
.rev-numeros>div{padding:36px 24px;border-left:1px solid var(--linha)}
.rev-numeros>div:first-child{border-left:0}
.rev-numeros .num{font-size:70px;font-style:italic}
.rev-numeros p{color:var(--suave);font-size:15px}
.rev-cta{padding:80px 56px 90px;text-align:center}
.rev-cta h2{font-size:100px;line-height:.95;letter-spacing:-.04em;max-width:1050px;margin:0 auto 30px}
.rev-cta .link-grande{font-family:var(--f-titulo);font-size:34px;font-style:italic;border-bottom:3px solid var(--destaque);padding-bottom:4px}
"""


def revista(s: dict, img: dict) -> str:
    h = s["hero"]
    n = s["numeros"]
    colunas = "".join(
        f'<div class="rev-col alvo" data-revela="sobe" data-atraso="{i * 0.14:.2f}"><span class="nro">Nº {i + 1:02d}</span>'
        f'<h3>{_e(it["nome"])}</h3><div class="foto">{_img(img, f"item{i}", alt=it["nome"], extra="data-paralaxe")}</div>'
        f'<p>{_e(it["texto"])}</p><span class="preco">{_e(it.get("preco", ""))}</span></div>'
        for i, it in enumerate(s["itens"][:3]))
    numeros = "".join(f'<div data-revela="sobe" data-atraso="{i * 0.1:.2f}"><div class="num" data-conta="{_e(x["valor"])}">{_e(x["valor"])}</div>'
                      f'<p>{_e(x["rotulo"])}</p></div>' for i, x in enumerate(n[:4]))
    return f"""
<section class="rev-hero" data-parada="0">
  <div class="rev-faixa-topo" data-revela="sobe"><span>{_e(h["selo"])}</span><span>{_e(s.get("cidade", ""))}</span><span>Edição nº 01</span></div>
  <h1>{_linhas_titulo(h["titulo"])}</h1>
  <div class="rev-fotos">
    <div data-revela="imagem" data-atraso=".2">{_img(img, "hero", alt=s["marca"], extra="data-kenburns")}<small>{_e(s["marca"])}</small></div>
    <div data-revela="imagem" data-atraso=".32">{_img(img, "sobre1", alt=s["marca"], extra="data-paralaxe")}<small>{_e(s["palavras"][0])}</small></div>
    <div data-revela="imagem" data-atraso=".44">{_img(img, "sobre0", alt=s["marca"], extra="data-paralaxe")}<small>{_e(s["palavras"][1])}</small></div>
  </div>
</section>
<section class="rev-intro" data-parada="0">
  <div class="lado alvo" data-revela="esquerda">{_e(s["sobre"]["selo"])}<b data-conta="{_e(n[0]["valor"])}">{_e(n[0]["valor"])}</b>{_e(n[0]["rotulo"])}</div>
  <p class="texto-grande" data-revela="palavras">{_e(h["subtitulo"])} {_e(s["sobre"]["texto"][:110])}</p>
</section>
<section class="rev-colunas" data-parada="0">{colunas}</section>
<section class="rev-citacao" data-parada="0">
  <div class="foto" data-revela="imagem">{_img(img, "item2", alt=s["marca"], extra="data-paralaxe")}</div>
  <div class="lado"><blockquote data-revela="palavras">“{_e(s["depoimento"]["texto"])}”</blockquote>
    <cite data-revela="sobe" data-atraso=".3">{_estrelas()} — {_e(s["depoimento"]["autor"])}</cite></div>
</section>
<section class="rev-numeros" data-parada="160">{numeros}</section>
<section class="rev-cta" data-parada="0">
  <h2 data-revela="palavras">{_rico(s["cta"]["titulo"])}</h2>
  <a class="link-grande alvo" data-revela="sobe" data-atraso=".3">{_e(s["cta"].get("botao") or s["botao"])} →</a>
</section>"""


# ==== neon =====================================================================
CSS_NEON = """
body{background:radial-gradient(1200px 700px at 50% -10%,color-mix(in srgb,var(--destaque) 26%,transparent),transparent 70%),var(--fundo)}
.nav{background:color-mix(in srgb,var(--fundo) 70%,transparent);border-bottom:1px solid rgba(255,255,255,.08)}
.neon-hero{position:relative;text-align:center;padding:66px 64px 0;overflow:hidden}
.orbe{position:absolute;border-radius:50%;filter:blur(90px);opacity:.5;background:var(--destaque);pointer-events:none}
.neon-hero h1{font-size:98px;letter-spacing:-.05em;line-height:.98;max-width:1050px;margin:24px auto 18px;color:#fff;
  text-shadow:0 0 42px color-mix(in srgb,var(--destaque) 50%,transparent)}
.neon-hero h1 em{color:var(--destaque);font-style:normal}
.chip-neon svg{width:18px;height:18px;color:var(--destaque)}
.chip-neon{display:inline-flex;gap:10px;align-items:center;padding:8px 16px;border-radius:999px;border:1px solid color-mix(in srgb,var(--destaque) 60%,transparent);
  background:color-mix(in srgb,var(--destaque) 12%,transparent);font-size:15px;font-weight:600}
.neon-hero .lead{font-size:20px;color:var(--suave);max-width:640px;margin:0 auto}
.neon-hero .acoes{display:flex;justify-content:center;gap:14px;margin-top:28px}
.neon-hero .botao{box-shadow:0 0 40px -6px var(--destaque)}
.neon-hero .botao.vazado{box-shadow:none;border-color:rgba(255,255,255,.25)}
.app{position:relative;margin:44px auto 0;width:960px;height:360px;border-radius:26px 26px 0 0;border:1px solid rgba(255,255,255,.14);border-bottom:0;
  background:rgba(255,255,255,.045);backdrop-filter:blur(12px);display:grid;grid-template-columns:220px 1fr;overflow:hidden;text-align:left}
.app .menu-app{border-right:1px solid rgba(255,255,255,.08);padding:22px}
.app .menu-app i{display:block;height:12px;border-radius:6px;background:rgba(255,255,255,.1);margin:14px 0}
.app .menu-app i.on{background:var(--destaque);width:70%}
.app .corpo-app{padding:22px;display:grid;grid-template-rows:auto 1fr;gap:18px}
.app .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.app .stat{border-radius:16px;background:rgba(255,255,255,.06);padding:16px}
.app .stat b{display:block;font-family:var(--f-titulo);font-size:30px}
.app .stat small{color:var(--suave)}
.app .grafico{display:flex;align-items:flex-end;gap:12px;padding:6px 4px 0;border-radius:16px;background:rgba(255,255,255,.03)}
.app .grafico i{flex:1;border-radius:8px 8px 0 0;background:linear-gradient(180deg,var(--destaque),color-mix(in srgb,var(--destaque) 25%,transparent));transform-origin:50% 100%}
.vidros{padding:76px 64px 50px}
.vidros h2{font-size:66px;letter-spacing:-.045em;text-align:center;max-width:900px;margin:10px auto 38px}
.vidros .grade{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.v{border-radius:26px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.045);overflow:hidden}
.v .foto{height:190px;overflow:hidden}
.v .corpo{padding:22px 24px 26px}
.v h3{font-size:28px;letter-spacing:-.03em}
.v p{color:var(--suave);font-size:16px;margin:8px 0 14px}
.v .preco{font-weight:700;color:var(--destaque)}
.trilha-passos{padding:40px 64px 60px;display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:center}
.trilha-passos .foto{height:500px;border-radius:30px;overflow:hidden;border:1px solid rgba(255,255,255,.12)}
.trilha-passos h2{font-size:62px;letter-spacing:-.045em;margin:12px 0 26px}
.etapa{position:relative;padding:0 0 26px 58px}
.etapa::before{content:"";position:absolute;left:18px;top:40px;bottom:0;width:2px;background:linear-gradient(var(--destaque),transparent)}
.etapa:last-child::before{display:none}
.etapa b{position:absolute;left:0;top:0;width:38px;height:38px;border-radius:50%;display:grid;place-items:center;background:var(--destaque);color:var(--sobre-destaque);
  box-shadow:0 0 24px var(--destaque)}
.etapa span{font-size:21px;font-weight:600}
.neon-numeros{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:0 64px}
.neon-numeros>div{border-radius:22px;border:1px solid rgba(255,255,255,.1);padding:30px 24px;background:rgba(255,255,255,.03)}
.neon-numeros .num{font-size:64px;letter-spacing:-.04em;color:#fff;text-shadow:0 0 30px var(--destaque)}
.neon-numeros p{color:var(--suave)}
.neon-cta{margin:70px 64px 80px;padding:84px 60px;border-radius:40px;text-align:center;position:relative;overflow:hidden;
  border:1px solid color-mix(in srgb,var(--destaque) 55%,transparent);background:radial-gradient(600px 300px at 50% 0%,color-mix(in srgb,var(--destaque) 35%,transparent),transparent)}
.neon-cta h2{font-size:80px;letter-spacing:-.05em;max-width:900px;margin:0 auto 16px}
.neon-cta p{color:var(--suave);font-size:19px;margin-bottom:30px}
.neon-cta .botao{box-shadow:0 0 50px -6px var(--destaque);font-size:19px;padding:20px 36px}
"""


def neon(s: dict, img: dict) -> str:
    h = s["hero"]
    n = s["numeros"]
    barras = "".join(f'<i data-revela="barra" data-atraso="{0.5 + k * 0.06:.2f}" style="height:{v}%"></i>'
                     for k, v in enumerate([38, 52, 44, 68, 57, 80, 66, 92, 74, 97]))
    stats = "".join(f'<div class="stat"><b data-conta="{_e(x["valor"])}">{_e(x["valor"])}</b><small>{_e(x["rotulo"])}</small></div>' for x in n[:3])
    cartoes = "".join(
        f'<div class="v alvo" data-revela="3d" data-atraso="{i * 0.12:.2f}"><div class="foto">{_img(img, f"item{i}", alt=it["nome"], extra="data-paralaxe")}</div>'
        f'<div class="corpo"><h3>{_e(it["nome"])}</h3><p>{_e(it["texto"])}</p><span class="preco">{_e(it.get("preco", ""))}</span></div></div>'
        for i, it in enumerate(s["itens"][:3]))
    etapas = "".join(f'<div class="etapa alvo" data-revela="direita" data-atraso="{0.2 + i * 0.15:.2f}"><b>{i + 1}</b><span>{_e(p)}</span></div>'
                     for i, p in enumerate(s["sobre"]["pontos"][:3]))
    numeros = "".join(f'<div data-revela="3d" data-atraso="{i * 0.1:.2f}"><div class="num" data-conta="{_e(x["valor"])}">{_e(x["valor"])}</div>'
                      f'<p>{_e(x["rotulo"])}</p></div>' for i, x in enumerate(n[:4]))
    titulo = " ".join(_partes_titulo(h["titulo"]))
    return f"""
<section class="neon-hero" data-parada="0">
  <span class="orbe" data-flutua="18" style="width:420px;height:420px;left:-80px;top:40px"></span>
  <span class="orbe" data-flutua="22" style="width:360px;height:360px;right:-60px;top:260px;opacity:.35"></span>
  <span class="chip-neon" data-revela="zoom">{_ic("raio")} {_e(h["selo"])}</span>
  <h1 data-revela="palavras" data-atraso=".1">{_rico(titulo)}</h1>
  <p class="lead" data-revela="sobe" data-atraso=".45">{_e(h["subtitulo"])}</p>
  <div class="acoes" data-revela="sobe" data-atraso=".6"><a class="botao">{_e(s["botao"])} {_ic("seta")}</a>
    <a class="botao vazado">{_e(s.get("botao2") or "Saiba mais")}</a></div>
  <div class="app" data-revela="3d" data-atraso=".55"><div class="menu-app"><i class="on"></i><i></i><i></i><i style="width:60%"></i><i></i><i style="width:45%"></i></div>
    <div class="corpo-app"><div class="stats">{stats}</div><div class="grafico">{barras}</div></div></div>
</section>
<section class="vidros" data-parada="0">
  <p class="eyebrow" style="justify-content:center;display:flex" data-revela="sobe">{_e(s["secao_itens"]["selo"])}</p>
  <h2 data-revela="palavras" data-atraso=".1">{_rico(s["secao_itens"]["titulo"])}</h2>
  <div class="grade">{cartoes}</div>
</section>
<section class="trilha-passos" data-parada="0">
  <div class="foto" data-revela="imagem">{_img(img, "sobre0", alt=s["marca"], extra="data-paralaxe")}</div>
  <div><p class="eyebrow" data-revela="sobe">{_e(s["sobre"]["selo"])}</p><h2 data-revela="palavras" data-atraso=".1">{_rico(s["sobre"]["titulo"])}</h2>{etapas}</div>
</section>
<section class="neon-numeros" data-parada="160">{numeros}</section>
<section class="neon-cta" data-revela="3d" data-parada="30">
  <h2 data-revela="palavras">{_rico(s["cta"]["titulo"])}</h2><p>{_e(s["cta"].get("texto", ""))}</p>
  <a class="botao">{_e(s["cta"].get("botao") or s["botao"])} {_ic("seta")}</a>
</section>"""


MODELOS = {"impacto": (impacto, CSS_IMPACTO), "minimal": (minimal, CSS_MINIMAL),
           "revista": (revista, CSS_REVISTA), "neon": (neon, CSS_NEON)}
