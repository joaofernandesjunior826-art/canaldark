// POST /api/chaves {nome, valor}  -> guarda (ou apaga, com valor vazio) uma chave no cofre.
// Quem chama é você, pelo painel, com a sua chave do GitHub. O valor nunca volta para o navegador.
import { REPO, gh, ErroGitHub, responder, responderErro, tokenDoPedido } from "./_github.js";
import { ARQUIVO, NOMES, cifrar } from "./_cofre.js";
// Os pedidos saem assinados como "Painel Clover" (sem o e-mail pessoal de quem usa o painel).
const PAINEL = { name: "Painel Clover", email: "painel-clover@users.noreply.github.com" };

async function lerCofre(token) {
  const r = await gh(token, `/repos/${REPO}/contents/${ARQUIVO}`);
  if (r.status === 404) return { sha: null, cofre: { versao: 1, chaves: {} } };
  if (!r.ok) throw new ErroGitHub(r.status, await r.text());
  const j = await r.json();
  return { sha: j.sha, cofre: JSON.parse(Buffer.from(j.content, "base64").toString("utf8")) };
}

export default async function handler(req, res) {
  if (req.method !== "POST") return responder(res, 405, { erro: "Use POST." });
  const token = tokenDoPedido(req);
  if (!token) return responder(res, 401, { erro: "Conecte a sua chave do GitHub." });
  const corpo = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  const nome = String(corpo.nome || "");
  const valor = String(corpo.valor || "").trim();
  if (!NOMES.includes(nome)) return responder(res, 400, { erro: "Chave desconhecida." });
  if (valor.length > 300 || /\s/.test(valor)) {
    return responder(res, 400, { erro: "A chave parece estar errada (tem espaços ou é grande demais). Copie de novo." });
  }
  try {
    for (let tentativa = 0; tentativa < 3; tentativa++) {
      const { sha, cofre } = await lerCofre(token);
      cofre.versao = 1;
      cofre.chaves = cofre.chaves || {};
      if (valor) cofre.chaves[nome] = { ...cifrar(valor), quando: new Date().toISOString() };
      else delete cofre.chaves[nome];
      const r = await gh(token, `/repos/${REPO}/contents/${ARQUIVO}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          committer: PAINEL, author: PAINEL,
        message: `Painel: chave ${nome} ${valor ? "guardada" : "removida"}`,
          content: Buffer.from(JSON.stringify(cofre, null, 2) + "\n").toString("base64"),
          ...(sha ? { sha } : {}),
        }),
      });
      if (r.ok) return responder(res, 200, { ok: true });
      if (r.status !== 409 && r.status !== 422) throw new ErroGitHub(r.status, await r.text());
    }
    return responder(res, 409, { erro: "O arquivo mudou enquanto salvava. Tente de novo." });
  } catch (erro) {
    if (/CHAVES_SEGREDO/.test(erro.message)) return responder(res, 500, { erro: erro.message });
    return responderErro(res, erro);
  }
}
