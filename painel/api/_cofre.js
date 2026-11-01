// Cofre das chaves da fábrica. As chaves coladas no painel ficam em dados/chaves.json
// criptografadas (AES-256-GCM) com um segredo que só existe aqui na Vercel (CHAVES_SEGREDO).
// Só a própria fábrica, rodando no GitHub Actions deste repositório, consegue abri-las:
// ela se identifica com um token OIDC assinado pelo GitHub.
import crypto from "node:crypto";
import { REPO } from "./_github.js";

export const NOMES = ["GEMINI_API_KEY", "PIXABAY_API_KEY", "PEXELS_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"];
export const ARQUIVO = "dados/chaves.json";
export const AUDIENCIA = "clover-fabrica";
const EMISSOR = "https://token.actions.githubusercontent.com";

function chaveAes() {
  const segredo = process.env.CHAVES_SEGREDO || "";
  if (segredo.length < 32) throw new Error("O cofre do painel não está configurado (CHAVES_SEGREDO).");
  return crypto.createHash("sha256").update(segredo).digest();
}

export function cifrar(texto) {
  const iv = crypto.randomBytes(12);
  const c = crypto.createCipheriv("aes-256-gcm", chaveAes(), iv);
  const dado = Buffer.concat([c.update(texto, "utf8"), c.final()]);
  return { iv: iv.toString("base64"), tag: c.getAuthTag().toString("base64"), dado: dado.toString("base64") };
}

export function decifrar(item) {
  const d = crypto.createDecipheriv("aes-256-gcm", chaveAes(), Buffer.from(item.iv, "base64"));
  d.setAuthTag(Buffer.from(item.tag, "base64"));
  return Buffer.concat([d.update(Buffer.from(item.dado, "base64")), d.final()]).toString("utf8");
}

let jwks = null;
export async function verificarOidc(jwt) {
  const partes = String(jwt || "").split(".");
  if (partes.length !== 3) throw new Error("token inválido");
  const [h, p, s] = partes;
  const cabecalho = JSON.parse(Buffer.from(h, "base64url").toString("utf8"));
  const corpo = JSON.parse(Buffer.from(p, "base64url").toString("utf8"));
  if (cabecalho.alg !== "RS256") throw new Error("algoritmo inválido");
  if (!jwks || !jwks.keys.some((k) => k.kid === cabecalho.kid)) {
    jwks = await (await fetch(`${EMISSOR}/.well-known/jwks`)).json();
  }
  const jwk = (jwks.keys || []).find((k) => k.kid === cabecalho.kid);
  if (!jwk) throw new Error("assinatura desconhecida");
  const valido = crypto.verify("RSA-SHA256", Buffer.from(`${h}.${p}`),
    crypto.createPublicKey({ key: jwk, format: "jwk" }), Buffer.from(s, "base64url"));
  if (!valido) throw new Error("assinatura inválida");
  const agora = Math.floor(Date.now() / 1000);
  if (corpo.iss !== EMISSOR || corpo.aud !== AUDIENCIA || corpo.repository !== REPO ||
      !(corpo.exp > agora) || (corpo.nbf && corpo.nbf > agora + 60)) {
    throw new Error("o token não é desta fábrica");
  }
  return corpo;
}
