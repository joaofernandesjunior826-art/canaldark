// GET /api/midia?asset=<id> -> {url} temporário para assistir/baixar a prévia (vídeo ou capa).
import { REPO, gh, ErroGitHub, responder, responderErro, tokenDoPedido } from "./_github.js";

export default async function handler(req, res) {
  const token = tokenDoPedido(req);
  if (!token) return responder(res, 401, { erro: "Conecte a sua chave do GitHub." });
  const asset = String(req.query.asset || "");
  if (!/^\d{1,15}$/.test(asset)) return responder(res, 400, { erro: "Arquivo inválido." });
  try {
    const r = await gh(token, `/repos/${REPO}/releases/assets/${asset}`, {
      headers: { Accept: "application/octet-stream" },
      redirect: "manual",
    });
    const destino = r.headers.get("location");
    if (r.status >= 300 && r.status < 400 && destino) return responder(res, 200, { url: destino });
    throw new ErroGitHub(r.status === 200 ? 502 : r.status, await r.text());
  } catch (erro) {
    return responderErro(res, erro);
  }
}
