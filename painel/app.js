"use strict";
/* Clover · Fábrica de Shorts — painel (sem dependências). */

const ESTACOES = [
  ["1 Pauta", "Pauta", "escolhe a história"],
  ["2 Roteiro", "Roteiro", "texto com o Gemini"],
  ["3 Narração", "Narração", "voz em português"],
  ["4 Cenas", "Cenas", "pinturas e paisagens"],
  ["5 Montagem", "Montagem", "junta cenas e voz"],
  ["6 Shorts", "Shorts", "legenda, música e 9:16"],
  ["7 Thumbnail", "Thumbnail", "capa do vídeo"],
  ["8 Agenda", "Agenda", "fila de aprovação"],
];
// O mesmo trabalho, quando o pedido é um Reels do Instagram (as estações do GitHub são as mesmas)
const ESTACOES_REELS = [
  ["1 Pauta", "Pauta", "escolhe o segmento"],
  ["2 Roteiro", "Conceito", "marca e textos (Gemini)"],
  ["3 Narração", "Trilha", "batida lo-fi"],
  ["4 Cenas", "Site", "fotos e páginas"],
  ["5 Montagem", "Notebook", "cena 3D e final"],
  ["6 Shorts", "Gravação", "site rolando na tela"],
  ["7 Thumbnail", "Capa", "capa do Reels"],
  ["8 Agenda", "Entrega", "prévia e aviso"],
];
const SEGMENTOS = [
  ["💈", "Barbearia"], ["🦷", "Clínica odontológica"], ["🏋️", "Academia"], ["🏠", "Imobiliária"], ["🐾", "Pet shop"],
  ["🚗", "Estética automotiva"], ["⚖️", "Advocacia"], ["🧁", "Doceria"], ["🍽️", "Restaurante"], ["☕", "Cafeteria"],
  ["💇", "Salão de beleza"], ["📐", "Arquitetura"], ["🧠", "Psicologia"], ["🗣️", "Escola de idiomas"], ["🍔", "Hamburgueria"],
  ["💍", "Joalheria"], ["✨", "Clínica de estética"], ["📊", "Contabilidade"], ["🔧", "Oficina mecânica"], ["💐", "Floricultura"],
  ["💪", "Personal trainer"], ["🏡", "Pousada"], ["📷", "Fotografia"], ["🍕", "Pizzaria"], ["🧘", "Estúdio de yoga"],
  ["🥗", "Nutricionista"], ["🖋️", "Estúdio de tatuagem"], ["👗", "Loja de roupas"], ["💻", "Coworking"], ["☀️", "Energia solar"],
];
const STATUS = {
  aguardando: "Aguardando", aprovado: "Pronto para postar", programado: "Programado",
  publicado: "Publicado", descartado: "Descartado", substituido: "Substituído",
};
const ACOES_TEXTO = {
  aprovar: "Aprovando", refazer: "Refazendo", descartar: "Descartando", publicado: "Marcando como publicado",
  produzir: "Pedindo vídeo novo", teste: "Pedindo vídeo de teste", instagram: "Pedindo o Reels",
};
const STATUS_REELS = { aguardando: "Pronto para postar", publicado: "Postado", descartado: "Descartado", substituido: "Refeito" };
const LINK_CHAVE = "https://github.com/settings/personal-access-tokens/new?name=Painel%20Clover" +
  "&description=Painel%20da%20F%C3%A1brica%20de%20Shorts&target_name=joaofernandesjunior826-art" +
  "&expires_in=365&actions=write&contents=write";
const PAGINAS = ["fabrica", "aprovacao", "agenda", "videos", "instagram", "historias", "config"];

const ICONES = {
  fabrica: '<path d="M3 20.5V10l5 3.2V10l5 3.2V6.5h3.5V4H20v16.5z"/><path d="M7 17h2m3 0h2m3 0h1"/>',
  aprovacao: '<rect x="4" y="3.5" width="16" height="17" rx="3"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>',
  agenda: '<rect x="3.5" y="5" width="17" height="15.5" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
  videos: '<rect x="3.5" y="4" width="17" height="16" rx="3"/><path d="M10.5 9.2v5.6l4.6-2.8z"/>',
  historias: '<path d="M4.5 5.5A2.5 2.5 0 017 3h12.5v15H7a2.5 2.5 0 00-2.5 2.5z"/><path d="M4.5 20.5A2.5 2.5 0 017 18h12.5v3H7"/>',
  instagram: '<rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="3.8"/><circle cx="17.1" cy="6.9" r="1" fill="currentColor" stroke="none"/>',
  surpresa: '<path d="M12 3l1.9 4.6L19 9.5l-4.1 2.9L16 18l-4-3-4 3 1.1-5.6L5 9.5l5.1-1.9z"/>',
  config: '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/>',
  busca: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
  lua: '<path d="M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z"/>',
  voltar: '<path d="M14.5 6l-6 6 6 6"/>',
  play: '<path d="M7 4.5v15l12.5-7.5z" fill="currentColor" stroke="none"/>',
  ok: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  refazer: '<path d="M20 11a8 8 0 10-2.3 5.7"/><path d="M20 4.5V11h-6.5"/>',
  lixo: '<path d="M4.5 7h15M9.5 7V4.5h5V7M6.5 7l1 13h9l1-13"/>',
  baixar: '<path d="M12 4v11M7 10.5l5 5 5-5M5 20h14"/>',
  copiar: '<rect x="8" y="8" width="12" height="12" rx="2.5"/><path d="M16 8V5.5A1.5 1.5 0 0014.5 4h-9A1.5 1.5 0 004 5.5v9A1.5 1.5 0 005.5 16H8"/>',
  externo: '<path d="M14 4h6v6M20 4l-9 9M18 14v4.5A1.5 1.5 0 0116.5 20h-11A1.5 1.5 0 014 18.5v-11A1.5 1.5 0 015.5 6H10"/>',
  mais: '<path d="M12 5v14M5 12h14"/>',
  sair: '<path d="M15 4h3.5A1.5 1.5 0 0120 5.5v13a1.5 1.5 0 01-1.5 1.5H15M10 16l-4-4 4-4M6 12h10"/>',
  fechar: '<path d="M6 6l12 12M18 6L6 18"/>',
  enviar: '<path d="M5 12l14-7-5 15-2.5-6z"/>',
};
const BOT = `<svg class="bot" viewBox="0 0 56 56" aria-hidden="true">
  <line class="bot-antena" x1="28" y1="7.5" x2="28" y2="14"/><circle class="bot-luz" cx="28" cy="6" r="3.2"/>
  <rect class="bot-cabeca" x="9" y="14" width="38" height="27" rx="10"/>
  <rect class="bot-olho" x="18.5" y="22.5" width="6" height="9" rx="3"/>
  <rect class="bot-olho" x="31.5" y="22.5" width="6" height="9" rx="3"/>
  <rect class="bot-corpo" x="20" y="43" width="16" height="7" rx="3.5"/>
  <text class="bot-z" x="44" y="13">z</text></svg>`;

