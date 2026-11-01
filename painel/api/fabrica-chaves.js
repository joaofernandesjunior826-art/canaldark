// POST /api/fabrica-chaves  (só para a fábrica no GitHub Actions)
// Recebe o conteúdo de dados/chaves.json e devolve as chaves abertas, mas só se o pedido vier
// com um token OIDC do GitHub Actions deste repositório.
import { responder } from "./_github.js";
import { NOMES, decifrar, verificarOidc } from "./_cofre.js";

export default async function handler(req, res) {
  if (req.method !== "POST") return responder(res, 405, { erro: "Use POST." });
  try {
    await verificarOidc(String(req.headers.authorization || "").replace(/^Bearer\s+/i, ""));
  } catch (erro) {
    return responder(res, 401, { erro: `Acesso negado: ${erro.message}` });
  }
  const corpo = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  const chaves = {};
  const falhas = [];
  // Primeiro as chaves guardadas na Vercel; as coladas no painel (mais recentes) têm prioridade.
  for (const nome of NOMES) {
    if (process.env[`FABRICA_${nome}`]) chaves[nome] = process.env[`FABRICA_${nome}`];
  }
  for (const [nome, item] of Object.entries(corpo.chaves || {})) {
    if (!/^[A-Z][A-Z0-9_]{2,40}$/.test(nome)) continue;
    try {
      chaves[nome] = decifrar(item);
    } catch {
      falhas.push(nome);
    }
  }
  return responder(res, 200, { chaves, falhas });
}
