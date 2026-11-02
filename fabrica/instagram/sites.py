"""Monta o HTML do site-conceito a partir da ficha que o Gemini escreve (ver conceito.py).

Os modelos são feitos à mão (para o site sempre parecer profissional); a IA escolhe o modelo,
as cores, as fontes e escreve todos os textos. O site tem uma pequena "máquina de animação"
(quadroSite) que a cena do notebook chama a cada quadro, para a gravação sair lisa e igual
toda vez (nada depende do relógio do computador).
"""
import html
import json
import re
import unicodedata

FONTES_TITULO = ["Fraunces", "Playfair Display", "DM Serif Display", "Cormorant Garamond", "Instrument Serif",
                 "Bricolage Grotesque", "Syne", "Outfit", "Sora", "Space Grotesk", "Archivo", "Unbounded"]
FONTES_TEXTO = ["Inter", "DM Sans", "Manrope", "Plus Jakarta Sans", "Outfit", "Sora"]
MODELOS = ["editorial", "luxo", "impacto", "minimal", "revista", "neon"]
# Fontes de título que combinam com cada modelo (a do Gemini vale se estiver aqui; senão, sorteia uma)
FAMILIAS = {
    "editorial": ["Fraunces", "Playfair Display", "DM Serif Display", "Instrument Serif", "Bricolage Grotesque"],
    "luxo": ["Cormorant Garamond", "Playfair Display", "Instrument Serif", "DM Serif Display"],
    "impacto": ["Unbounded", "Syne", "Archivo", "Bricolage Grotesque", "Space Grotesk"],
    "minimal": ["Inter", "Manrope", "Plus Jakarta Sans", "Outfit", "Sora"],
    "revista": ["Playfair Display", "Fraunces", "DM Serif Display", "Instrument Serif", "Cormorant Garamond"],
    "neon": ["Sora", "Space Grotesk", "Outfit", "Syne", "Unbounded"],
}
SERIFADAS = {"Fraunces", "Playfair Display", "DM Serif Display", "Cormorant Garamond", "Instrument Serif"}