const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];
const icone = (nome) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONES[nome] || ""}</svg>`;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const memoria = {
  ler(k) { try { return localStorage.getItem(k); } catch { return null; } },
  gravar(k, v) { try { localStorage.setItem(k, v); } catch { /* aba anônima */ } },
  apagar(k) { try { localStorage.removeItem(k); } catch { /* idem */ } },
};

const app = {
  token: memoria.ler("clover.token"),
  dados: null,
  pagina: "fabrica",
  busca: "",
  filtro: "todos",
  segmento: "",         // segmento escolhido na página Instagram
  pendentes: new Map(), // id do vídeo (ou "fabrica") -> {acao, desde}
  abertos: new Set(),   // cartões com o formulário de refazer aberto
  midias: new Map(),    // asset -> {url, ate}
  temporizador: null,
  estavaAtiva: false,
};

/* ---------------- API ---------------- */
async function api(caminho, opcoes = {}) {
  const r = await fetch(caminho, {
    method: opcoes.method || "GET",
    headers: { Authorization: `Bearer ${app.token}`, ...(opcoes.body ? { "Content-Type": "application/json" } : {}) },
    body: opcoes.body ? JSON.stringify(opcoes.body) : undefined,
  });
  let corpo = {};
  try { corpo = await r.json(); } catch { /* sem corpo */ }
  if (!r.ok) {
    const erro = new Error(corpo.erro || `Erro ${r.status}`);
    erro.status = r.status;
    throw erro;
  }
  return corpo;
}

async function urlMidia(asset) {
  const guardada = app.midias.get(asset);
  if (guardada && guardada.ate > Date.now()) return guardada.url;
  const { url } = await api(`/api/midia?asset=${asset}`);
  app.midias.set(asset, { url, ate: Date.now() + 4 * 60 * 1000 });
  return url;
}

async function carregar({ leve = false } = {}) {
  try {
    if (leve && app.dados) {
      const { execucao } = await api("/api/estado?leve=1");
      app.dados.execucao = execucao;
      const ativa = !!execucao.ativa;
      if (app.estavaAtiva && !ativa) return carregar(); // terminou: busca tudo de novo
      app.estavaAtiva = ativa;
    } else {
      app.dados = await api("/api/estado");
      app.estavaAtiva = !!app.dados.execucao.ativa;
      limparPendentes();
    }
    desenhar();
  } catch (erro) {
    if (erro.status === 401 || erro.status === 404 || (erro.status === 403 && !app.dados)) {
      desconectar(erro.message);
      return;
    }
    if (!app.dados) $("#conteudo").innerHTML = `<div class="vazio"><img src="${logo()}" alt="">${esc(erro.message)}<br><br><button class="botao" data-acao="recarregar">Tentar de novo</button></div>`;
    else avisar(erro.message, true);
  } finally {
    agendar();
  }
}

function agendar() {
  clearTimeout(app.temporizador);
  const d = app.dados;
  const agitado = d && (d.execucao.ativa || d.pedidos.length || app.pendentes.size);
  app.temporizador = setTimeout(() => {
    if (document.hidden) return agendar();
    carregar({ leve: !!(d && d.execucao.ativa && !d.pedidos.length && !app.pendentes.size) });
  }, agitado ? 6000 : 45000);
}

function limparPendentes() {
  const videos = new Map((app.dados?.videos || []).map((v) => [v.id, v]));
  for (const [id, p] of app.pendentes) {
    const v = videos.get(id);
    const resolvido = (p.acao === "aprovar" && v && ["aprovado", "programado"].includes(v.status)) ||
      (p.acao === "descartar" && v && v.status === "descartado") ||
      (p.acao === "publicado" && v && v.status === "publicado") ||
      (p.acao === "refazer" && v && v.status === "substituido");
    if (resolvido || Date.now() - p.desde > 15 * 60 * 1000 ||
        (["produzir", "teste", "instagram"].includes(p.acao) && app.dados.execucao.ativa)) app.pendentes.delete(id);
  }
}

async function pedir(acao, extra = {}, botao) {
  if (botao) botao.disabled = true;
  try {
    await api("/api/acao", { method: "POST", body: { acao, ...extra } });
    app.pendentes.set(extra.id || "fabrica", { acao, desde: Date.now() });
    avisar(`${ACOES_TEXTO[acao] || "Pedido enviado"}… a fábrica já recebeu o pedido.`);
    desenhar();
    clearTimeout(app.temporizador);
    app.temporizador = setTimeout(() => carregar(), 5000);
  } catch (erro) {
    avisar(erro.message, true);
    if (botao) botao.disabled = false;
  }
}

/* ---------------- Utilidades ---------------- */
const fuso = { timeZone: "America/Sao_Paulo" };
function dataCurta(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const dia = d.toLocaleDateString("pt-BR", { ...fuso, day: "2-digit", month: "2-digit" });
  const hora = d.toLocaleTimeString("pt-BR", { ...fuso, hour: "2-digit", minute: "2-digit" });
  return `${dia} às ${hora}`;
}
function haQuanto(iso) {
  const s = Math.round((Date.now() - new Date(iso)) / 1000);
  if (s < 60) return "agora há pouco";
  if (s < 3600) return `há ${Math.round(s / 60)} min`;
  if (s < 86400) return `há ${Math.round(s / 3600)} h`;
  return `há ${Math.round(s / 86400)} dia(s)`;
}
function proximoVideo(horarios) {
  const agora = new Date(new Date().toLocaleString("en-US", fuso));
  const hs = (horarios && horarios.length ? horarios : [9]).slice().sort((a, b) => a - b);
  const prox = hs.find((h) => h > agora.getHours());
  return prox !== undefined ? `hoje às ${prox}h` : `amanhã às ${hs[0]}h`;
}
function logo() { return document.documentElement.dataset.tema === "claro" ? "marca-clara.png" : "marca.png"; }
const ehReels = (v) => v.tipo === "instagram";
function videosCom(...status) { return (app.dados?.videos || []).filter((v) => !ehReels(v) && status.includes(v.status)); }
function reels() { return (app.dados?.videos || []).filter(ehReels); }
function rotuloStatus(v) { return (ehReels(v) ? STATUS_REELS[v.status] : STATUS[v.status]) || v.status; }
function execucaoEhReels(exec) { return /instagram/i.test((exec && exec.ativa && exec.ativa.titulo) || ""); }
function previa(v) { return app.dados?.previas?.[v.id] || {}; }

function avisar(texto, erro = false) {
  const el = document.createElement("div");
  el.className = `aviso vidro${erro ? " erro" : ""}`;
  el.textContent = texto;
  $("#avisos").append(el);
  setTimeout(() => el.remove(), erro ? 6500 : 3800);
}

async function copiar(texto) {
  try { await navigator.clipboard.writeText(texto); }
  catch {
    const t = Object.assign(document.createElement("textarea"), { value: texto });
    document.body.append(t); t.select(); document.execCommand("copy"); t.remove();
  }
  avisar("Copiado!");
}

/* ---------------- Barra lateral ---------------- */
function desenharBarra() {
  const d = app.dados;
  for (const a of $$(".item[data-pagina]")) a.classList.toggle("ativo", a.dataset.pagina === app.pagina);
  if (!d) return;
  const aguardando = videosCom("aguardando").length;
  const prontos = videosCom("aprovado").length;
  $("#m-aprovacao").textContent = aguardando || "";
  $("#m-agenda").textContent = prontos || "";
  $("#m-instagram").textContent = reels().filter((v) => v.status === "aguardando").length || "";
  $("#m-fabrica").classList.toggle("ligado", !!d.execucao.ativa);
  const cfg = d.estado.config || {};
  $("#m-config").classList.toggle("ligado", !cfg.gemini);
  if (d.usuario) {
    $("#avatar").src = d.usuario.avatar;
    $("#perfil-nome").textContent = d.usuario.nome || d.usuario.login;
  }
  $("#perfil-repo").textContent = d.repo;
}

function recolher(sim) {
  $("#app").classList.toggle("recolhida", sim);
  memoria.gravar("clover.recolhida", sim ? "1" : "0");
  const celular = matchMedia("(max-width: 760px)").matches;
  $("#veu").hidden = sim || !celular;
}

/* ---------------- Páginas ---------------- */
function desenhar() {
  desenharBarra();
  if (!app.dados) return;
  const paginas = { fabrica: pgFabrica, aprovacao: pgAprovacao, agenda: pgAgenda, videos: pgVideos, instagram: pgInstagram, historias: pgHistorias, config: pgConfig };
  const foco = document.activeElement && document.activeElement.id;
  $("#conteudo").innerHTML = paginas[app.pagina]();
  if (foco && $("#" + foco) && foco !== "busca") $("#" + foco).focus();
  carregarCapas();
}

function topo(titulo, sub, direita = "") {
  return `<header class="topo-pagina"><div><h1>${esc(titulo)}</h1><p class="sub">${sub}</p></div>${direita}</header>`;
}

function estadoDasEstacoes() {
  const exec = app.dados.execucao;
  const passos = new Map((exec.etapas || []).map((e) => [e.nome, e]));
  return (execucaoEhReels(exec) ? ESTACOES_REELS : ESTACOES).map(([nome, rotulo, desc], i) => {
    const p = passos.get(nome);
    let classe = "espera";
    if (p && p.status === "in_progress") classe = "ativa";
    else if (p && p.conclusao === "success") classe = "feita";
    else if (p && p.conclusao === "failure") classe = "erro";
    return { numero: String(i + 1).padStart(2, "0"), rotulo, desc, classe };
  });
}

function pgFabrica() {
  const d = app.dados;
  const exec = d.execucao;
  const cfg = d.estado.config || {};
  const estacoes = estadoDasEstacoes();
  const ativa = estacoes.find((e) => e.classe === "ativa");
  const preparando = exec.ativa && !ativa && !estacoes.some((e) => e.classe !== "espera");
  let sub;
  if (ativa) sub = `${execucaoEhReels(exec) ? "Fazendo um <b>Reels do Instagram</b>: estação" : "Trabalhando na estação"} <b>${esc(ativa.rotulo)}</b>`;
  else if (exec.ativa) sub = preparando ? "Lendo os pedidos e preparando as máquinas…" : "Terminando…";
  else sub = `Parada. Próximo vídeo ${proximoVideo(cfg.horarios)}.`;
  const falha = d.estado.ultima_falha;
  if (!exec.ativa && falha && Date.now() - new Date(falha.quando) < 24 * 3600 * 1000)
    sub += ` <span style="color:var(--vermelho)">Última falha: estação ${esc(falha.estacao)}, ${haQuanto(falha.quando)}.</span>`;

  const estacoesHtml = estacoes.map((e) => `
    <div class="estacao ${e.classe}">
      <span class="num">${e.numero}</span>
      ${e.classe === "feita" ? '<span class="marcador">✓</span>' : e.classe === "erro" ? '<span class="marcador">!</span>' : ""}
      ${BOT}
      <b>${esc(e.rotulo)}</b><small>${esc(e.desc)}</small>
      <span class="esteira"></span>
    </div>`).join("");

  const n = (s) => videosCom(s).length;
  const pedindo = app.pendentes.get("fabrica");
  const recentes = (exec.recentes || []).slice(0, 5).map((r) => {
    const classe = r.status !== "completed" ? "andamento" : r.conclusao === "success" ? "sucesso" : r.conclusao === "cancelled" || r.conclusao === "skipped" ? "" : "falha";
    let origem = { schedule: "Agenda automática", push: "Pedido do painel", workflow_dispatch: "Botão do GitHub" }[r.evento] || r.evento;
    if (/instagram/i.test(r.titulo || "")) origem = "Reels do Instagram";
    const res = r.status !== "completed" ? "em andamento" : r.conclusao === "success" ? "ok" : r.conclusao === "failure" ? "falhou" : r.conclusao;
    return `<a class="lista-item" href="${esc(r.url)}" target="_blank" rel="noopener"><span class="bolinha ${classe}"></span>
      <span class="texto"><b>${esc(origem)}</b><small>${dataCurta(r.inicio)} · ${esc(res)}</small></span>${icone("externo")}</a>`;
  }).join("") || '<p class="sub">Nenhuma execução ainda.</p>';

  return topo("fábrica", sub, `<span class="selo ${exec.ativa ? "vivo" : ""}"><i></i>${exec.ativa ? "ao vivo" : "parada"}</span>`) + `
    <section class="linha-producao vidro"><div class="estacoes">${estacoesHtml}</div></section>
    <section class="kpis">
      <div class="kpi vidro destaque"><b>${n("aguardando")}</b><span>esperando aprovação</span></div>
      <div class="kpi vidro"><b>${n("aprovado")}</b><span>prontos para postar</span></div>
      <div class="kpi vidro"><b>${n("programado")}</b><span>programados</span></div>
      <div class="kpi vidro"><b>${n("publicado")}</b><span>publicados</span></div>
    </section>
    <section class="grade-2">
      <div class="cartao vidro">
        <h2>Fazer um vídeo agora <small>opcional</small></h2>
        <p class="sub" style="margin:0 0 12px">Deixe em branco para a próxima história da lista, ou escreva um tema.</p>
        <form class="linha-form" data-form="produzir">
          <input class="campo" name="tema" placeholder="Ex.: Sansão e Dalila" maxlength="200">
          <button class="botao principal" type="submit" ${pedindo || exec.ativa ? "disabled" : ""}>${icone("mais")}Produzir</button>
        </form>
        ${!cfg.gemini ? `<p class="sub" style="margin-top:12px">Sem a chave do Gemini ainda? <button class="botao pequeno" data-acao="teste" ${pedindo ? "disabled" : ""}>Fazer vídeo de teste</button></p>` : ""}
        ${pedindo ? `<p class="sub" style="margin-top:10px">⏳ ${esc(ACOES_TEXTO[pedindo.acao])}…</p>` : ""}
      </div>
      <div class="cartao vidro"><h2>Atividade recente</h2><div class="lista">${recentes}</div></div>
    </section>`;
}

function cartaoVideo(v, modo) {
  const p = app.pendentes.get(v.id);
  const etiquetas = [`<span class="etiqueta ${p ? "processando" : v.status}">${p ? "⏳ " + esc(ACOES_TEXTO[p.acao]) : esc(STATUS[v.status] || v.status)}</span>`];
  if (v.tipo === "teste") etiquetas.push('<span class="etiqueta">teste</span>');
  if (v.tipo === "refazer") etiquetas.push('<span class="etiqueta">refeito</span>');
  const meta = [v.referencia, v.duracao_seg ? `${v.duracao_seg} s` : "", dataCurta(v.data)].filter(Boolean).map(esc).join(" · ");
  let acoes = "";
  if (modo === "aprovacao") {
    acoes = `<button class="botao principal pequeno" data-acao="aprovar" data-id="${v.id}" ${p ? "disabled" : ""}>${icone("ok")}Aprovar</button>
      <button class="botao pequeno" data-acao="abrir-refazer" data-id="${v.id}" ${p ? "disabled" : ""}>${icone("refazer")}Refazer</button>
      <button class="botao pequeno perigo" data-acao="descartar" data-id="${v.id}" ${p ? "disabled" : ""} aria-label="Descartar">${icone("lixo")}</button>`;
  } else if (modo === "postar") {
    acoes = `<button class="botao pequeno" data-acao="baixar" data-id="${v.id}">${icone("baixar")}Baixar</button>
      <button class="botao pequeno" data-acao="copiar-titulo" data-id="${v.id}">${icone("copiar")}Título</button>
      <button class="botao principal pequeno" data-acao="publicado" data-id="${v.id}" ${p ? "disabled" : ""}>${icone("ok")}Já postei</button>`;
  }
  const refazer = app.abertos.has(v.id) ? `
    <form class="refazer-form" data-form="refazer" data-id="${v.id}">
      <textarea class="campo" name="ajuste" maxlength="500" placeholder="O que mudar? (opcional) Ex.: mais curto, comece pela batalha"></textarea>
      <div class="linha-acoes"><button class="botao principal pequeno" type="submit">${icone("enviar")}Refazer agora</button>
      <button class="botao pequeno" type="button" data-acao="fechar-refazer" data-id="${v.id}">Cancelar</button></div>
    </form>` : "";
  return `<article class="video-cartao vidro">
    <div class="capa" data-acao="assistir" data-id="${v.id}" role="button" aria-label="Assistir">
      ${previa(v).jpg ? `<img data-asset="${previa(v).jpg}" alt="">` : ""}
      <span class="play">${icone("play")}</span>
    </div>
    <div class="video-info">
      <div class="linha-acoes">${etiquetas.join("")}</div>
      <h3>${esc(v.titulo)}</h3>
      <div class="meta">${meta}</div>
      ${v.ajuste ? `<div class="meta">✏️ ${esc(v.ajuste)}</div>` : ""}
      <div class="linha-acoes">${acoes}</div>
    </div>${refazer}
  </article>`;
}

function pgAprovacao() {
  const fila = videosCom("aguardando");
  const sub = fila.length ? `${fila.length} vídeo(s) esperando você. Assista, aprove ou peça para refazer.` : "Tudo em dia por aqui.";
  const vazio = `<div class="vazio vidro cartao"><img src="${logo()}" alt="">Nada esperando aprovação.<br>O próximo vídeo sai ${proximoVideo(app.dados.estado.config?.horarios)}.</div>`;
  return topo("aprovação", sub) + (fila.length ? `<div class="fila">${fila.map((v) => cartaoVideo(v, "aprovacao")).join("")}</div>` : vazio);
}

function pgAgenda() {
  const cfg = app.dados.estado.config || {};
  const prontos = videosCom("aprovado");
  const programados = videosCom("programado").sort((a, b) => (a.youtube?.agendado_para || "").localeCompare(b.youtube?.agendado_para || ""));
  const publicados = videosCom("publicado").slice(0, 10);
  const banner = cfg.youtube_auto ? "" : `<div class="aviso-banner"><b>Como postar:</b> toque em <b>Baixar</b>, abra o app do YouTube › <b>+</b> › <b>Enviar um vídeo</b>, cole o título e publique (ou programe). Depois toque em <b>Já postei</b>. O envio automático só pode ser ligado quando a Google aprovar a auditoria do seu projeto (veja Configurações).</div>`;
  const listaProg = programados.map((v) => `<div class="lista-item"><span class="mini">${previa(v).jpg ? `<img data-asset="${previa(v).jpg}" alt="">` : ""}</span>
    <span class="texto"><b>${esc(v.titulo)}</b><small>📅 ${dataCurta(v.youtube?.agendado_para)}</small></span>
    ${v.youtube?.id ? `<a class="botao pequeno" target="_blank" rel="noopener" href="https://studio.youtube.com/video/${esc(v.youtube.id)}/edit">${icone("externo")}</a>` : ""}</div>`).join("");
  const listaPub = publicados.map((v) => `<div class="lista-item"><span class="mini">${previa(v).jpg ? `<img data-asset="${previa(v).jpg}" alt="">` : ""}</span>
    <span class="texto"><b>${esc(v.titulo)}</b><small>✅ ${dataCurta(v.publicado_em || v.data)}</small></span></div>`).join("");
  return topo("agenda", `${prontos.length} pronto(s) para postar · ${programados.length} programado(s)`) + banner +
    (prontos.length ? `<h2 class="mono" style="font-size:15px;margin:4px 0 12px">Prontos para postar</h2><div class="fila" style="margin-bottom:18px">${prontos.map((v) => cartaoVideo(v, "postar")).join("")}</div>` : "") +
    `<div class="cartao vidro"><h2>Programados no YouTube</h2><div class="lista">${listaProg || '<p class="sub">Nenhum vídeo programado.</p>'}</div></div>
     <div class="cartao vidro"><h2>Publicados</h2><div class="lista">${listaPub || '<p class="sub">Nenhum vídeo marcado como publicado ainda.</p>'}</div></div>`;
}

function pgVideos() {
  const termo = app.busca.trim().toLowerCase();
  const filtros = ["todos", "aguardando", "aprovado", "programado", "publicado", "descartado"];
  const lista = app.dados.videos.filter((v) => !ehReels(v) &&
    (app.filtro === "todos" || v.status === app.filtro) &&
    (!termo || `${v.titulo} ${v.historia} ${v.referencia}`.toLowerCase().includes(termo)));
  const itens = lista.map((v) => `<div class="lista-item" data-acao="assistir" data-id="${v.id}" role="button" style="cursor:pointer">
      <span class="mini">${previa(v).jpg ? `<img data-asset="${previa(v).jpg}" alt="">` : ""}</span>
      <span class="texto"><b>${esc(v.titulo)}</b><small>${esc(v.referencia || "")} · ${dataCurta(v.data)}</small></span>
      <span class="etiqueta ${v.status}">${esc(STATUS[v.status] || v.status)}</span></div>`).join("");
  return topo("vídeos", `${app.dados.videos.filter((v) => !ehReels(v)).length} Short(s) feitos pela fábrica${termo ? ` · busca: “${esc(app.busca)}”` : ""}`) +
    `<div class="filtros">${filtros.map((f) => `<button class="filtro ${app.filtro === f ? "ativo" : ""}" data-acao="filtro" data-filtro="${f}">${f === "todos" ? "Todos" : esc(STATUS[f])}</button>`).join("")}</div>
     <div class="cartao vidro"><div class="lista">${itens || '<p class="sub">Nenhum vídeo por aqui.</p>'}</div></div>`;
}

/* ---------------- Instagram: Reels com sites-conceito ---------------- */
function cartaoReels(v) {
  const p = app.pendentes.get(v.id);
  const etiqueta = `<span class="etiqueta ${p ? "processando" : v.status === "aguardando" ? "pronto" : v.status}">${p ? "⏳ " + esc(ACOES_TEXTO[p.acao]) : esc(rotuloStatus(v))}</span>`;
  const meta = [v.segmento, v.duracao_seg ? `${v.duracao_seg} s` : "", dataCurta(v.data)].filter(Boolean).map(esc).join(" · ");
  const ativo = ["aguardando", "aprovado"].includes(v.status);
  const acoes = `<button class="botao pequeno" data-acao="baixar" data-id="${v.id}">${icone("baixar")}Baixar</button>
      <button class="botao pequeno" data-acao="copiar-legenda" data-id="${v.id}">${icone("copiar")}Legenda</button>
      ${ativo ? `<button class="botao principal pequeno" data-acao="publicado" data-id="${v.id}" ${p ? "disabled" : ""}>${icone("ok")}Já postei</button>` : ""}
      ${ativo ? `<button class="botao pequeno" data-acao="abrir-refazer" data-id="${v.id}" ${p ? "disabled" : ""} aria-label="Refazer">${icone("refazer")}</button>
      <button class="botao pequeno perigo" data-acao="descartar" data-id="${v.id}" ${p ? "disabled" : ""} aria-label="Descartar">${icone("lixo")}</button>` : ""}`;
  const refazer = app.abertos.has(v.id) ? `
    <form class="refazer-form" data-form="refazer" data-id="${v.id}">
      <textarea class="campo" name="ajuste" maxlength="500" placeholder="O que mudar? (opcional) Ex.: cores verde e dourado, nome mais curto, tema escuro"></textarea>
      <div class="linha-acoes"><button class="botao principal pequeno" type="submit">${icone("enviar")}Refazer agora</button>
      <button class="botao pequeno" type="button" data-acao="fechar-refazer" data-id="${v.id}">Cancelar</button></div>
    </form>` : "";
  return `<article class="video-cartao vidro">
    <div class="capa" data-acao="assistir" data-id="${v.id}" role="button" aria-label="Assistir">
      ${previa(v).jpg ? `<img data-asset="${previa(v).jpg}" alt="">` : ""}
      <span class="play">${icone("play")}</span>
    </div>
    <div class="video-info">
      <div class="linha-acoes">${etiqueta}</div>
      <h3>${esc(v.marca || v.titulo)}</h3>
      <div class="meta">${meta}</div>
      ${v.ajuste ? `<div class="meta">✏️ ${esc(v.ajuste)}</div>` : ""}
      <div class="linha-acoes">${acoes}</div>
    </div>${refazer}
  </article>`;
}

function pgInstagram() {
  const d = app.dados;
  const cfg = d.estado.config || {};
  const todos = reels();
  const prontos = todos.filter((v) => ["aguardando", "aprovado"].includes(v.status));
  const postados = todos.filter((v) => v.status === "publicado").slice(0, 12);
  const pedindo = app.pendentes.get("fabrica");
  const ocupada = !!d.execucao.ativa && !pedindo;
  const escolhido = app.segmento || "";
  const chips = SEGMENTOS.map(([emoji, nome]) =>
    `<button type="button" class="chip ${escolhido === nome ? "ativo" : ""}" data-acao="segmento" data-segmento="${esc(nome)}">${emoji} ${esc(nome)}</button>`).join("");
  const andamento = ocupada ? `<p class="sub" style="margin-top:12px">⏳ ${execucaoEhReels(d.execucao) ? "A fábrica está fazendo um Reels agora" : "A fábrica está ocupada com outro vídeo; o seu pedido entra na fila"}. Acompanhe em <a href="#fabrica">Fábrica</a>.</p>` :
    pedindo ? `<p class="sub" style="margin-top:12px">⏳ ${esc(ACOES_TEXTO[pedindo.acao] || "Pedido enviado")}…</p>` : "";
  const dicaFotos = !cfg.pixabay && !cfg.pexels ? `<div class="aviso-banner"><b>Dica:</b> com a chave grátis do <b>Pixabay</b>, os sites ganham fotos profissionais do segmento. Cole em <a href="#config">Configurações › Chaves da fábrica</a>.</div>` : "";
  const dicaGemini = !cfg.gemini ? `<div class="aviso-banner">Sem a chave do Gemini, a fábrica faz um Reels de exemplo (barbearia). Cole a chave em <a href="#config">Configurações</a> para ela criar sites novos.</div>` : "";
  return topo("instagram", "Reels de 30 s: um site-conceito da Clover rolando no notebook") + dicaGemini + dicaFotos + `
    <div class="cartao vidro">
      <h2>Criar um Reels</h2>
      <p class="sub" style="margin:0 0 12px">Escolha o segmento do site (ou deixe a fábrica escolher). A IA inventa a marca, os textos e as cores.</p>
      <div class="chips">${chips}</div>
      <form class="form-reels" data-form="instagram">
        <input class="campo" name="tema" maxlength="60" placeholder="Ou escreva outro segmento (ex.: loja de vinhos)" value="${esc(SEGMENTOS.some(([, n]) => n === escolhido) ? "" : escolhido)}">
        <input class="campo" name="ajuste" maxlength="300" placeholder="Algum pedido? (opcional) Ex.: tema escuro, cores verde e dourado">
        <div class="linha-acoes">
          <button class="botao principal" type="submit" ${pedindo ? "disabled" : ""}>${icone("mais")}Criar Reels${escolhido ? ` de ${esc(escolhido)}` : ""}</button>
          <button class="botao" type="button" data-acao="reels-surpresa" ${pedindo ? "disabled" : ""}>${icone("surpresa")}Surpreenda-me</button>
        </div>
      </form>
      ${andamento}
      <p class="sub" style="margin-top:10px">Leva uns 5 minutos. Os sites são conceitos: as marcas são inventadas e a legenda já avisa isso.</p>
    </div>
    ${prontos.length ? `<h2 class="mono" style="font-size:15px;margin:4px 0 12px">Prontos para postar</h2><div class="fila" style="margin-bottom:18px">${prontos.map(cartaoReels).join("")}</div>` : ""}
    <div class="aviso-banner"><b>Como postar:</b> toque em <b>Baixar</b>, abra o Instagram › <b>+</b> › <b>Reels</b>, escolha o vídeo e, se quiser, uma música em alta. Toque em <b>Legenda</b> aqui para copiar o texto. Depois, <b>Já postei</b>.</div>
    <div class="cartao vidro"><h2>Já postados</h2><div class="lista">${postados.map((v) => `<div class="lista-item" data-acao="assistir" data-id="${v.id}" role="button" style="cursor:pointer">
      <span class="mini">${previa(v).jpg ? `<img data-asset="${previa(v).jpg}" alt="">` : ""}</span>
      <span class="texto"><b>${esc(v.marca || v.titulo)}</b><small>${esc(v.segmento || "")} · ${dataCurta(v.publicado_em || v.data)}</small></span></div>`).join("") || '<p class="sub">Nenhum Reels marcado como postado ainda.</p>'}</div></div>`;
}

function pgHistorias() {
  const feitas = new Set(app.dados.videos.map((v) => v.historia));
  const proxima = app.dados.historias.find((h) => !feitas.has(h.titulo));
  const termo = app.busca.trim().toLowerCase();
  const itens = app.dados.historias.filter((h) => !termo || h.titulo.toLowerCase().includes(termo)).map((h) => {
    const feita = feitas.has(h.titulo);
    const ehProxima = proxima && h.titulo === proxima.titulo;
    return `<div class="lista-item"><span class="bolinha ${feita ? "sucesso" : ehProxima ? "andamento" : ""}"></span>
      <span class="texto"><b>${esc(h.titulo)}</b><small>${esc(h.referencia)}${feita ? " · já virou vídeo" : ehProxima ? " · próxima da fila" : ""}</small></span>
      <button class="botao pequeno" data-acao="produzir-historia" data-tema="${esc(h.titulo)}">${icone("mais")}Fazer</button></div>`;
  }).join("");
  return topo("histórias", `${app.dados.historias.length} histórias na lista · ${feitas.size} já viraram vídeo`) +
    `<div class="cartao vidro"><div class="lista">${itens}</div></div>
     <p class="sub">Para mudar a lista, edite o arquivo <span class="mono">dados/historias.txt</span> no GitHub.</p>`;
}

const CHAVES = [
  { nome: "GEMINI_API_KEY", titulo: "Gemini (roteiro)", obrigatoria: true, cfg: "gemini",
    ajuda: "Obrigatória. Crie em aistudio.google.com/apikey", link: "https://aistudio.google.com/apikey" },
  { nome: "PIXABAY_API_KEY", titulo: "Pixabay (fotos e paisagens)", cfg: "pixabay",
    ajuda: "Opcional. Fotos profissionais nos sites dos Reels e paisagens nos Shorts.", link: "https://pixabay.com/api/docs/" },
  { nome: "PEXELS_API_KEY", titulo: "Pexels (paisagens)", cfg: "pexels",
    ajuda: "Opcional. O Pexels pausou chaves novas; use se já tiver uma." },
  { nome: "TELEGRAM_BOT_TOKEN", titulo: "Telegram: token do bot", cfg: "telegram",
    ajuda: "Opcional. Para receber os vídeos no celular." },
  { nome: "TELEGRAM_CHAT_ID", titulo: "Telegram: número do chat", cfg: "telegram",
    ajuda: "Opcional. Vem junto com o token do bot." },
];

function campoChave(c, cfg, cofre) {
  const noCofre = !!cofre[c.nome];
  const naFabrica = !!cfg[c.cfg];
  const ok = noCofre || naFabrica;
  const situacao = ok ? (noCofre ? "Guardada no cofre" : "Cadastrada no GitHub") : c.ajuda;
  return `<form class="chave-linha" data-form="chave" data-nome="${c.nome}">
    <div class="chave-topo"><span class="sinal ${ok ? "ok" : c.obrigatoria ? "falta" : "opcional"}">${ok ? "✓" : c.obrigatoria ? "!" : "–"}</span>
      <span><b>${esc(c.titulo)}</b><small>${esc(situacao)}${!ok && c.link ? ` · <a href="${c.link}" target="_blank" rel="noopener">abrir</a>` : ""}</small></span></div>
    <div class="linha-form"><input class="campo mono" name="valor" type="password" autocomplete="off" placeholder="${ok ? "Colar uma nova para trocar" : "Cole a chave aqui"}">
      <button class="botao principal pequeno" type="submit">Salvar</button></div>
  </form>`;
}

function pgConfig() {
  const d = app.dados;
  const cfg = d.estado.config || {};
  const conhecida = Object.keys(cfg).length > 0;
  const item = (ok, titulo, texto, opcional = false) => `<li><span class="sinal ${ok ? "ok" : opcional ? "opcional" : "falta"}">${ok ? "✓" : opcional ? "–" : "!"}</span>
    <span><b>${titulo}</b><small>${texto}</small></span></li>`;
  const segredos = `https://github.com/${d.repo}/settings/secrets/actions`;
  const variaveis = `https://github.com/${d.repo}/settings/variables/actions`;
  return topo("configurações", "O que já está pronto e o que falta") + `
    <div class="cartao vidro"><h2>Chaves da fábrica</h2>
      <p class="sub" style="margin:0 0 14px">Cole a chave e toque em <b>Salvar</b>. Ela fica guardada com criptografia e só a sua fábrica consegue abrir.</p>
      <div class="chaves">${CHAVES.map((c) => campoChave(c, cfg, d.cofre || {})).join("")}</div>
      ${conhecida ? "" : '<p class="sub" style="margin-top:12px">A fábrica confirma as chaves na próxima vez que rodar.</p>'}
    </div>
    <div class="cartao vidro"><h2>Agenda e vídeo</h2>
      <ul class="checklist">
        ${item(true, "Vídeo novo todo dia", `às ${(cfg.horarios || [9]).map((h) => h + "h").join(", ")} (horário de Brasília). Para mudar: variável HORARIOS, ex.: 9,18.`)}
        ${item(true, "Duração", `${cfg.duracao_alvo || 60} segundos. Variável DURACAO_ALVO_SEG.`)}
        ${item(true, "Voz", esc(cfg.voz || "pt-BR-AntonioNeural") + ". Variável VOZ.")}
        ${item(true, "Reels do Instagram", `Final com o botão “${esc(cfg.instagram_cta || "Peça o seu site")}” e ${esc(cfg.instagram_arroba || "@_clover.sd_")}. Variáveis INSTAGRAM_CTA e INSTAGRAM_ARROBA.`)}
      </ul>
      <div class="linha-acoes" style="margin-top:14px"><a class="botao pequeno" href="${variaveis}" target="_blank" rel="noopener">${icone("externo")}Mudar ajustes (Variables)</a></div>
    </div>
    <div class="cartao vidro"><h2>Este aparelho</h2>
      <p class="sub" style="margin:0 0 12px">Conectado como <b>${esc(d.usuario?.login || "?")}</b> ao repositório <span class="mono">${esc(d.repo)}</span>.</p>
      <div class="linha-acoes"><a class="botao pequeno" href="https://github.com/${d.repo}/actions" target="_blank" rel="noopener">${icone("externo")}Execuções no GitHub</a>
      <button class="botao pequeno perigo" data-acao="sair">${icone("sair")}Desconectar</button></div>
    </div>`;
}

