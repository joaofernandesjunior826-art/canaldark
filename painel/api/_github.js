// Funções comuns da API do painel. A chave do GitHub vem do celular de quem usa o painel
// (cabeçalho Authorization) e nunca é guardada aqui.
export const REPO = process.env.GITHUB_REPO || "joaofernandesjunior826-art/canaldark";
export const WORKFLOW = "fabrica.yml";
const API = "https://api.github.com";

export class ErroGitHub extends Error {
  constructor(status, corpo) {
    super(`GitHub respondeu ${status}`);
    this.status = status;
    this.corpo = corpo;
  }
}

export function tokenDoPedido(req) {
  const m = String(req.headers.authorization || "").match(/^Bearer\s+([\w-]{20,255})$/i);
  return m ? m[1] : null;
}

export async function gh(token, caminho, opcoes = {}) {
  return fetch(API + caminho, {
    method: opcoes.method || "GET",
    body: opcoes.body,
    redirect: opcoes.redirect || "follow",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "clover-fabrica-painel",
      ...(opcoes.headers || {}),
    },
  });
}

export async function ghJson(token, caminho, opcoes) {
  const r = await gh(token, caminho, opcoes);
  if (!r.ok) throw new ErroGitHub(r.status, await r.text());
  return r.json();
}

// Lê um arquivo do repositório como texto. Devolve null se ele não existir.
export async function lerArquivo(token, caminho) {
  const r = await gh(token, `/repos/${REPO}/contents/${caminho}`, {
    headers: { Accept: "application/vnd.github.raw+json" },
  });
  if (r.status === 404) return null;
  if (!r.ok) throw new ErroGitHub(r.status, await r.text());
  return r.text();
}

export function responder(res, status, dados) {
  res.setHeader("Cache-Control", "no-store");
  res.status(status).json(dados);
}

// Transforma erros do GitHub em mensagens que qualquer pessoa entende.
export function responderErro(res, erro) {
  if (erro instanceof ErroGitHub) {
    const mensagens = {
      401: "A chave do GitHub é inválida ou venceu. Crie uma nova e conecte de novo.",
      403: "A chave não tem permissão. Ela precisa de Actions (leitura e escrita) e Contents (leitura e escrita).",
      404: "A chave não tem acesso ao repositório da fábrica. Ao criar a chave, escolha o repositório canaldark.",
    };
    const limite = erro.status === 403 && /rate limit/i.test(erro.corpo || "");
    return responder(res, erro.status === 401 ? 401 : erro.status === 404 ? 404 : 403, {
      erro: limite ? "Muitas consultas ao GitHub em pouco tempo. Espere alguns minutos." :
        mensagens[erro.status] || `O GitHub respondeu com erro ${erro.status}.`,
    });
  }
  console.error(erro);
  return responder(res, 500, { erro: "Algo deu errado no painel. Tente de novo em instantes." });
}