_PESOS = {"Inter": "wght@400;500;600;700;800", "Syne": "wght@500;600;700;800", "Space Grotesk": "wght@400;500;600;700",
          "Cormorant Garamond": "ital,wght@0,500;0,600;0,700;1,500", "Instrument Serif": "ital@0;1",
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
              movs: [], alvos: [], cliques: [], cursor: null, anel: null, palavras: [], paralaxe: [], barra: null,
              B: null, abre: [], sub: [], noite: [], ativos: [], dicas: [], hovers: [], texto: [], digita: null, cursor0: null,
              ultimoAtivo: -1, ultimaNoite: -1, ultimaDica: null };

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
      trechos.push({ t0, t1: t0 + d1, de: ps[i - 1], para: meio, curva: "roda" });
      trechos.push({ t0: t0 + d1 + pausa, t1: t0 + d1 + pausa + d2, de: meio, para: ps[i], fimSecao: true, curva: "roda" });
    }
    return trechos;
  }
  function rolagemEm(t) {
    let y = R.paradas[0] || 0;
    for (const r of R.trechos) {
      if (t >= r.t1) y = r.para;
      else if (t > r.t0) return r.de + (r.para - r.de) * (r.curva === "suave" ? suave : saida4)((t - r.t0) / (r.t1 - r.t0));
      else break;
    }
    return y;
  }
  function valorEm(lista, t, v0) {          // linha do tempo de um valor (0 a 1) com transições suaves
    let v = v0;
    for (const s of lista) {
      if (t >= s.t1) v = s.para;
      else if (t > s.t0) return s.de + (s.para - s.de) * suave((t - s.t0) / (s.t1 - s.t0));
      else break;
    }
    return v;
  }
  function janela(lista, t, sobe = 0.12, desce = 0.15) {  // intensidade (0 a 1) dentro de janelas de tempo
    let h = 0;
    for (const j of lista) h = Math.max(h, clamp((t - j.t0) / sobe) * (1 - clamp((t - j.t1) / desce)));
    return h;
  }
  function alvosDaPagina() {
    const seletor = ".alvo, .botao, .card, .linha-preco, .vidro-card, .flutuante, .numeros > div, .numeros-luxo > div, .galeria .g, .lista li, .pontos span";
    return [...document.querySelectorAll(seletor)].filter((el) => !el.closest(".nav, .barra-v")).map((el) => {
      const r = el.getBoundingClientRect();
      return { el, x: r.left, y: r.top + scrollY, w: r.width, h: r.height, botao: el.classList.contains("botao") };
    }).filter((a) => a.w > 20 && a.h > 16 && a.w < innerWidth * 0.9);
  }
  function rolandoEm(t) { return R.trechos.some((r) => t > r.t0 - 0.05 && t < r.t1 + 0.05); }

  // Cursor do mouse: em cada parada vai até um botão ou cartão e fica "em cima" dele.
  function planejarCursor(ini, fim) {
    const vh = innerHeight, menu = alturaMenu();
    const seletor = ".alvo, .botao, .card, .linha-preco, .vidro-card, .flutuante, .numeros > div, .numeros-luxo > div, .galeria .g, .lista li, .pontos span";
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
        if (m) R.cliques.push({ t: m.t1 + 0.35, x: m.x1, y: m.y1 });
      }
    });
  }
  // ---- barra lateral de vidro: o cursor usa ela de verdade ----
  function medirBarra(b) {
    const B = { el: b, itens: [...b.querySelectorAll(".bv-item")], subs: [...b.querySelectorAll(".bv-sub a")],
                seta: b.querySelector(".bv-seta"), busca: b.querySelector(".bv-busca"), noite: b.querySelector(".bv-noite"),
                digitado: b.querySelector(".digitado"), ph: b.querySelector(".ph"), caret: b.querySelector(".caret"),
                dica: document.querySelector(".bv-dica") };
    const centro = (el, fx = 0.5) => { const r = el.getBoundingClientRect(); return [r.left + r.width * fx, r.top + r.height / 2]; };
    const icone = (el) => centro(el.querySelector("svg") || el);
    b.style.setProperty("--abre", 0); b.style.setProperty("--sub", 0);
    B.fechada = { itens: B.itens.map(icone), seta: centro(B.seta), noite: icone(B.noite), direita: b.getBoundingClientRect().right };
    b.style.setProperty("--abre", 1); b.style.setProperty("--sub", 1);
    B.aberta = { itens: B.itens.map((el) => centro(el, 0.35)), subs: B.subs.map((el) => centro(el, 0.4)), seta: centro(B.seta),
                 busca: centro(B.busca, 0.42) };
    b.style.setProperty("--abre", 0); b.style.setProperty("--sub", 0);
    return B;
  }
  function planejarComBarra(ini, fim) {
    const B = R.B, P = R.paradas, N = P.length - 1, vh = innerHeight, menu = alturaMenu();
    const temTema = !!(window.TEMAS && window.TEMAS.para);
    const passos = [{ tipo: "heroi", y: P[0] }];
    for (let k = 1; k <= N; k++) {
      passos.push({ tipo: k % 2 ? "clique" : "roda", de: P[k - 1], para: P[k], k });
      passos.push({ tipo: k === N ? "final" : k === 1 ? "expandir" : (k === 2 && temTema) ? "tema" : "hover", y: P[k] });
    }
    const base = { heroi: 1.2, clique: 1.6, roda: 1.1, hover: 0.95, expandir: 2.9, tema: 1.3, final: 1.1 };
    const t0 = R.inicio + 0.25, soma = passos.reduce((a, p) => a + base[p.tipo], 0);
    const f = Math.min(1.25, (fim - t0) / soma);
    let t = t0, x = innerWidth * 0.66, y = vh * 0.8, ativo = 0;
    R.cursor0 = [x, y];
    const usados = new Set(), todos = alvosDaPagina();
    const mover = (a, b, nx, ny, el = null, fimHover = null) => { R.movs.push({ t0: a, t1: b, x0: x, y0: y, x1: nx, y1: ny, el, fimHover: fimHover ?? b }); x = nx; y = ny; };
    const clicar = (tc) => R.cliques.push({ t: tc, x, y });
    const alvoPagina = (yRol, botao) => {
      const vis = todos.filter((a) => a.y - yRol > menu + 10 && a.y + a.h - yRol < vh - 20 && !usados.has(a.el));
      if (!vis.length) return null;
      vis.sort((a, b) => (b.botao - a.botao) * (botao ? 1 : -1) || a.y - b.y || a.x - b.x);
      const a = vis[0]; usados.add(a.el);
      return { x: a.x + a.w * (a.botao ? 0.62 : 0.55), y: a.y - yRol + a.h * (a.botao ? 0.6 : 0.45), el: a.el };
    };
    for (const p of passos) {
      const d = base[p.tipo] * f, em = (k) => t + k * d;
      if (p.tipo === "heroi" || p.tipo === "hover" || p.tipo === "final") {
        const a = alvoPagina(p.y, p.tipo !== "hover");
        if (a) { mover(em(0.05), em(0.48), a.x, a.y, a.el, em(1)); if (p.tipo === "final") clicar(em(0.72)); }
      } else if (p.tipo === "clique") {             // clica no ícone da barra e a página rola até a seção
        const idx = Math.min(p.k, B.itens.length - 1);
        mover(em(0), em(0.3), ...B.fechada.itens[idx]);
        R.hovers.push({ el: B.itens[idx], t0: em(0.28), t1: em(0.6) });
        R.dicas.push({ alvo: B.itens[idx], t0: em(0.28), t1: em(0.6) });
        clicar(em(0.48)); R.ativos.push({ t: em(0.48), idx }); ativo = idx;
        R.trechos.push({ t0: em(0.5), t1: em(1), de: p.de, para: p.para, curva: "suave" });
      } else if (p.tipo === "roda") {               // volta para a página e rola com a roda do mouse
        mover(em(0), em(0.25), innerWidth * 0.6, vh * 0.58);
        const meio = p.de + (p.para - p.de) * 0.64;
        R.trechos.push({ t0: em(0.22), t1: em(0.6), de: p.de, para: meio, curva: "roda" });
        R.trechos.push({ t0: em(0.64), t1: em(1), de: meio, para: p.para, curva: "roda", fimSecao: true });
      } else if (p.tipo === "expandir") {           // abre a barra, busca, abre um submenu e fecha
        mover(em(0), em(0.1), ...B.fechada.seta);
        R.hovers.push({ el: B.seta, t0: em(0.08), t1: em(0.14) });
        clicar(em(0.12));
        R.abre.push({ t0: em(0.12), t1: em(0.22), de: 0, para: 1 });
        mover(em(0.23), em(0.32), ...B.aberta.busca);
        R.texto.push({ t0: em(0.29), t1: em(0.52) });
        clicar(em(0.33));
        R.digita = { t0: em(0.35), t1: em(0.5), ate: em(0.9) };
        mover(em(0.53), em(0.61), ...B.aberta.itens[1]);
        R.hovers.push({ el: B.itens[1], t0: em(0.6), t1: em(0.67) });
        clicar(em(0.63)); R.ativos.push({ t: em(0.63), idx: 1 });
        R.sub.push({ t0: em(0.63), t1: em(0.72), de: 0, para: 1 });
        if (B.aberta.subs.length) {
          mover(em(0.67), em(0.75), ...B.aberta.subs[0]);
          R.hovers.push({ el: B.subs[0], t0: em(0.74), t1: em(0.82) });
        }
        mover(em(0.82), em(0.9), ...B.aberta.seta);
        R.hovers.push({ el: B.seta, t0: em(0.88), t1: em(0.93) });
        clicar(em(0.91));
        R.abre.push({ t0: em(0.91), t1: em(1), de: 1, para: 0 });
        R.sub.push({ t0: em(0.91), t1: em(0.97), de: 1, para: 0 });
        R.ativos.push({ t: em(0.95), idx: ativo });
      } else if (p.tipo === "tema") {               // liga o modo noturno: o site inteiro escurece
        mover(em(0), em(0.3), ...B.fechada.noite);
        R.hovers.push({ el: B.noite, t0: em(0.28), t1: em(0.62) });
        R.dicas.push({ alvo: B.noite, t0: em(0.28), t1: em(0.62) });
        clicar(em(0.5));
        R.noite.push({ t0: em(0.5), t1: em(0.8), de: 0, para: 1 });
        mover(em(0.7), em(1), innerWidth * 0.6, vh * 0.55);
      }
      t += d;
    }
    R.trechos.sort((a, b) => a.t0 - b.t0);
  }
  const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const misturaCor = (a, b, k) => "#" + hex(a).map((v, i) => Math.round(v + (hex(b)[i] - v) * k).toString(16).padStart(2, "0")).join("");
  function aplicarTema(k) {
    const T = window.TEMAS;
    if (!T || !T.para || Math.abs(k - R.ultimaNoite) < 0.002) return;
    R.ultimaNoite = k;
    for (const nome of Object.keys(T.de)) document.documentElement.style.setProperty(`--${nome}`, misturaCor(T.de[nome], T.para[nome], k));
  }
  function quadroBarra(t) {
    const B = R.B;
    B.el.style.setProperty("--abre", valorEm(R.abre, t, 0).toFixed(4));
    B.el.style.setProperty("--sub", valorEm(R.sub, t, 0).toFixed(4));
    const noite = valorEm(R.noite, t, 0);
    B.el.style.setProperty("--noite", noite.toFixed(4));
    aplicarTema(noite);
    let idx = 0;
    for (const a of R.ativos) if (t >= a.t) idx = a.idx;
    if (idx !== R.ultimoAtivo) { B.itens.forEach((el, i) => el.classList.toggle("ativo", i === idx)); R.ultimoAtivo = idx; }
    const alvosHover = new Set(R.hovers.map((h) => h.el));
    for (const el of alvosHover) el.style.setProperty("--h", janela(R.hovers.filter((h) => h.el === el), t, 0.1, 0.12).toFixed(3));
    let dica = null, forca = 0;
    for (const d of R.dicas) { const k = janela([d], t, 0.12, 0.12); if (k > forca) { forca = k; dica = d; } }
    if (B.dica) {
      B.dica.style.opacity = forca;
      if (dica) {
        if (R.ultimaDica !== dica.alvo) {
          const rot = dica.alvo.querySelector(".rot"), cont = dica.alvo.querySelector(".bv-cont");
          B.dica.innerHTML = (rot ? rot.textContent : "") + (cont ? `<i>${cont.textContent}</i>` : "");
          R.ultimaDica = dica.alvo;
        }
        const r = (dica.alvo.querySelector("svg") || dica.alvo).getBoundingClientRect();
        B.dica.style.transform = `translate(${B.fechada.direita + 16}px, ${r.top + r.height / 2}px) translateY(-50%) scale(${0.88 + 0.12 * forca})`;
      }
    }
    if (R.digita && B.digitado) {
      const D = R.digita, txt = B.digitado.dataset.texto || "";
      const n = t < D.t0 ? 0 : t >= D.ate ? 0 : Math.round(txt.length * clamp((t - D.t0) / (D.t1 - D.t0)));
      B.digitado.textContent = txt.slice(0, n);
      B.ph.style.opacity = n ? 0 : 1;
      const foco = t > D.t0 - 0.12 && t < D.ate;
      B.caret.style.opacity = foco && Math.floor(t * 2.6) % 2 === 0 ? 1 : foco && t < D.t1 ? 1 : 0;
    }
  }

  function cursorEm(t) {
    let pos = R.movs.length ? [R.movs[0].x0, R.movs[0].y0] : (R.cursor0 || [innerWidth * 0.72, innerHeight * 0.78]);
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
    R.inicio = op.inicio ?? 1.0;
    const ini = op.inicioRolagem ?? 2.4, fim = op.fim ?? 12.0;
    const barra = document.querySelector(".barra-v");
    R.paradas = paradas(barra ? 5 : Math.max(3, Math.round((fim - ini) / 2.4) + 1));
    if (barra) { R.B = medirBarra(barra); planejarComBarra(ini, fim); }
    else R.trechos = montarRolagem(R.paradas, ini, fim);
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
      if (!barra) planejarCursor(ini, fim);
      R.cursor = Object.assign(document.createElement("div"), { id: "cursor-clover" });
      R.cursor.innerHTML = '<svg class="seta-c" viewBox="0 0 28 28" width="54" height="54"><path d="M6 3.5v19.2l4.6-4.3 2.9 6.6 3.4-1.5-2.9-6.5h6.3z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>' +
        '<svg class="texto-c" viewBox="0 0 28 28" width="54" height="54" style="display:none"><path d="M10 4.5h8M10 23.5h8M14 4.5v19" fill="none" stroke="#fff" stroke-width="4.2" stroke-linecap="round"/><path d="M10 4.5h8M10 23.5h8M14 4.5v19" fill="none" stroke="#111" stroke-width="1.9" stroke-linecap="round"/></svg>';
      R.anel = Object.assign(document.createElement("div"), { id: "clique-clover" });
      document.body.append(R.anel, R.cursor);
    }
    return { paradas: R.paradas, altura: document.documentElement.scrollHeight, trechos: R.trechos.length, cursor: R.movs.length, barra: !!barra };
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
      else if (r.tipo === "barra") s.transform = `scaleY(${0.04 + 0.96 * p})`;
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
    if (R.B) quadroBarra(t);
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
      let aperta = 1, clique = null;
      for (const c of R.cliques) if (t >= c.t) clique = c;
      if (clique) {
        const dc = t - clique.t;
        if (dc < 0.2) aperta = 0.84;
        const ka = clamp(dc / 0.5);
        R.anel.style.opacity = (1 - ka) * 0.9;
        R.anel.style.transform = `translate(${clique.x}px, ${clique.y}px) scale(${0.2 + ka * 0.9})`;
      } else R.anel.style.opacity = 0;
      const textoC = R.texto.some((j) => t >= j.t0 && t < j.t1);
      R.cursor.querySelector(".seta-c").style.display = textoC ? "none" : "";
      R.cursor.querySelector(".texto-c").style.display = textoC ? "" : "none";
      R.cursor.style.opacity = aparece;
      R.cursor.style.transform = `translate(${x - 12}px, ${y - 7}px) scale(${aperta})`;
      for (const m of R.movs) {             // "hover": o botão ou cartão sobe e brilha com o cursor em cima
        if (!m.el) continue;
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


# ---- barra lateral de vidro (efeitos de interface que o cursor usa) ------------
CSS_BARRA = """
body.tem-barra{padding-left:118px}
.barra-v{position:fixed;left:18px;top:18px;bottom:18px;z-index:60;width:calc(92px + 250px * var(--abre,0));border-radius:32px;padding:16px 12px;
  display:flex;flex-direction:column;gap:5px;font-family:var(--f-texto);color:var(--texto);
  background:color-mix(in srgb,var(--fundo) 58%,transparent);backdrop-filter:blur(24px) saturate(160%);-webkit-backdrop-filter:blur(24px) saturate(160%);
  border:1px solid color-mix(in srgb,var(--texto) 14%,transparent);
  box-shadow:0 34px 70px -34px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.28)}
.barra-v .rot{display:block;overflow:hidden;white-space:nowrap;max-width:calc(220px * var(--abre,0));opacity:var(--abre,0);font-size:18px;font-weight:600}
.barra-v small{display:block;font-size:13px;font-weight:500;opacity:.6}
.barra-v svg{width:27px;height:27px;flex:none}
.bv-topo{display:flex;align-items:center;gap:calc(12px * var(--abre,0));padding:2px 0 10px calc(10px + 2px * (1 - var(--abre,0)))}
.bv-logo{width:48px;height:48px;border-radius:50%;flex:none;display:grid;place-items:center;background:var(--destaque);color:var(--sobre-destaque);
  font-family:var(--f-titulo);font-weight:800;font-size:22px;box-shadow:0 8px 20px -8px var(--destaque)}
.bv-seta{position:absolute;top:26px;right:-17px;width:34px;height:34px;border-radius:50%;display:grid;place-items:center;background:#fff;color:#111;
  box-shadow:0 6px 16px -4px rgba(0,0,0,.45);transform:rotate(calc(180deg * var(--abre,0)));outline:calc(var(--h,0) * 4px) solid color-mix(in srgb,var(--destaque) 45%,transparent)}
.bv-seta svg{width:18px;height:18px}
.bv-busca,.bv-item,.bv-noite,.bv-perfil{position:relative;display:flex;align-items:center;gap:calc(14px * var(--abre,0));min-height:52px;border-radius:17px;
  padding-left:calc(20.5px * (1 - var(--abre,0)) + 16px * var(--abre,0));padding-right:12px}
.bv-busca::before,.bv-item::before,.bv-noite::before,.bv-sub a::before{content:"";position:absolute;inset:0;border-radius:inherit;background:var(--texto);
  opacity:calc(var(--h,0) * .1);pointer-events:none}
.bv-busca{margin-bottom:4px}
.bv-busca::after{content:"";position:absolute;inset:0;border-radius:inherit;border:1px solid color-mix(in srgb,var(--texto) 16%,transparent);opacity:var(--abre,0)}
.bv-campo{position:relative;overflow:hidden;white-space:nowrap;max-width:calc(200px * var(--abre,0));opacity:var(--abre,0);font-size:18px;display:flex;align-items:center}
.bv-campo .ph{opacity:.5;position:absolute;left:0}
.bv-campo .caret{display:inline-block;width:2px;height:22px;background:var(--destaque);margin-left:2px;opacity:0}
.bv-busca kbd{margin-left:auto;font-size:12px;opacity:calc(var(--abre,0) * .55);border:1px solid currentColor;border-radius:7px;padding:2px 6px}
.bv-secao{position:relative;height:26px;margin:8px 0 2px;padding-left:18px;font-size:12.5px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.bv-secao span{opacity:calc(var(--abre,0) * .55)}
.bv-secao::before{content:"";position:absolute;left:24px;top:12px;width:20px;height:2px;border-radius:2px;background:currentColor;opacity:calc((1 - var(--abre,0)) * .3)}
.bv-item.ativo::after{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;
  background:linear-gradient(180deg,color-mix(in srgb,var(--texto) 16%,transparent),color-mix(in srgb,var(--texto) 7%,transparent));
  border:1px solid color-mix(in srgb,var(--texto) 22%,transparent);box-shadow:0 10px 22px -12px color-mix(in srgb,var(--destaque) 80%,transparent)}
.bv-item.ativo svg{color:var(--destaque)}
.bv-marca{position:absolute;left:40px;top:9px;width:12px;height:12px;border-radius:50%;background:#ef4444;border:2px solid var(--fundo);opacity:calc(1 - var(--abre,0))}
.bv-cont{margin-left:auto;font-style:normal;font-size:13px;font-weight:700;min-width:28px;height:24px;padding:0 8px;border-radius:12px;display:grid;place-items:center;
  background:color-mix(in srgb,var(--texto) 12%,transparent);opacity:var(--abre,0)}
.bv-cont.vermelho{background:#ef4444;color:#fff}
.bv-sub{position:relative;overflow:hidden;max-height:calc(150px * var(--sub,0) * var(--abre,0));opacity:var(--sub,0);margin-left:34px;padding-left:16px;
  border-left:2px solid color-mix(in srgb,var(--texto) 14%,transparent)}
.bv-sub a{position:relative;display:flex;align-items:center;gap:12px;height:42px;padding:0 10px;border-radius:12px;font-size:16.5px;white-space:nowrap}
.bv-sub i{width:10px;height:10px;border-radius:50%;flex:none}
.bv-espaco{flex:1}
.bv-chave{position:relative;margin-left:auto;width:48px;height:28px;border-radius:14px;flex:none;opacity:var(--abre,0);
  background:color-mix(in srgb,var(--texto) 16%,transparent)}
.bv-chave::before{content:"";position:absolute;inset:0;border-radius:inherit;background:var(--destaque);opacity:var(--noite,0)}
.bv-chave::after{content:"";position:absolute;top:3px;left:3px;width:22px;height:22px;border-radius:50%;background:#fff;
  transform:translateX(calc(20px * var(--noite,0)));box-shadow:0 2px 6px rgba(0,0,0,.3)}
.bv-noite svg{transform:rotate(calc(-30deg * var(--noite,0)))}
.bv-perfil{border-top:1px solid color-mix(in srgb,var(--texto) 12%,transparent);border-radius:0;padding-top:12px;margin-top:4px;min-height:64px}
.bv-avatar{position:relative;width:44px;height:44px;border-radius:50%;flex:none;display:grid;place-items:center;font-weight:800;color:#fff;
  background:linear-gradient(135deg,color-mix(in srgb,var(--destaque) 70%,#fff),color-mix(in srgb,var(--destaque) 70%,#000))}
.bv-avatar::after{content:"";position:absolute;right:-1px;bottom:-1px;width:13px;height:13px;border-radius:50%;background:#22c55e;border:2px solid var(--fundo)}
.bv-dica{position:fixed;left:0;top:0;z-index:70;display:flex;align-items:center;gap:10px;padding:10px 16px;border-radius:14px;font-family:var(--f-texto);
  font-size:17px;font-weight:600;white-space:nowrap;color:var(--texto);opacity:0;pointer-events:none;
  background:color-mix(in srgb,var(--fundo) 72%,transparent);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
  border:1px solid color-mix(in srgb,var(--texto) 16%,transparent);box-shadow:0 16px 34px -14px rgba(0,0,0,.5)}
.bv-dica i{font-style:normal;font-size:13px;padding:2px 8px;border-radius:9px;background:color-mix(in srgb,var(--texto) 12%,transparent)}
"""

_ICONES_BARRA = {
    "inicio": '<rect x="4" y="4" width="6.5" height="6.5" rx="3.2"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="3.2"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="3.2"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="3.2"/>',
    "raio": '<path d="M13 2.5L5 13.5h6l-1 8 8-11h-6z"/>',
    "cartao": '<rect x="3.5" y="5.5" width="17" height="13" rx="3"/><path d="M3.5 10h17M7.5 15h4"/>',
    "agenda": '<rect x="3.5" y="5" width="17" height="15.5" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    "conversa": '<path d="M20 11.5a7.5 7.5 0 01-11 6.6L4.5 19.5l1.3-4.2A7.5 7.5 0 1120 11.5z"/>',
    "busca": '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
    "lua": '<path d="M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z"/>',
    "sol": '<circle cx="12" cy="12" r="4.2"/><path d="M12 2.8v2M12 19.2v2M2.8 12h2M19.2 12h2M5.5 5.5l1.4 1.4M17.1 17.1l1.4 1.4M5.5 18.5l1.4-1.4M17.1 6.9l1.4-1.4"/>',
    "chevron": '<path d="M9.5 6l6 6-6 6"/>',
}


def _ib(nome: str, largura: float = 1.9) -> str:
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{largura}" '
            f'stroke-linecap="round" stroke-linejoin="round">{_ICONES_BARRA[nome]}</svg>')