/* ---------------- Capas e vídeo ---------------- */
function carregarCapas() {
  const imgs = $$("img[data-asset]:not([src])");
  const obs = "IntersectionObserver" in window ? new IntersectionObserver((entradas) => {
    for (const e of entradas) if (e.isIntersecting) { obs.unobserve(e.target); mostrarCapa(e.target); }
  }, { rootMargin: "200px" }) : null;
  for (const img of imgs) obs ? obs.observe(img) : mostrarCapa(img);
}
async function mostrarCapa(img) {
  try { img.src = await urlMidia(img.dataset.asset); } catch { img.remove(); }
}

async function assistir(id) {
  const v = app.dados.videos.find((x) => x.id === id);
  if (!v) return;
  const p = previa(v);
  const modal = $("#modal");
  if (ehReels(v)) return assistirReels(v, p, modal);
  const titulo = v.titulo.length + 8 <= 100 && !/#shorts/i.test(v.titulo) ? `${v.titulo} #Shorts` : v.titulo;
  modal.innerHTML = `<div class="modal-caixa vidro">
    <button class="fechar" data-acao="fechar-modal" aria-label="Fechar">${icone("fechar")}</button>
    ${p.mp4 ? '<video controls playsinline preload="metadata"></video>' : '<div class="vazio">A prévia deste vídeo não está mais guardada.</div>'}
    <h3>${esc(v.titulo)}</h3>
    <div class="meta">${esc(STATUS[v.status] || v.status)} · ${esc(v.referencia || "")} · ${dataCurta(v.data)}</div>
    <div class="textos-copiar">
      <div class="copiar"><span>${esc(titulo)}</span><button class="botao pequeno" data-acao="copiar" data-texto="${esc(titulo)}">${icone("copiar")}</button></div>
      ${v.descricao ? `<div class="copiar"><span>${esc(v.descricao)}</span><button class="botao pequeno" data-acao="copiar" data-texto="${esc(v.descricao)}">${icone("copiar")}</button></div>` : ""}
    </div>
    <div class="linha-acoes">
      ${v.status === "aguardando" ? `<button class="botao principal" data-acao="aprovar" data-id="${v.id}">${icone("ok")}Aprovar</button>
        <button class="botao" data-acao="abrir-refazer" data-id="${v.id}">${icone("refazer")}Refazer</button>` : ""}
      ${v.status === "aprovado" ? `<button class="botao principal" data-acao="publicado" data-id="${v.id}">${icone("ok")}Já postei</button>` : ""}
      ${p.mp4 ? `<button class="botao" data-acao="baixar" data-id="${v.id}">${icone("baixar")}Baixar</button>` : ""}
    </div></div>`;
  modal.hidden = false;
  if (p.mp4) {
    try { $("video", modal).src = await urlMidia(p.mp4); } catch (erro) { avisar(erro.message, true); }
  }
}
async function assistirReels(v, p, modal) {
  const ativo = ["aguardando", "aprovado"].includes(v.status);
  modal.innerHTML = `<div class="modal-caixa vidro">
    <button class="fechar" data-acao="fechar-modal" aria-label="Fechar">${icone("fechar")}</button>
    ${p.mp4 ? '<video controls playsinline preload="metadata"></video>' : '<div class="vazio">A prévia deste Reels não está mais guardada.</div>'}
    <h3>${esc(v.marca || v.titulo)}</h3>
    <div class="meta">${esc(rotuloStatus(v))} · ${esc(v.segmento || "")} · ${dataCurta(v.data)}</div>
    ${v.legenda ? `<div class="legenda-caixa">${esc(v.legenda)}</div>` : ""}
    <div class="linha-acoes">
      ${p.mp4 ? `<button class="botao" data-acao="baixar" data-id="${v.id}">${icone("baixar")}Baixar</button>` : ""}
      ${v.legenda ? `<button class="botao" data-acao="copiar-legenda" data-id="${v.id}">${icone("copiar")}Copiar legenda</button>` : ""}
      ${ativo ? `<button class="botao principal" data-acao="publicado" data-id="${v.id}">${icone("ok")}Já postei</button>` : ""}
    </div></div>`;
  modal.hidden = false;
  if (p.mp4) {
    try { $("video", modal).src = await urlMidia(p.mp4); } catch (erro) { avisar(erro.message, true); }
  }
}
function fecharModal() { const m = $("#modal"); m.hidden = true; m.innerHTML = ""; }

