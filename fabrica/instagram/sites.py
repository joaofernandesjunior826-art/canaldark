"""Monta o HTML do site-conceito a partir da ficha que o Gemini escreve (ver conceito.py).

Os modelos são feitos à mão (para o site sempre parecer profissional); a IA escolhe o modelo,
as cores, as fontes e escreve todos os textos. O site tem uma pequena "máquina de animação"
(quadroSite) que a cena do notebook chama a cada quadro, para a gravação sair lisa e igual
toda vez (nada depende do relógio do computador).
"""
import html
import re

FONTES_TITULO = ["Fraunces", "Playfair Display", "DM Serif Display", "Cormorant Garamond", "Instrument Serif",
                 "Bricolage Grotesque", "Syne", "Outfit", "Sora", "Space Grotesk", "Archivo", "Unbounded"]
FONTES_TEXTO = ["Inter", "DM Sans", "Manrope", "Plus Jakarta Sans", "Outfit", "Sora"]
MODELOS = ["editorial", "impacto", "luxo"]

_PESOS = {"Cormorant Garamond": "ital,wght@0,500;0,600;0,700;1,500", "Instrument Serif": "ital@0;1",
          "Fraunces": "ital,opsz,wght@0,9..144,400..800;1,9..144,400..700",
          "Playfair Display": "ital,wght@0,500..900;1,500..700", "DM Serif Display": "ital@0;1",
          "Unbounded": "wght@400..800", "Archivo": "wght@400..900", "Bricolage Grotesque": "opsz,wght@12..96,400..800"}


def _e(texto) -> str:
    return html.escape(str(texto or ""), quote=True)


def _fontes_url(titulo: str, texto: str) -> str:
    familias = []
    for f in dict.fromkeys([titulo, texto]):
        pesos = _PESOS.get(f, "wght@400;500;600;700;800")
        familias.append(f"family={f.replace(' ', '+')}:{pesos}")
    return "https://fonts.googleapis.com/css2?" + "&".join(familias) + "&display=block"