def _barra_lateral(s: dict, p: dict) -> str:
    menu = (s.get("menu") or ["Serviços", "Sobre", "Depoimentos", "Contato"])[:4]
    menu += ["Contato"] * (4 - len(menu))
    itens = s.get("itens") or []
    cores_sub = ["var(--destaque)", "#22c55e", "#f59e0b"]
    subs = "".join(f'<a><i style="background:{cores_sub[i % 3]}"></i>{_e(it["nome"])}</a>' for i, it in enumerate(itens[:3]))
    nome = s.get("depoimento", {}).get("autor", "Ana Souza").split(",")[0].split(" ")[0][:14] or "Ana"
    dominio = re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s["marca"].lower()).encode("ascii", "ignore").decode())[:14] or "marca"
    busca = (itens[0]["nome"] if itens else s["segmento"]).lower()[:16]
    claro = not p["escuro"]
    return f"""
<aside class="barra-v">
  <div class="bv-topo"><span class="bv-logo">{_e(s["marca"][:1].upper())}</span><span class="rot"><b>{_e(s["marca"])}</b><small>{_e(s.get("segmento", ""))}</small></span></div>
  <span class="bv-seta">{_ib("chevron", 2.4)}</span>
  <div class="bv-busca">{_ib("busca")}<span class="bv-campo"><span class="ph">Buscar…</span><span class="digitado" data-texto="{_e(busca)}"></span><i class="caret"></i></span><kbd>⌘K</kbd></div>
  <p class="bv-secao"><span>Menu</span></p>
  <a class="bv-item ativo">{_ib("inicio")}<span class="rot">Início</span></a>
  <a class="bv-item">{_ib("raio")}<i class="bv-marca"></i><span class="rot">{_e(menu[0])}</span><em class="bv-cont">{len(itens[:3]) or 3}</em></a>
  <div class="bv-sub">{subs}</div>
  <a class="bv-item">{_ib("cartao")}<span class="rot">{_e(menu[1])}</span></a>
  <a class="bv-item">{_ib("conversa")}<i class="bv-marca"></i><span class="rot">{_e(menu[2])}</span><em class="bv-cont vermelho">2</em></a>
  <a class="bv-item">{_ib("agenda")}<span class="rot">{_e(menu[3])}</span></a>
  <div class="bv-espaco"></div>
  <div class="bv-noite">{_ib("lua" if claro else "sol")}<span class="rot">{"Modo noturno" if claro else "Modo claro"}</span><span class="bv-chave"></span></div>
  <div class="bv-perfil"><span class="bv-avatar">{_e(nome[:1].upper())}</span><span class="rot"><b>{_e(nome)}</b><small>{_e(nome.lower())}@{_e(dominio)}.com</small></span></div>
</aside>
<div class="bv-dica"></div>"""


