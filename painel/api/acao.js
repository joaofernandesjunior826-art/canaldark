// POST /api/acao {acao, id?, tema?, ajuste?}
// Grava o pedido como um arquivo em dados/pedidos/. Isso dispara a fábrica na hora (on: push),
// e nenhum pedido se perde mesmo se você apertar vários botões seguidos.
import { REPO, gh, ErroGitHub, responder, responderErro, tokenDoPedido } from "./_github.js";

const ACOES = new Set(["produzir", "teste", "aprovar", "refazer", "descartar", "publicado"]);
const PRECISA_ID = new Set(["aprovar", "refazer", "descartar", "publicado"]);

export default async function handler(req, res) {
  if (req.method !== "POST") return responder(res, 405, { erro: "Use POST." });
  const token = tokenDoPedido(req);
  if (!token) return responder(res, 401, { erro: "Conecte a sua chave do GitHub." });

  const corpo = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  const acao = String(corpo.acao || "");
  const id = String(corpo.id || "");
  if (!ACOES.has(acao)) return responder(res, 400, { erro: "Ação desconhecida." });
  if (PRECISA_ID.has(acao) && !/^\d{8}-\d{6}$/.test(id)) return responder(res, 400, { erro: "Vídeo inválido." });

  const pedido = {
    acao, id, tema: String(corpo.tema || "").slice(0, 200), ajuste: String(corpo.ajuste || "").slice(0, 500),
    quando: new Date().toISOString(), origem: "painel",
  };
  const nome = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}.json`;
  try {
    const r = await gh(token, `/repos/${REPO}/contents/dados/pedidos/${nome}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: `Painel: ${acao}${id ? " " + id : ""}`,
        content: Buffer.from(JSON.stringify(pedido, null, 2) + "\n").toString("base64"),
      }),
    });
    if (!r.ok) throw new ErroGitHub(r.status, await r.text());
    return responder(res, 200, { ok: true, pedido: nome });
  } catch (erro) {
    return responderErro(res, erro);
  }
}