async function baixar(id) {
  const v = app.dados.videos.find((x) => x.id === id);
  const p = v && previa(v);
  if (!p || !p.mp4) return avisar("A prévia deste vídeo não está mais guardada.", true);
  try {
    const url = await urlMidia(p.mp4);
    const nome = ehReels(v) ? `reels-${(v.marca || v.id).toLowerCase().normalize("NFD").replace(/[^a-z0-9]+/g, "-")}.mp4` : `${v.id}.mp4`;
    const a = Object.assign(document.createElement("a"), { href: url, download: nome, rel: "noopener" });
    document.body.append(a); a.click(); a.remove();
  } catch (erro) { avisar(erro.message, true); }
}

/* ---------------- Eventos ---------------- */
function irPara(pagina) {
  app.pagina = PAGINAS.includes(pagina) ? pagina : "fabrica";
  if (matchMedia("(max-width: 760px)").matches) recolher(true);
  desenhar();
  window.scrollTo({ top: 0 });
}

document.addEventListener("click", (ev) => {
  const alvo = ev.target.closest("[data-acao]");
  if (!alvo) return;
  const { acao, id } = alvo.dataset;
  const v = id && app.dados?.videos.find((x) => x.id === id);
  switch (acao) {
    case "aprovar": pedir("aprovar", { id }, alvo); fecharModal(); break;
    case "descartar": if (confirm(`Descartar “${v?.titulo}”?`)) pedir("descartar", { id }, alvo); break;
    case "publicado": pedir("publicado", { id }, alvo); fecharModal(); break;
    case "abrir-refazer":
      app.abertos.add(id); fecharModal();
      if (v && ehReels(v)) app.pagina = "instagram";
      else if (app.pagina !== "aprovacao") app.pagina = "aprovacao";
      desenhar(); setTimeout(() => $(`form[data-id="${id}"] textarea`)?.focus(), 50); break;
    case "fechar-refazer": app.abertos.delete(id); desenhar(); break;
    case "assistir": assistir(id); break;
    case "fechar-modal": fecharModal(); break;
    case "baixar": baixar(id); break;
    case "copiar": copiar(alvo.dataset.texto); break;
    case "copiar-titulo": copiar(v.titulo.length + 8 <= 100 ? `${v.titulo} #Shorts` : v.titulo); break;
    case "teste": pedir("teste", {}, alvo); break;
    case "segmento": app.segmento = app.segmento === alvo.dataset.segmento ? "" : alvo.dataset.segmento; desenhar(); break;
    case "reels-surpresa": app.segmento = ""; pedir("instagram", { tema: "", ajuste: $('form[data-form="instagram"] [name="ajuste"]')?.value.trim() || "" }, alvo); break;
    case "copiar-legenda": if (v && v.legenda) copiar(v.legenda); else avisar("Este Reels não tem legenda guardada.", true); break;
    case "produzir-historia": pedir("produzir", { tema: alvo.dataset.tema }, alvo); break;
    case "filtro": app.filtro = alvo.dataset.filtro; desenhar(); break;
    case "recarregar": carregar(); break;
    case "sair": if (confirm("Desconectar este aparelho da fábrica?")) desconectar(); break;
  }
});