def _tema_noturno(p: dict) -> str:
    """Cores do modo noturno (só para sites claros), para o cursor ligar o modo noturno no vídeo."""
    if p["escuro"]:
        return "<script>window.TEMAS = null;</script>"
    escuro = _misturar("#0d0c11", p["destaque"], 0.07)
    para = {"fundo": escuro, "texto": "#f3f1f6", "superficie": _misturar(escuro, "#ffffff", 0.07),
            "suave": _misturar("#f3f1f6", escuro, 0.42), "linha": _misturar(escuro, "#f3f1f6", 0.16)}
    de = {k: p[k] for k in para}
    return f"<script>window.TEMAS = {json.dumps({'de': de, 'para': para})};</script>"


# ---- montagem final -----------------------------------------------------------
def montar_site(s: dict, imagens: dict) -> str:
    """Devolve o HTML completo do site. `imagens` = {"hero": "img/hero.jpg", "item0": ..., "sobre0": ...}."""
    from . import modelos as extras
    modelo = s.get("modelo") if s.get("modelo") in MODELOS else "editorial"
    sorte = sum(map(ord, s.get("marca", ""))) + len(s.get("segmento", ""))
    cores = dict(s.get("cores") or {})
    claro = _luminancia(_hex(cores.get("fundo"), "#f6f1ea")) >= 0.2
    if modelo in ("luxo", "neon") and claro:          # sempre escuros
        cores.update(fundo="#0e0d0c" if modelo == "luxo" else "#07070c", texto="#f4efe7" if modelo == "luxo" else "#eeedfb",
                     superficie="#1a1816" if modelo == "luxo" else "#12121c")
    if modelo in ("minimal", "revista") and not claro:  # sempre claros
        cores.update(fundo="#f7f6f2" if modelo == "minimal" else "#f2ede3", texto="#141414", superficie="#ecebe6" if modelo == "minimal" else "#e7e0d2")
    p = paleta(cores)
    familia = FAMILIAS[modelo]
    f_titulo = s.get("fonte_titulo") if s.get("fonte_titulo") in familia else familia[sorte % len(familia)]
    f_texto = s.get("fonte_texto") if s.get("fonte_texto") in FONTES_TEXTO else "Inter"
    serifada = f_titulo in SERIFADAS
    if modelo in extras.MODELOS:
        funcao, css_modelo = extras.MODELOS[modelo]
        corpo = funcao(s, imagens)
    else:
        corpo = (_luxo if modelo == "luxo" else _editorial)(s, imagens)
        css_modelo = CSS_LUXO if modelo == "luxo" else CSS_EDITORIAL
    com_barra = s.get("barra", sorte % 4 != 0)   # a maioria dos sites tem a barra de vidro
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
  --f-titulo:"{f_titulo}";--f-texto:"{f_texto}";--peso-titulo:{500 if serifada else 800 if modelo == "impacto" else 700};--esp-titulo:{"-0.02em" if serifada else "-0.045em"}}}
{CSS_BASE}{css_modelo}{CSS_BARRA if com_barra else ""}
</style></head>
<body class="{"tem-barra" if com_barra else ""}">
{_barra_lateral(s, p) if com_barra else ""}
<header class="nav"><a class="logo"><i>{inicial}</i>{_e(s["marca"])}</a><nav>{links}</nav>
  <a class="botao">{_e(s["botao"])}</a></header>
{corpo}
<footer><span class="logo" style="font-size:22px"><i>{inicial}</i>{_e(s["marca"])}</span>
  <span>{_icone("local")} {_e(s.get("cidade", ""))}</span><span>© {_e(s["marca"])} · site-conceito</span></footer>
{_tema_noturno(p) if com_barra else ""}
{JS_ANIMACAO}
</body></html>"""
