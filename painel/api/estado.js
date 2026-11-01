// GET /api/estado            -> tudo que o painel mostra
// GET /api/estado?leve=1     -> só a execução em andamento (para atualizar as estações ao vivo)
import { REPO, WORKFLOW, ghJson, lerArquivo, responder, responderErro, tokenDoPedido, gh } from "./_github.js";
import { NOMES } from "./_cofre.js";

const ATIVOS = new Set(["queued", "in_progress", "waiting", "requested", "pending"]);

async function execucoes(token) {
  const dados = await ghJson(token, `/repos/${REPO}/actions/workflows/${WORKFLOW}/runs?per_page=8`);
  const runs = (dados.workflow_runs || []).map((r) => ({
    id: r.id, status: r.status, conclusao: r.conclusion, evento: r.event, titulo: r.display_title || "",
    inicio: r.run_started_at || r.created_at, fim: r.updated_at, url: r.html_url,
  }));
  const ativa = runs.find((r) => ATIVOS.has(r.status)) || null;
  let etapas = [];
  if (ativa) {
    const jobs = await ghJson(token, `/repos/${REPO}/actions/runs/${ativa.id}/jobs`);
    const passos = (jobs.jobs && jobs.jobs[0] && jobs.jobs[0].steps) || [];
    etapas = passos
      .filter((p) => /^\d\s/.test(p.name) || p.name === "Pedidos" || p.name === "Preparar a fábrica")
      .map((p) => ({ nome: p.name, status: p.status, conclusao: p.conclusion }));
  }
  return { ativa, etapas, recentes: runs };
}

export default async function handler(req, res) {
  const token = tokenDoPedido(req);
  if (!token) return responder(res, 401, { erro: "Conecte a sua chave do GitHub." });
  try {
    const exec = await execucoes(token);
    if (req.query.leve === "1") return responder(res, 200, { execucao: exec });

    const [usuario, historicoTxt, estadoTxt, historiasTxt, pedidosResp, releaseResp, cofreTxt] = await Promise.all([
      ghJson(token, "/user").catch(() => null),
      lerArquivo(token, "dados/historico.json"),
      lerArquivo(token, "dados/estado.json"),
      lerArquivo(token, "dados/historias.txt"),
      gh(token, `/repos/${REPO}/contents/dados/pedidos`),
      gh(token, `/repos/${REPO}/releases/tags/previas`),
      lerArquivo(token, "dados/chaves.json"),
    ]);

    // Cofre de chaves: só os nomes e quando foram guardadas (os valores nunca saem daqui).
    const cofre = {};
    for (const nome of NOMES) if (process.env[`FABRICA_${nome}`]) cofre[nome] = { origem: "painel" };
    for (const [nome, item] of Object.entries((JSON.parse(cofreTxt || "{}").chaves) || {})) {
      cofre[nome] = { origem: "painel", quando: item.quando };
    }

    const videos = JSON.parse(historicoTxt || "[]").reverse();
    const estado = JSON.parse(estadoTxt || "{}");
    delete estado.clipes_usados;

    const pedidos = pedidosResp.ok
      ? (await pedidosResp.json()).filter((a) => a.name.endsWith(".json")).map((a) => a.name)
      : [];

    const previas = {};
    if (releaseResp.ok) {
      for (const a of (await releaseResp.json()).assets || []) {
        const [id, ext] = a.name.split(".");
        previas[id] = { ...(previas[id] || {}), [ext]: a.id };
      }
    }

    const historias = (historiasTxt || "").split("\n")
      .map((l) => l.trim()).filter((l) => l && !l.startsWith("#"))
      .map((l) => { const [titulo, ref] = l.split("|"); return { titulo: titulo.trim(), referencia: (ref || "").trim() }; });

    return responder(res, 200, {
      repo: REPO,
      usuario: usuario && { login: usuario.login, nome: usuario.name, avatar: usuario.avatar_url },
      videos, estado, pedidos, previas, historias, cofre, execucao: exec,
      agora: new Date().toISOString(),
    });
  } catch (erro) {
    return responderErro(res, erro);
  }
}