# ---- cores --------------------------------------------------------------------
def _rgb(hexa: str) -> tuple[int, int, int]:
    h = hexa.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _luminancia(hexa: str) -> float:
    def canal(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(hexa)
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(a: str, b: str) -> float:
    la, lb = sorted([_luminancia(a), _luminancia(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _misturar(a: str, b: str, k: float) -> str:
    ra, ga, ba = _rgb(a)
    rb, gb, bb = _rgb(b)
    return "#{:02x}{:02x}{:02x}".format(round(ra + (rb - ra) * k), round(ga + (gb - ga) * k), round(ba + (bb - ba) * k))


def _hex(valor, padrao: str) -> str:
    v = str(valor or "").strip()
    if re.fullmatch(r"#?[0-9a-fA-F]{6}", v):
        return "#" + v.lstrip("#").lower()
    if re.fullmatch(r"#?[0-9a-fA-F]{3}", v):
        v = v.lstrip("#")
        return "#" + "".join(c * 2 for c in v).lower()
    return padrao


def paleta(cores: dict) -> dict:
    """Completa e corrige a paleta (contraste mínimo para tudo ficar legível)."""
    fundo = _hex(cores.get("fundo"), "#f6f1ea")
    escuro = _luminancia(fundo) < 0.2
    texto = _hex(cores.get("texto"), "#f4efe8" if escuro else "#1b1714")
    if contraste(fundo, texto) < 7:
        texto = "#f6f2ec" if escuro else "#16120f"
    destaque = _hex(cores.get("destaque"), "#c8743a")
    if contraste(fundo, destaque) < 2.2:  # destaque que some no fundo: escurece ou clareia
        destaque = _misturar(destaque, "#ffffff" if escuro else "#000000", 0.35)
    sobre_destaque = "#ffffff" if contraste(destaque, "#ffffff") >= contraste(destaque, "#111111") else "#111111"
    superficie = _hex(cores.get("superficie"), _misturar(fundo, texto, 0.06))
    if contraste(superficie, fundo) > 1.6 or contraste(superficie, texto) < 6:
        superficie = _misturar(fundo, texto, 0.06)
    return {"fundo": fundo, "texto": texto, "destaque": destaque, "sobre_destaque": sobre_destaque,
            "superficie": superficie, "suave": _misturar(texto, fundo, 0.38), "linha": _misturar(fundo, texto, 0.14),
            "escuro": escuro}


# ---- pedaços comuns -----------------------------------------------------------
def _img(imagens: dict, chave: str, classe: str = "", alt: str = "", extra: str = "") -> str:
    url = imagens.get(chave)
    if url:
        return f'<img class="{classe}" src="{_e(url)}" alt="{_e(alt)}" {extra}>'
    return f'<div class="sem-foto {classe}"><i></i><span>{_e(alt or "✦")}</span></div>'


def _rico(texto) -> str:
    """Escapa o texto e transforma *palavra* em destaque."""
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", _e(texto)).replace("*", "")


def _linhas_titulo(texto: str, atraso: float = 0.08) -> str:
    partes = [p.strip() for p in str(texto).split("|") if p.strip()] or [str(texto)]
    saida = []
    for i, p in enumerate(partes):
        p = _rico(p)
        saida.append(f'<span class="linha"><span data-revela="linha" data-atraso="{atraso + i * 0.12:.2f}">{p}</span></span>')
    return "".join(saida)


def _estrelas() -> str:
    return '<span class="estrelas">★★★★★</span>'


_ICONES = {
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "seta": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "estrela": '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
    "relogio": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "local": '<path d="M12 21s7-6.2 7-11.5A7 7 0 005 9.5C5 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
}


def _icone(nome: str) -> str:
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{_ICONES[nome]}</svg>')


def _selo_giratorio(texto: str) -> str:
    texto = _e(f" {texto} • " * 2)
    return ('<div class="selo-gira" data-gira="18"><svg viewBox="0 0 200 200"><defs><path id="circ" '
            'd="M100,100 m-78,0 a78,78 0 1,1 156,0 a78,78 0 1,1 -156,0"/></defs>'
            f'<text><textPath href="#circ" startOffset="0">{texto}</textPath></text></svg>'
            f'<span>{_icone("estrela")}</span></div>')


# ---- animação (roda dentro do site, chamada pela cena) -------------------------
JS_ANIMACAO = r"""
<script>
"use strict";
(function () {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const saida = (k) => 1 - Math.pow(1 - clamp(k), 3);
  const suave = (k) => { k = clamp(k); return k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; };
  const molinha = (k) => { k = clamp(k); const c = 1.6; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };
  const R = { revela: [], gira: [], flutua: [], letreiro: [], kb: [], conta: [], trechos: [], paradas: [0], inicio: 1.55 };

  function paradas() {
    const max = document.documentElement.scrollHeight - innerHeight;
    const nav = document.querySelector(".nav");
    const menu = nav && getComputedStyle(nav).position === "sticky" ? nav.offsetHeight : 0;
    const ys = [0, ...[...document.querySelectorAll("[data-parada]")].map((el) =>
      Math.min(Math.max(el.getBoundingClientRect().top + scrollY - menu - (+el.dataset.parada || 0), 0), max))];
    const unicos = [...new Set(ys.map(Math.round))].sort((a, b) => a - b);
    return unicos.filter((y, i) => i === 0 || y - unicos[i - 1] > 140);
  }
  // Rolagem: fica no topo enquanto o começo do site aparece, depois para em cada seção.
  function montarRolagem(ps, ini, fim) {
    const n = Math.max(ps.length - 1, 1), passo = (fim - ini) / n, mov = Math.min(1.3, passo * .45), trechos = [];
    for (let i = 1; i < ps.length; i++) {
      const t0 = ini + (i - 1) * passo + (passo - mov) * .35;
      trechos.push({ t0, t1: t0 + mov, de: ps[i - 1], para: ps[i] });
    }
    return trechos;
  }
  function rolagemEm(t) {
    let y = R.paradas[0] || 0;
    for (const r of R.trechos) {
      if (t >= r.t1) y = r.para;
      else if (t > r.t0) return r.de + (r.para - r.de) * suave((t - r.t0) / (r.t1 - r.t0));
      else break;
    }
    return y;
  }
  window.prepararSite = function (op) {
    op = op || {};
    R.inicio = op.inicio ?? 1.55;
    R.paradas = paradas();
    R.trechos = montarRolagem(R.paradas, op.inicioRolagem ?? 4.6, op.fim ?? 25.4);
    const vh = innerHeight;
    const quando = (topo) => {               // instante em que o elemento entra na tela
      if (topo < vh * 0.9) return R.inicio;
      for (let t = 0; t < 60; t += 1 / 30) if (rolagemEm(t) + vh * 0.86 > topo) return t + 0.05;
      return 99;
    };
    const topo = (el) => el.getBoundingClientRect().top + scrollY;
    for (const el of document.querySelectorAll("[data-revela]"))
      R.revela.push({ el, tipo: el.dataset.revela, t0: quando(topo(el)) + (+el.dataset.atraso || 0),
                      dur: +el.dataset.dur || (el.dataset.revela === "linha" ? 0.8 : 0.9) });
    for (const el of document.querySelectorAll("[data-gira]")) R.gira.push({ el, v: +el.dataset.gira || 20 });
    let fase = 0;
    for (const el of document.querySelectorAll("[data-flutua]")) R.flutua.push({ el, a: +el.dataset.flutua || 10, f: (fase += 2.1) });
    for (const el of document.querySelectorAll("[data-letreiro]")) R.letreiro.push({ el, v: +el.dataset.letreiro || 60, w: el.scrollWidth / 2 });
    for (const el of document.querySelectorAll("[data-kenburns]")) R.kb.push(el);
    for (const el of document.querySelectorAll("[data-conta]")) {
      const m = el.dataset.conta.match(/^([^\d]*)([\d.,]+)(.*)$/);
      if (m) R.conta.push({ el, t0: quando(topo(el)) + 0.2, m });
    }
    return { paradas: R.paradas, altura: document.documentElement.scrollHeight, trechos: R.trechos.length };
  };
  window.quadroSite = function (t) {
    window.scrollTo(0, rolagemEm(t));
    for (const r of R.revela) {
      const k = (t - r.t0) / r.dur, p = saida(k), s = r.el.style;
      if (r.tipo === "linha") s.transform = `translateY(${(1 - p) * 105}%)`;
      else if (r.tipo === "zoom") { s.opacity = clamp(k * 1.6); s.transform = `scale(${0.9 + 0.1 * molinha(k)})`; }
      else if (r.tipo === "imagem") s.clipPath = `inset(${(1 - p) * 100}% 0 0 0 round var(--raio))`;
      else if (r.tipo === "esquerda") { s.opacity = clamp(k * 1.5); s.transform = `translateX(${(1 - p) * -70}px)`; }
      else if (r.tipo === "direita") { s.opacity = clamp(k * 1.5); s.transform = `translateX(${(1 - p) * 70}px)`; }
      else { s.opacity = clamp(k * 1.5); s.transform = `translateY(${(1 - p) * 46}px)`; }
    }
    for (const g of R.gira) g.el.style.transform = `rotate(${t * g.v}deg)`;
    for (const f of R.flutua) f.el.style.transform = `translateY(${Math.sin(t * 1.6 + f.f) * f.a}px)`;
    for (const l of R.letreiro) l.el.style.transform = `translateX(${-((t * l.v) % l.w)}px)`;
    for (const el of R.kb) el.style.transform = `scale(${1.12 - 0.12 * saida(t / 12)})`;
    for (const c of R.conta) {
      const alvo = parseFloat(c.m[2].replace(/\./g, "").replace(",", "."));
      const casas = (c.m[2].split(",")[1] || "").length;
      const v = alvo * saida((t - c.t0) / 1.4);
      c.el.textContent = c.m[1] + v.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas }) + c.m[3];
    }
    return true;
  };
})();
</script>
"""


CSS_BASE = """
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:auto}
body{background:var(--fundo);color:var(--texto);font-family:var(--f-texto),system-ui,sans-serif;font-size:18px;line-height:1.55;
  -webkit-font-smoothing:antialiased;overflow-x:hidden;--raio:28px}
img{display:block;width:100%;height:100%;object-fit:cover}
a{color:inherit;text-decoration:none}
h1,h2,h3,.logo,.num{font-family:var(--f-titulo),serif;font-weight:var(--peso-titulo);letter-spacing:var(--esp-titulo);line-height:.98}
em{font-style:italic;color:var(--destaque)}
.linha{display:block;overflow:hidden;padding-bottom:.06em}
.linha>span{display:inline-block;will-change:transform}
[data-revela]{will-change:transform,opacity}
.eyebrow{display:inline-flex;align-items:center;gap:12px;font-size:15px;font-weight:600;letter-spacing:.22em;text-transform:uppercase;color:var(--suave)}
.eyebrow::before{content:"";width:34px;height:1.5px;background:var(--destaque)}
.botao{display:inline-flex;align-items:center;gap:10px;padding:15px 28px;border-radius:999px;background:var(--destaque);color:var(--sobre-destaque);font-weight:700;font-size:16px;white-space:nowrap}
.botao svg{width:18px;height:18px}
.botao.vazado{background:transparent;color:var(--texto);border:1.5px solid var(--linha)}
.sem-foto{position:relative;overflow:hidden;width:100%;height:100%;color:var(--sobre-destaque);
  background:radial-gradient(60% 50% at 28% 22%,color-mix(in srgb,var(--destaque) 50%,#fff 50%) 0%,transparent 62%),
    radial-gradient(70% 60% at 82% 88%,color-mix(in srgb,var(--destaque) 65%,#000 35%) 0%,transparent 66%),
    linear-gradient(155deg,color-mix(in srgb,var(--destaque) 88%,#fff 12%),color-mix(in srgb,var(--destaque) 62%,#000 38%))}
.sem-foto::before{content:"";position:absolute;width:78%;aspect-ratio:1;border-radius:50%;right:-22%;top:-18%;border:2px solid color-mix(in srgb,var(--sobre-destaque) 35%,transparent)}
.sem-foto::after{content:"";position:absolute;width:52%;aspect-ratio:1;border-radius:50%;left:-14%;bottom:-16%;background:color-mix(in srgb,var(--sobre-destaque) 12%,transparent)}
.sem-foto i{position:absolute;inset:0;opacity:.18;background-image:radial-gradient(color-mix(in srgb,var(--sobre-destaque) 60%,transparent) 1.2px,transparent 1.6px);background-size:18px 18px}
.sem-foto span{position:absolute;left:8%;right:8%;bottom:9%;font-family:var(--f-titulo),serif;font-weight:var(--peso-titulo);font-size:clamp(26px,3.2vw,46px);
  line-height:1;letter-spacing:var(--esp-titulo);z-index:1}
.nav{position:sticky;top:0;z-index:10;display:flex;align-items:center;justify-content:space-between;gap:30px;padding:22px 64px;
  background:color-mix(in srgb,var(--fundo) 82%,transparent);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid color-mix(in srgb,var(--linha) 60%,transparent)}
.logo{display:flex;align-items:center;gap:12px;font-size:28px;letter-spacing:-.01em}
.logo i{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;background:var(--destaque);color:var(--sobre-destaque);font-style:normal;font-size:19px}
.nav nav{display:flex;gap:34px;font-size:15.5px;font-weight:500;color:var(--suave)}
.nav nav a:first-child{color:var(--texto)}
.nav .botao{padding:12px 22px;font-size:15px}
.estrelas{color:#f5b301;letter-spacing:2px}
section{position:relative}
.letreiro{overflow:hidden;background:var(--destaque);color:var(--sobre-destaque);padding:26px 0;white-space:nowrap}
.letreiro div{display:inline-flex;gap:46px;font-family:var(--f-titulo),serif;font-size:46px;font-weight:var(--peso-titulo);letter-spacing:var(--esp-titulo)}
.letreiro b{font-weight:inherit;opacity:.55}
footer{padding:46px 64px;display:flex;justify-content:space-between;align-items:center;color:var(--suave);font-size:15px;border-top:1px solid var(--linha)}
"""


# ---- modelo 1: editorial ------------------------------------------------------
CSS_EDITORIAL = """
.hero{min-height:calc(100vh - 87px);display:grid;grid-template-columns:1.08fr .92fr;gap:56px;align-items:center;padding:30px 64px 50px}
.hero h1{font-size:118px;margin:22px 0 26px}
.hero .lead{font-size:20px;max-width:520px;color:var(--suave)}
.acoes{display:flex;align-items:center;gap:22px;margin-top:34px}
.acoes .link{font-weight:600;display:flex;gap:8px;align-items:center}
.acoes .link svg{width:18px;height:18px}
.prova{display:flex;align-items:center;gap:14px;margin-top:36px;font-size:15px;color:var(--suave)}
.avatares{display:flex}
.avatares span{width:40px;height:40px;border-radius:50%;border:3px solid var(--fundo);margin-left:-10px;background:var(--destaque);display:grid;place-items:center;color:var(--sobre-destaque);font-size:14px;font-weight:700}
.avatares span:nth-child(2){background:color-mix(in srgb,var(--destaque) 60%,var(--texto))}
.avatares span:nth-child(3){background:color-mix(in srgb,var(--destaque) 40%,var(--fundo))}
.avatares span:first-child{margin-left:0}
.hero-visual{position:relative;height:640px}
.arco{position:absolute;inset:0 30px 0 40px;border-radius:300px 300px 34px 34px;overflow:hidden;background:var(--superficie);box-shadow:0 40px 80px -40px rgba(0,0,0,.5)}
.flutuante{position:absolute;left:-6px;bottom:70px;display:flex;align-items:center;gap:14px;padding:16px 22px;border-radius:20px;background:var(--fundo);
  box-shadow:0 24px 50px -20px rgba(0,0,0,.45);font-weight:600;font-size:16px}
.flutuante b{display:block;font-size:22px;font-family:var(--f-titulo),serif;font-weight:var(--peso-titulo)}
.flutuante i{width:46px;height:46px;border-radius:14px;display:grid;place-items:center;background:var(--destaque);color:var(--sobre-destaque)}
.flutuante svg{width:22px;height:22px}
.selo-gira{position:absolute;right:0;top:30px;width:150px;height:150px;border-radius:50%;background:var(--destaque);color:var(--sobre-destaque);display:grid;place-items:center}
.selo-gira svg{position:absolute;inset:0;width:100%;height:100%}
.selo-gira text{font-size:17px;font-weight:700;letter-spacing:4px;text-transform:uppercase;fill:currentColor}
.selo-gira span svg{position:static;width:34px;height:34px}
.servicos{padding:70px 64px 56px}
.cabeca{display:flex;justify-content:space-between;align-items:flex-end;gap:40px;margin-bottom:32px}
.cabeca h2{font-size:70px;max-width:780px;margin-top:14px}
.cabeca p.lado{max-width:360px;color:var(--suave)}
.grade{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:24px}
.card{border-radius:var(--raio);background:var(--superficie);overflow:hidden;display:flex;flex-direction:column}
.card .foto{height:236px;overflow:hidden}
.card .corpo{padding:20px 24px 22px;display:flex;flex-direction:column;gap:6px;flex:1}
.card h3{font-size:29px}
.card p{color:var(--suave);font-size:16px}
.card .preco{margin-top:auto;padding-top:10px;font-weight:700;color:var(--destaque);font-size:19px}
.numeros{padding:56px 64px;display:grid;grid-template-columns:repeat(4,1fr);gap:24px;border-top:1px solid var(--linha);border-bottom:1px solid var(--linha)}
.numeros .num{font-size:74px;color:var(--texto);white-space:nowrap}
.numeros .num em{font-style:normal}
.numeros p{color:var(--suave);font-size:17px;margin-top:6px}
.sobre{padding:64px 64px;display:grid;grid-template-columns:1fr 1fr;gap:70px;align-items:center}
.colagem{position:relative;height:560px}
.colagem .a{position:absolute;left:0;top:0;width:72%;height:82%;border-radius:var(--raio);overflow:hidden}
.colagem .b{position:absolute;right:0;bottom:0;width:50%;height:52%;border-radius:var(--raio);overflow:hidden;border:10px solid var(--fundo)}
.sobre h2{font-size:66px;margin:16px 0 18px}
.sobre p{color:var(--suave);font-size:19px}
.lista{list-style:none;display:grid;gap:14px;margin-top:28px}
.lista li{display:flex;gap:14px;align-items:center;font-weight:600;font-size:18px}
.lista li i{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;background:color-mix(in srgb,var(--destaque) 18%,transparent);color:var(--destaque)}
.lista svg{width:17px;height:17px}
.depoimento{padding:96px 64px;text-align:center;background:var(--superficie)}
.depoimento blockquote{font-family:var(--f-titulo),serif;font-weight:var(--peso-titulo);font-size:58px;line-height:1.12;letter-spacing:var(--esp-titulo);max-width:1050px;margin:26px auto 30px}
.depoimento cite{font-style:normal;color:var(--suave);font-size:18px}
.cta{padding:60px 64px 80px}
.cta-caixa{border-radius:40px;background:var(--destaque);color:var(--sobre-destaque);padding:76px 76px;display:grid;grid-template-columns:1.3fr .7fr;gap:40px;align-items:center;overflow:hidden;position:relative}
.cta-caixa h2{font-size:78px}
.cta-caixa p{opacity:.85;margin-top:18px;font-size:19px}
.cta-caixa .botao{background:var(--sobre-destaque);color:var(--destaque);font-size:19px;padding:20px 34px;justify-self:end}
.cta-caixa::after{content:"";position:absolute;right:-120px;top:-160px;width:460px;height:460px;border-radius:50%;border:70px solid color-mix(in srgb,var(--sobre-destaque) 12%,transparent)}
"""


def _editorial(s: dict, img: dict) -> str:
    itens = s["itens"][:4]
    cards = "".join(
        f'<article class="card" data-revela="sobe" data-atraso="{i * 0.12:.2f}">'
        f'<div class="foto">{_img(img, f"item{i}", alt=it["nome"])}</div>'
        f'<div class="corpo"><h3>{_e(it["nome"])}</h3><p>{_e(it["texto"])}</p>'
        f'<span class="preco">{_e(it.get("preco", ""))}</span></div></article>' for i, it in enumerate(itens))
    numeros = "".join(f'<div data-revela="sobe" data-atraso="{i * 0.1:.2f}"><div class="num" data-conta="{_e(n["valor"])}">{_e(n["valor"])}</div>'
                      f'<p>{_e(n["rotulo"])}</p></div>' for i, n in enumerate(s["numeros"][:4]))
    lista = "".join(f'<li data-revela="esquerda" data-atraso="{0.3 + i * 0.1:.2f}"><i>{_icone("check")}</i>{_e(x)}</li>'
                    for i, x in enumerate(s["sobre"].get("pontos", [])[:3]))
    letreiro = "".join(f"<span>{_e(p)}</span><b>✦</b>" for p in s["palavras"]) * 4
    h = s["hero"]
    return f"""
<section class="hero" data-parada="0">
  <div class="hero-texto">
    <p class="eyebrow" data-revela="sobe" data-atraso="0">{_e(h["selo"])}</p>
    <h1>{_linhas_titulo(h["titulo"])}</h1>
    <p class="lead" data-revela="sobe" data-atraso=".45">{_e(h["subtitulo"])}</p>
    <div class="acoes" data-revela="sobe" data-atraso=".6"><a class="botao">{_e(s["botao"])} {_icone("seta")}</a>
      <a class="link">{_e(s.get("botao2") or "Saiba mais")}</a></div>
    <div class="prova" data-revela="sobe" data-atraso=".75"><span class="avatares"><span>{_e(s["marca"][:1])}</span><span>★</span><span>+</span></span>
      <span>{_estrelas()}<br>{_e(h.get("prova", ""))}</span></div>
  </div>
  <div class="hero-visual" data-revela="zoom" data-atraso=".15">
    <div class="arco">{_img(img, "hero", alt=s["marca"], extra="data-kenburns")}</div>
    <div class="flutuante" data-flutua="9"><i>{_icone("relogio")}</i><span><b>{_e(h.get("destaque", ""))}</b>{_e(h.get("destaque_sub", ""))}</span></div>
    {_selo_giratorio(h.get("selo_giratorio") or s["marca"])}
  </div>
</section>
<div class="letreiro"><div data-letreiro="70">{letreiro}</div></div>
<section class="servicos" data-parada="0" style="--n:{len(itens)}">
  <div class="cabeca"><div><p class="eyebrow" data-revela="sobe">{_e(s["secao_itens"]["selo"])}</p>
    <h2 data-revela="sobe" data-atraso=".1">{_rico(s["secao_itens"]["titulo"])}</h2></div>
    <p class="lado" data-revela="sobe" data-atraso=".2">{_e(s["secao_itens"].get("texto", ""))}</p></div>
  <div class="grade">{cards}</div>
</section>
<section class="numeros" data-parada="180">{numeros}</section>
<section class="sobre" data-parada="0">
  <div class="colagem"><div class="a" data-revela="imagem">{_img(img, "sobre0", alt=s["marca"])}</div>
    <div class="b" data-revela="zoom" data-atraso=".25">{_img(img, "sobre1", alt=s["marca"])}</div></div>
  <div><p class="eyebrow" data-revela="sobe">{_e(s["sobre"]["selo"])}</p>
    <h2 data-revela="sobe" data-atraso=".1">{_rico(s["sobre"]["titulo"])}</h2>
    <p data-revela="sobe" data-atraso=".2">{_e(s["sobre"]["texto"])}</p><ul class="lista">{lista}</ul></div>
</section>
<section class="depoimento" data-parada="0">
  <div data-revela="sobe">{_estrelas()}</div>
  <blockquote data-revela="sobe" data-atraso=".1">“{_e(s["depoimento"]["texto"])}”</blockquote>
  <cite data-revela="sobe" data-atraso=".25">{_e(s["depoimento"]["autor"])}</cite>
</section>
<section class="cta" data-parada="0">
  <div class="cta-caixa" data-revela="zoom"><div><h2>{_rico(s["cta"]["titulo"])}</h2><p>{_e(s["cta"].get("texto", ""))}</p></div>
    <a class="botao">{_e(s["cta"].get("botao") or s["botao"])} {_icone("seta")}</a></div>
</section>"""


# ---- montagem final -----------------------------------------------------------
def montar_site(s: dict, imagens: dict) -> str:
    """Devolve o HTML completo do site. `imagens` = {"hero": "img/hero.jpg", "item0": ..., "sobre0": ...}."""
    p = paleta(s.get("cores", {}))
    f_titulo = s.get("fonte_titulo") if s.get("fonte_titulo") in FONTES_TITULO else "Fraunces"
    f_texto = s.get("fonte_texto") if s.get("fonte_texto") in FONTES_TEXTO else "Inter"
    serifada = f_titulo in FONTES_TITULO[:5]
    corpo = _editorial(s, imagens)
    links = "".join(f"<a>{_e(x)}</a>" for x in s.get("menu", [])[:4])
    inicial = _e(s["marca"][:1].upper())
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=1280">
<title>{_e(s["marca"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{_fontes_url(f_titulo, f_texto)}">
<style>
:root{{--fundo:{p["fundo"]};--texto:{p["texto"]};--destaque:{p["destaque"]};--sobre-destaque:{p["sobre_destaque"]};
  --superficie:{p["superficie"]};--suave:{p["suave"]};--linha:{p["linha"]};
  --f-titulo:"{f_titulo}";--f-texto:"{f_texto}";--peso-titulo:{500 if serifada else 700};--esp-titulo:{"-0.02em" if serifada else "-0.045em"}}}
{CSS_BASE}{CSS_EDITORIAL}
</style></head>
<body>
<header class="nav"><a class="logo"><i>{inicial}</i>{_e(s["marca"])}</a><nav>{links}</nav>
  <a class="botao">{_e(s["botao"])}</a></header>
{corpo}
<footer><span class="logo" style="font-size:22px"><i>{inicial}</i>{_e(s["marca"])}</span>
  <span>{_icone("local")} {_e(s.get("cidade", ""))}</span><span>© {_e(s["marca"])} · site-conceito</span></footer>
{JS_ANIMACAO}
</body></html>"""