document.addEventListener("submit", (ev) => {
  const form = ev.target.closest("form[data-form]");
  if (!form) return;
  ev.preventDefault();
  const botao = $("button[type=submit]", form);
  if (form.dataset.form === "produzir") pedir("produzir", { tema: form.tema.value.trim() }, botao);
  if (form.dataset.form === "instagram") {
    const tema = form.tema.value.trim() || app.segmento || "";
    pedir("instagram", { tema, ajuste: form.ajuste.value.trim() }, botao);
    app.segmento = "";
  }
  if (form.dataset.form === "chave") {
    const valor = form.valor.value.trim();
    if (!valor) return avisar("Cole a chave antes de salvar.", true);
    botao.disabled = true;
    api("/api/chaves", { method: "POST", body: { nome: form.dataset.nome, valor } })
      .then(() => { form.valor.value = ""; avisar("Chave guardada com segurança! A fábrica usa a partir da próxima execução."); carregar(); })
      .catch((erro) => { avisar(erro.message, true); botao.disabled = false; });
    return;
  }
  if (form.dataset.form === "refazer") {
    app.abertos.delete(form.dataset.id);
    pedir("refazer", { id: form.dataset.id, ajuste: form.ajuste.value.trim() }, botao);
  }
});

$("#modal").addEventListener("click", (ev) => { if (ev.target.id === "modal") fecharModal(); });
document.addEventListener("keydown", (ev) => {
  if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === "k") {
    ev.preventDefault(); recolher(false); $("#busca").focus();
  }
  if (ev.key === "Escape") { fecharModal(); if (matchMedia("(max-width: 760px)").matches) recolher(true); }
});

