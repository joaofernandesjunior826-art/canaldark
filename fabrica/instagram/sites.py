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
<style>
#cursor-clover{position:fixed;left:0;top:0;width:54px;height:54px;z-index:99999;pointer-events:none;will-change:transform;
  filter:drop-shadow(0 3px 5px rgba(0,0,0,.45))}
#progresso-clover{position:fixed;left:0;top:0;height:5px;width:100%;z-index:9999;transform-origin:0 50%;transform:scaleX(0);
  background:linear-gradient(90deg,var(--destaque),color-mix(in srgb,var(--destaque) 55%,#fff))}
.palavra{display:inline-block;will-change:transform,opacity}
[data-paralaxe]{position:relative;height:118%!important;top:-9%}
.botao{position:relative;overflow:hidden;isolation:isolate}
.botao::after{content:"";position:absolute;top:-20%;bottom:-20%;width:42%;left:0;z-index:-1;pointer-events:none;
  background:linear-gradient(100deg,transparent,rgba(255,255,255,.45),transparent);transform:translateX(var(--brilho,-160%)) skewX(-18deg)}
#clique-clover{position:fixed;left:0;top:0;width:80px;height:80px;margin:-40px 0 0 -40px;border-radius:50%;z-index:99998;pointer-events:none;
  border:3px solid rgba(255,255,255,.9);box-shadow:0 0 0 3px rgba(0,0,0,.25);opacity:0}
</style>
<script>
"use strict";
(function () {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const saida = (k) => 1 - Math.pow(1 - clamp(k), 3);
  const saida4 = (k) => 1 - Math.pow(1 - clamp(k), 4);
  const suave = (k) => { k = clamp(k); return k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; };
  const molinha = (k) => { k = clamp(k); const c = 1.6; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };
  const R = { revela: [], gira: [], flutua: [], letreiro: [], kb: [], conta: [], trechos: [], paradas: [0], inicio: 1.1,
              movs: [], alvos: [], clique: null, cursor: null, anel: null, palavras: [], paralaxe: [], barra: null };

  function alturaMenu() {
    const nav = document.querySelector(".nav");
    return nav && getComputedStyle(nav).position === "sticky" ? nav.offsetHeight : 0;
  }
  function paradas(maximo) {
    const max = document.documentElement.scrollHeight - innerHeight, menu = alturaMenu();
    const ys = [0, ...[...document.querySelectorAll("[data-parada]")].map((el) =>
      Math.min(Math.max(el.getBoundingClientRect().top + scrollY - menu - (+el.dataset.parada || 0), 0), max))];
    const unicos = [...new Set(ys.map(Math.round))].sort((a, b) => a - b).filter((y, i, l) => i === 0 || y - l[i - 1] > 140);
    if (unicos.length <= maximo) return unicos;
    const fica = [unicos[0]];                       // vídeo curto: pula algumas seções do meio
    for (let i = 1; i < maximo - 1; i++) fica.push(unicos[Math.round(i * (unicos.length - 1) / (maximo - 1))]);
    fica.push(unicos[unicos.length - 1]);
    return [...new Set(fica)];
  }
  // Rolagem como a roda do mouse: cada mudança de seção são duas "puxadas" que desaceleram.
  function montarRolagem(ps, ini, fim) {
    const n = Math.max(ps.length - 1, 1), passo = (fim - ini) / n, trechos = [];
    const d1 = Math.min(0.62, passo * 0.24), d2 = Math.min(0.56, passo * 0.22), pausa = 0.1;
    for (let i = 1; i < ps.length; i++) {
      const t0 = ini + (i - 1) * passo, meio = ps[i - 1] + (ps[i] - ps[i - 1]) * 0.64;
      trechos.push({ t0, t1: t0 + d1, de: ps[i - 1], para: meio });
      trechos.push({ t0: t0 + d1 + pausa, t1: t0 + d1 + pausa + d2, de: meio, para: ps[i], fimSecao: true });
    }
    return trechos;
  }
  function rolagemEm(t) {
    let y = R.paradas[0] || 0;
    for (const r of R.trechos) {
      if (t >= r.t1) y = r.para;
      else if (t > r.t0) return r.de + (r.para - r.de) * saida4((t - r.t0) / (r.t1 - r.t0));
      else break;
    }
    return y;
  }
  function rolandoEm(t) { return R.trechos.some((r) => t > r.t0 - 0.05 && t < r.t1 + 0.05); }

  // Cursor do mouse: em cada parada vai até um botão ou cartão e fica "em cima" dele.
  function planejarCursor(ini, fim) {
    const vh = innerHeight, menu = alturaMenu();
    const seletor = ".botao, .card, .linha-preco, .vidro-card, .flutuante, .numeros > div, .numeros-luxo > div, .galeria .g, .lista li, .pontos span";
    const todos = [...document.querySelectorAll(seletor)].map((el) => {
      const r = el.getBoundingClientRect();
      return { el, x: r.left, y: r.top + scrollY, w: r.width, h: r.height, botao: el.classList.contains("botao") };
    }).filter((a) => a.w > 20 && a.h > 16 && a.w < innerWidth * 0.9);
    const segs = [{ ini: R.inicio + 0.75, fim: R.trechos[0] ? R.trechos[0].t0 : fim, y: R.paradas[0] }];
    R.trechos.forEach((r, i) => {
      if (!r.fimSecao) return;
      const prox = R.trechos[i + 1];
      segs.push({ ini: r.t1 + 0.05, fim: prox ? prox.t0 : fim, y: r.para });
    });
    let x = innerWidth * 0.72, y = vh * 0.78, usados = new Set();
    R.movs = [];
    segs.forEach((sg, n) => {
      const visiveis = todos.filter((a) => a.y - sg.y > menu + 10 && a.y + a.h - sg.y < vh - 20 && !usados.has(a.el));
      if (!visiveis.length) return;
      const ultima = n === segs.length - 1;
      visiveis.sort((a, b) => (b.botao - a.botao) * (ultima || n === 0 ? 1 : -0.3) || a.y - b.y || a.x - b.x);
      const dur = sg.fim - sg.ini, qtd = dur > 2.3 && visiveis.length > 1 && !ultima ? 2 : 1;
      for (let k = 0; k < qtd; k++) {
        const a = visiveis[k === 0 ? 0 : Math.min(visiveis.length - 1, 1 + ((n * 3) % (visiveis.length - 1 || 1)))];
        usados.add(a.el);
        const t0 = sg.ini + k * dur / qtd, t1 = t0 + Math.min(0.7, dur / qtd * 0.45);
        const nx = a.x + a.w * (a.botao ? 0.62 : 0.55), ny = a.y - sg.y + a.h * (a.botao ? 0.6 : 0.45);
        R.movs.push({ t0, t1, x0: x, y0: y, x1: nx, y1: ny, el: a.el, fimHover: k + 1 < qtd ? sg.ini + (k + 1) * dur / qtd : sg.fim });
        x = nx; y = ny;
      }
      if (ultima) {
        const m = R.movs[R.movs.length - 1];
        if (m) R.clique = { t: m.t1 + 0.35, x: m.x1, y: m.y1 };
      }
    });
  }
  function cursorEm(t) {
    let pos = R.movs.length ? [R.movs[0].x0, R.movs[0].y0] : [innerWidth * 0.72, innerHeight * 0.78];
    for (const m of R.movs) {
      if (t >= m.t1) pos = [m.x1, m.y1];
      else if (t > m.t0) {
        const k = suave((t - m.t0) / (m.t1 - m.t0)), curva = Math.sin(Math.PI * k) * 0.12;
        const dx = m.x1 - m.x0, dy = m.y1 - m.y0;
        return [m.x0 + dx * k - dy * curva, m.y0 + dy * k + dx * curva];
      } else break;
    }
    return pos;
  }

  window.prepararSite = function (op) {
    op = op || {};
    R.inicio = op.inicio ?? 1.1;
    const ini = op.inicioRolagem ?? 3.0, fim = op.fim ?? 16.4;
    R.paradas = paradas(Math.max(3, Math.round((fim - ini) / 2.6) + 1));
    R.trechos = montarRolagem(R.paradas, ini, fim);
    const vh = innerHeight;
    const quando = (topo) => {               // instante em que o elemento entra na tela
      if (topo < vh * 0.9) return R.inicio;
      for (let t = 0; t < 60; t += 1 / 30) if (rolagemEm(t) + vh * 0.88 > topo) return t + 0.02;
      return 99;
    };
    const topo = (el) => el.getBoundingClientRect().top + scrollY;
    for (const el of document.querySelectorAll('[data-revela]:not([data-revela="palavras"])'))
      R.revela.push({ el, tipo: el.dataset.revela, t0: quando(topo(el)) + (+el.dataset.atraso || 0) * 0.8,
                      dur: +el.dataset.dur || (el.dataset.revela === "linha" ? 0.7 : 0.75) });
    // títulos que aparecem palavra por palavra
    for (const el of document.querySelectorAll('[data-revela="palavras"]')) {
      const andar = (no) => {
        for (const filho of [...no.childNodes]) {
          if (filho.nodeType === 3) {
            const frag = document.createDocumentFragment();
            for (const parte of filho.textContent.split(/(\s+)/)) {
              if (!parte) continue;
              if (/^\s+$/.test(parte)) { frag.append(parte); continue; }
              frag.append(Object.assign(document.createElement("span"), { className: "palavra", textContent: parte }));
            }
            filho.replaceWith(frag);
          } else if (filho.nodeType === 1) andar(filho);
        }
      };
      andar(el);
      const t0 = quando(topo(el)) + (+el.dataset.atraso || 0) * 0.8;
      [...el.querySelectorAll(".palavra")].forEach((w, i) => R.palavras.push({ el: w, t0: t0 + i * 0.07 }));
    }
    for (const el of document.querySelectorAll("[data-paralaxe]")) R.paralaxe.push({ el, pai: el.parentElement });
    R.barra = Object.assign(document.createElement("div"), { id: "progresso-clover" });
    document.body.append(R.barra);
    for (const el of document.querySelectorAll("[data-gira]")) R.gira.push({ el, v: +el.dataset.gira || 20 });
    let fase = 0;
    for (const el of document.querySelectorAll("[data-flutua]")) R.flutua.push({ el, a: +el.dataset.flutua || 10, f: (fase += 2.1) });
    for (const el of document.querySelectorAll("[data-letreiro]")) R.letreiro.push({ el, v: +el.dataset.letreiro || 60, w: el.scrollWidth / 2 });
    for (const el of document.querySelectorAll("[data-kenburns]")) R.kb.push(el);
    for (const el of document.querySelectorAll("[data-conta]")) {
      const m = el.dataset.conta.match(/^([^\d]*)([\d.,]+)(.*)$/);
      if (m) R.conta.push({ el, t0: quando(topo(el)) + 0.15, m });
    }
    if (op.cursor !== false) {
      planejarCursor(ini, fim);
      R.cursor = Object.assign(document.createElement("div"), { id: "cursor-clover" });
      R.cursor.innerHTML = '<svg viewBox="0 0 28 28" width="54" height="54"><path d="M6 3.5v19.2l4.6-4.3 2.9 6.6 3.4-1.5-2.9-6.5h6.3z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
      R.anel = Object.assign(document.createElement("div"), { id: "clique-clover" });
      document.body.append(R.anel, R.cursor);
    }
    return { paradas: R.paradas, altura: document.documentElement.scrollHeight, trechos: R.trechos.length, cursor: R.movs.length };
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
      else if (r.tipo === "3d") { s.opacity = clamp(k * 1.6); s.transform = `perspective(900px) rotateX(${(1 - p) * 16}deg) translateY(${(1 - p) * 70}px) scale(${0.94 + 0.06 * p})`; }
      else { s.opacity = clamp(k * 1.5); s.transform = `translateY(${(1 - p) * 46}px)`; }
    }
    for (const w of R.palavras) {
      const k = (t - w.t0) / 0.6, p = saida(k);
      w.el.style.opacity = clamp(k * 2);
      w.el.style.transform = `translateY(${(1 - p) * 0.55}em) rotate(${(1 - p) * 4}deg)`;
      w.el.style.filter = p < 1 ? `blur(${(1 - p) * 6}px)` : "";
    }
    const y = scrollY, vh = innerHeight, max = Math.max(document.documentElement.scrollHeight - vh, 1);
    for (const px of R.paralaxe) {          // fotos andam mais devagar que a página (profundidade)
      const r = px.pai.getBoundingClientRect();
      const desvio = (r.top + r.height / 2 - vh / 2) / vh;
      px.el.style.translate = `0 ${clamp(desvio, -1.2, 1.2) * r.height * -0.075}px`;
    }
    if (R.barra) R.barra.style.transform = `scaleX(${y / max})`;
    document.documentElement.style.setProperty("--brilho", `${-160 + ((t * 140) % 420)}%`);
    for (const g of R.gira) g.el.style.transform = `rotate(${t * g.v}deg)`;
    for (const f of R.flutua) f.el.style.transform = `translateY(${Math.sin(t * 1.6 + f.f) * f.a}px)`;
    for (const l of R.letreiro) l.el.style.transform = `translateX(${-((t * l.v) % l.w)}px)`;
    for (const el of R.kb) el.style.transform = `scale(${1.12 - 0.12 * saida(t / 9)})`;
    for (const c of R.conta) {
      const alvo = parseFloat(c.m[2].replace(/\./g, "").replace(",", "."));
      const casas = (c.m[2].split(",")[1] || "").length;
      const v = alvo * saida((t - c.t0) / 1.2);
      c.el.textContent = c.m[1] + v.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas }) + c.m[3];
    }
    if (R.cursor) {
      const [x, y] = cursorEm(t);
      const aparece = clamp((t - R.inicio - 0.2) / 0.3);
      let aperta = 1;
      if (R.clique) {
        const dc = t - R.clique.t;
        if (dc > 0 && dc < 0.22) aperta = 0.84;
        const ka = clamp(dc / 0.55);
        R.anel.style.opacity = dc > 0 ? (1 - ka) * 0.9 : 0;
        R.anel.style.transform = `translate(${R.clique.x}px, ${R.clique.y}px) scale(${0.2 + ka * 0.9})`;
      }
      R.cursor.style.opacity = aparece;
      R.cursor.style.transform = `translate(${x - 12}px, ${y - 7}px) scale(${aperta})`;
      for (const m of R.movs) {             // "hover": o botão ou cartão sobe e brilha com o cursor em cima
        const h = rolandoEm(t) && t > m.t1 ? 0 : clamp((t - m.t1 + 0.12) / 0.2) * (1 - clamp((t - m.fimHover + 0.05) / 0.2));
        m.el.style.translate = h ? `0 ${-5 * h}px` : "";
        m.el.style.scale = h ? `${1 + 0.035 * h}` : "";
        m.el.style.filter = h ? `brightness(${1 + 0.1 * h})` : "";
        if (m.el.classList.contains("botao")) m.el.style.boxShadow = h ? `0 ${12 * h}px ${28 * h}px -10px color-mix(in srgb, var(--destaque) 80%, transparent)` : "";
      }
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
        f'<article class="card" data-revela="3d" data-atraso="{i * 0.14:.2f}">'
        f'<div class="foto">{_img(img, f"item{i}", alt=it["nome"], extra="data-paralaxe")}</div>'
        f'<div class="corpo"><h3>{_e(it["nome"])}</h3><p>{_e(it["texto"])}</p>'
        f'<span class="preco">{_e(it.get("preco", ""))}</span></div></article>' for i, it in enumerate(itens))
    numeros = "".join(f'<div data-revela="3d" data-atraso="{i * 0.1:.2f}"><div class="num" data-conta="{_e(n["valor"])}">{_e(n["valor"])}</div>'
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
    <h2 data-revela="palavras" data-atraso=".1">{_rico(s["secao_itens"]["titulo"])}</h2></div>
    <p class="lado" data-revela="sobe" data-atraso=".2">{_e(s["secao_itens"].get("texto", ""))}</p></div>
  <div class="grade">{cards}</div>
</section>
<section class="numeros" data-parada="180">{numeros}</section>
<section class="sobre" data-parada="0">
  <div class="colagem"><div class="a" data-revela="imagem">{_img(img, "sobre0", alt=s["marca"], extra="data-paralaxe")}</div>
    <div class="b" data-revela="zoom" data-atraso=".25">{_img(img, "sobre1", alt=s["marca"])}</div></div>
  <div><p class="eyebrow" data-revela="sobe">{_e(s["sobre"]["selo"])}</p>
    <h2 data-revela="palavras" data-atraso=".1">{_rico(s["sobre"]["titulo"])}</h2>
    <p data-revela="sobe" data-atraso=".2">{_e(s["sobre"]["texto"])}</p><ul class="lista">{lista}</ul></div>
</section>
<section class="depoimento" data-parada="0">
  <div data-revela="sobe">{_estrelas()}</div>
  <blockquote data-revela="palavras" data-atraso=".1">“{_e(s["depoimento"]["texto"])}”</blockquote>
  <cite data-revela="sobe" data-atraso=".25">{_e(s["depoimento"]["autor"])}</cite>
</section>
<section class="cta" data-parada="0">
  <div class="cta-caixa" data-revela="zoom"><div><h2>{_rico(s["cta"]["titulo"])}</h2><p>{_e(s["cta"].get("texto", ""))}</p></div>
    <a class="botao">{_e(s["cta"].get("botao") or s["botao"])} {_icone("seta")}</a></div>
</section>"""


# ---- modelo 2: luxo (escuro, foto de ponta a ponta) --------------------------
CSS_LUXO = """
.nav{background:color-mix(in srgb,var(--fundo) 70%,transparent)}
.hero-luxo{position:relative;height:calc(100vh - 87px);overflow:hidden;display:flex;align-items:flex-end;padding:0 64px 70px}
.hero-luxo .fundo-foto{position:absolute;inset:0}
.hero-luxo .fundo-foto img,.hero-luxo .fundo-foto .sem-foto{transform-origin:60% 40%}
.hero-luxo::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.18) 0%,rgba(0,0,0,.1) 35%,color-mix(in srgb,var(--fundo) 88%,transparent) 100%)}
.hero-luxo .conteudo{position:relative;z-index:1;max-width:820px}
.hero-luxo h1{font-size:122px;margin:20px 0 22px;color:#fff}
.hero-luxo .eyebrow{color:rgba(255,255,255,.82)}
.hero-luxo .lead{font-size:20px;color:rgba(255,255,255,.82);max-width:560px}
.hero-luxo .acoes{display:flex;gap:18px;margin-top:30px}
.hero-luxo .botao.vazado{color:#fff;border-color:rgba(255,255,255,.45)}
.vidro-card{position:absolute;right:64px;bottom:70px;z-index:1;width:300px;padding:22px 24px;border-radius:24px;color:#fff;
  background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.25);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}
.vidro-card b{display:block;font-family:var(--f-titulo),serif;font-weight:var(--peso-titulo);font-size:46px;line-height:1}
.vidro-card small{display:block;margin-top:8px;color:rgba(255,255,255,.8);font-size:15px}
.intro{padding:90px 64px;text-align:center}
.intro h2{font-size:76px;max-width:1000px;margin:18px auto 22px}
.intro p{color:var(--suave);font-size:20px;max-width:720px;margin:0 auto}
.intro .pontos{display:flex;justify-content:center;gap:34px;margin-top:34px;font-weight:600}
.intro .pontos span{display:flex;align-items:center;gap:10px}
.intro .pontos svg{width:20px;height:20px;color:var(--destaque)}
.menu-precos{padding:60px 64px 40px}
.menu-precos h2{font-size:70px;margin:12px 0 30px}
.linha-preco{display:grid;grid-template-columns:200px 1fr auto;gap:30px;align-items:center;padding:18px 0;border-top:1px solid var(--linha)}
.linha-preco .foto{height:130px;border-radius:18px;overflow:hidden}
.linha-preco h3{font-size:38px}
.linha-preco p{color:var(--suave);font-size:17px;margin-top:6px}
.linha-preco .preco{font-family:var(--f-titulo),serif;font-weight:var(--peso-titulo);font-size:36px;color:var(--destaque);white-space:nowrap}
.numeros-luxo{display:grid;grid-template-columns:repeat(4,1fr);margin:30px 64px;border:1px solid var(--linha);border-radius:28px;overflow:hidden}
.numeros-luxo>div{padding:40px 30px;border-left:1px solid var(--linha)}
.numeros-luxo>div:first-child{border-left:0}
.numeros-luxo .num{font-size:66px;white-space:nowrap}
.numeros-luxo p{color:var(--suave);margin-top:8px}
.galeria{display:grid;grid-template-columns:1fr 1.25fr;gap:24px;padding:40px 64px 70px;height:640px}
.galeria .g{border-radius:28px;overflow:hidden;position:relative}
.hero-luxo .sem-foto span,.cta-luxo .sem-foto span,.galeria .sem-foto span{display:none}
.galeria .g .rotulo{position:absolute;left:24px;bottom:22px;z-index:1;color:#fff;font-weight:600;font-size:17px;padding:8px 14px;border-radius:999px;
  background:rgba(0,0,0,.35);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
.depo-luxo{padding:100px 64px;text-align:center}
.depo-luxo .aspas{font-family:var(--f-titulo),serif;font-size:160px;line-height:.6;color:var(--destaque);height:70px}
.depo-luxo blockquote{font-family:var(--f-titulo),serif;font-weight:var(--peso-titulo);font-size:56px;line-height:1.12;letter-spacing:var(--esp-titulo);max-width:1040px;margin:10px auto 28px}
.depo-luxo cite{font-style:normal;color:var(--suave)}
.cta-luxo{position:relative;margin:20px 64px 80px;border-radius:40px;overflow:hidden;height:520px;display:grid;place-items:center;text-align:center}
.cta-luxo .fundo-foto{position:absolute;inset:0}
.cta-luxo::after{content:"";position:absolute;inset:0;background:rgba(0,0,0,.55)}
.cta-luxo .conteudo{position:relative;z-index:1;color:#fff;padding:0 60px}
.cta-luxo h2{font-size:86px;max-width:900px;margin:0 auto 18px}
.cta-luxo p{font-size:20px;opacity:.85;margin-bottom:30px}
"""


def _luxo(s: dict, img: dict) -> str:
    h = s["hero"]
    linhas = "".join(
        f'<div class="linha-preco" data-revela="esquerda" data-atraso="{i * 0.14:.2f}"><div class="foto">{_img(img, f"item{i}", alt=it["nome"], extra="data-paralaxe")}</div>'
        f'<div><h3>{_e(it["nome"])}</h3><p>{_e(it["texto"])}</p></div><span class="preco">{_e(it.get("preco", ""))}</span></div>'
        for i, it in enumerate(s["itens"][:3]))
    numeros = "".join(f'<div data-revela="3d" data-atraso="{i * 0.1:.2f}"><div class="num" data-conta="{_e(n["valor"])}">{_e(n["valor"])}</div>'
                      f'<p>{_e(n["rotulo"])}</p></div>' for i, n in enumerate(s["numeros"][:4]))
    pontos = "".join(f'<span data-revela="sobe" data-atraso="{0.3 + i * 0.1:.2f}">{_icone("check")}{_e(x)}</span>'
                     for i, x in enumerate(s["sobre"].get("pontos", [])[:3]))
    letreiro = "".join(f"<span>{_e(p)}</span><b>✦</b>" for p in s["palavras"]) * 4
    return f"""
<section class="hero-luxo" data-parada="0">
  <div class="fundo-foto">{_img(img, "hero", alt=s["marca"], extra="data-kenburns")}</div>
  <div class="conteudo">
    <p class="eyebrow" data-revela="sobe">{_e(h["selo"])}</p>
    <h1>{_linhas_titulo(h["titulo"])}</h1>
    <p class="lead" data-revela="sobe" data-atraso=".45">{_e(h["subtitulo"])}</p>
    <div class="acoes" data-revela="sobe" data-atraso=".6"><a class="botao">{_e(s["botao"])} {_icone("seta")}</a>
      <a class="botao vazado">{_e(s.get("botao2") or "Saiba mais")}</a></div>
  </div>
  <div class="vidro-card" data-revela="direita" data-atraso=".8"><b>{_e(h.get("destaque", ""))}</b>
    <small>{_e(h.get("destaque_sub", ""))}</small><small>{_estrelas()} {_e(h.get("prova", ""))}</small></div>
</section>
<div class="letreiro"><div data-letreiro="70">{letreiro}</div></div>
<section class="intro" data-parada="0">
  <p class="eyebrow" data-revela="sobe">{_e(s["sobre"]["selo"])}</p>
  <h2 data-revela="palavras" data-atraso=".1">{_rico(s["sobre"]["titulo"])}</h2>
  <p data-revela="sobe" data-atraso=".2">{_e(s["sobre"]["texto"])}</p>
  <div class="pontos">{pontos}</div>
</section>
<section class="menu-precos" data-parada="0">
  <p class="eyebrow" data-revela="sobe">{_e(s["secao_itens"]["selo"])}</p>
  <h2 data-revela="palavras" data-atraso=".1">{_rico(s["secao_itens"]["titulo"])}</h2>
  {linhas}
</section>
<section class="numeros-luxo" data-parada="200">{numeros}</section>
<section class="galeria" data-parada="0">
  <div class="g" data-revela="imagem">{_img(img, "sobre0", alt=s["marca"], extra="data-paralaxe")}<span class="rotulo">{_e(s["palavras"][0] if s["palavras"] else s["marca"])}</span></div>
  <div class="g" data-revela="imagem" data-atraso=".15">{_img(img, "sobre1", alt=s["marca"], extra="data-paralaxe")}<span class="rotulo">{_e(s.get("cidade", ""))}</span></div>
</section>
<section class="depo-luxo" data-parada="0">
  <div class="aspas" data-revela="zoom">“</div>
  <blockquote data-revela="palavras" data-atraso=".1">{_e(s["depoimento"]["texto"])}</blockquote>
  <cite data-revela="sobe" data-atraso=".25">{_estrelas()} · {_e(s["depoimento"]["autor"])}</cite>
</section>
<section class="cta-luxo" data-parada="60">
  <div class="fundo-foto">{_img(img, "hero", alt=s["marca"], extra="data-paralaxe")}</div>
  <div class="conteudo"><h2 data-revela="palavras">{_rico(s["cta"]["titulo"])}</h2><p data-revela="sobe" data-atraso=".1">{_e(s["cta"].get("texto", ""))}</p>
    <a class="botao" data-revela="zoom" data-atraso=".2">{_e(s["cta"].get("botao") or s["botao"])} {_icone("seta")}</a></div>
</section>"""


# ---- montagem final -----------------------------------------------------------
def montar_site(s: dict, imagens: dict) -> str:
    """Devolve o HTML completo do site. `imagens` = {"hero": "img/hero.jpg", "item0": ..., "sobre0": ...}."""
    modelo = s.get("modelo") if s.get("modelo") in ("editorial", "luxo") else "editorial"
    cores = dict(s.get("cores") or {})
    if modelo == "luxo" and _luminancia(_hex(cores.get("fundo"), "#f6f1ea")) >= 0.2:
        cores.update(fundo="#0e0d0c", texto="#f4efe7", superficie="#1a1816")  # o luxo é sempre escuro
    p = paleta(cores)
    f_titulo = s.get("fonte_titulo") if s.get("fonte_titulo") in FONTES_TITULO else "Fraunces"
    f_texto = s.get("fonte_texto") if s.get("fonte_texto") in FONTES_TEXTO else "Inter"
    serifada = f_titulo in FONTES_TITULO[:5]
    corpo = (_luxo if modelo == "luxo" else _editorial)(s, imagens)
    css_modelo = CSS_LUXO if modelo == "luxo" else CSS_EDITORIAL
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
{CSS_BASE}{css_modelo}
</style></head>
<body>
<header class="nav"><a class="logo"><i>{inicial}</i>{_e(s["marca"])}</a><nav>{links}</nav>
  <a class="botao">{_e(s["botao"])}</a></header>
{corpo}
<footer><span class="logo" style="font-size:22px"><i>{inicial}</i>{_e(s["marca"])}</span>
  <span>{_icone("local")} {_e(s.get("cidade", ""))}</span><span>© {_e(s["marca"])} · site-conceito</span></footer>
{JS_ANIMACAO}
</body></html>"""