$("#recolher").addEventListener("click", () => recolher(!$("#app").classList.contains("recolhida")));

// Dica com o nome do item quando a barra está recolhida (fora do vidro, para não ser cortada)
const dica = Object.assign(document.createElement("div"), { className: "dica", hidden: true });
document.body.append(dica);
$("#barra").addEventListener("mouseover", (ev) => {
  const item = ev.target.closest(".item[data-dica]");
  if (!item || !$("#app").classList.contains("recolhida") || matchMedia("(hover: none)").matches) { dica.hidden = true; return; }
  const caixa = item.getBoundingClientRect();
  const extra = $(".contador", item)?.textContent;
  dica.innerHTML = esc(item.dataset.dica) + (extra ? `<i>${esc(extra)}</i>` : "");
  dica.style.left = `${caixa.right + 14}px`;
  dica.style.top = `${caixa.top + caixa.height / 2}px`;
  dica.hidden = false;
});
$("#barra").addEventListener("mouseleave", () => (dica.hidden = true));
$("#veu").addEventListener("click", () => recolher(true));
$("#caixa-busca").addEventListener("click", () => { if ($("#app").classList.contains("recolhida")) { recolher(false); setTimeout(() => $("#busca").focus(), 300); } });
$("#busca").addEventListener("input", (ev) => {
  app.busca = ev.target.value;
  if (!["videos", "historias"].includes(app.pagina)) app.pagina = "videos";
  desenhar();
});
$("#modo-noturno").addEventListener("change", (ev) => {
  const tema = ev.target.checked ? "escuro" : "claro";
  document.documentElement.dataset.tema = tema;
  memoria.gravar("clover.tema", tema);
  $$("img.logo").forEach((img) => (img.src = logo()));
  $('meta[name="theme-color"]').content = tema === "escuro" ? "#0b0a10" : "#f6f5fb";
  if (app.dados) desenhar();
});
window.addEventListener("hashchange", () => irPara(location.hash.slice(1)));
document.addEventListener("visibilitychange", () => { if (!document.hidden && app.token) carregar(); });

/* ---------------- Conectar / desconectar ---------------- */
function desconectar(mensagem) {
  memoria.apagar("clover.token");
  app.token = null; app.dados = null;
  clearTimeout(app.temporizador);
  $("#app").hidden = true;
  $("#tela-conectar").hidden = false;
  const erro = $("#erro-conectar");
  erro.hidden = !mensagem; erro.textContent = mensagem || "";
}

$("#form-conectar").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const chave = $("#campo-chave").value.trim();
  if (!chave) return;
  app.token = chave;
  const botao = $("button[type=submit]", ev.target);
  botao.disabled = true; botao.textContent = "Conectando…";
  try {
    app.dados = await api("/api/estado");
    memoria.gravar("clover.token", chave);
    $("#campo-chave").value = "";
    abrirPainel();
  } catch (erro) {
    app.token = null;
    $("#erro-conectar").hidden = false;
    $("#erro-conectar").textContent = erro.message;
  } finally {
    botao.disabled = false; botao.textContent = "Conectar";
  }
});

function abrirPainel() {
  $("#tela-conectar").hidden = true;
  $("#app").hidden = false;
  const celular = matchMedia("(max-width: 760px)").matches;
  recolher(celular || memoria.ler("clover.recolhida") === "1");
  app.pagina = PAGINAS.includes(location.hash.slice(1)) ? location.hash.slice(1) : "fabrica";
  if (app.dados) { app.estavaAtiva = !!app.dados.execucao.ativa; desenhar(); agendar(); }
  else carregar();
}

function iniciar() {
  for (const el of $$("[data-icone]")) el.outerHTML = icone(el.dataset.icone);
  $("#icone-busca").outerHTML = icone("busca");
  $("#recolher").innerHTML = icone("voltar");
  $("#link-chave").href = LINK_CHAVE;
  const tema = document.documentElement.dataset.tema || "escuro";
  $("#modo-noturno").checked = tema === "escuro";
  $$("img.logo").forEach((img) => (img.src = logo()));
  if (app.token) abrirPainel();
  else $("#tela-conectar").hidden = false;
}
iniciar();
