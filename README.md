# Clover · Fábrica de Shorts (Histórias da Bíblia)

Uma fábrica que faz sozinha, todo dia, um YouTube Short contando uma história da Bíblia, e um
**painel** com a marca Clover onde você acompanha a produção ao vivo e aprova cada vídeo.
Tudo grátis: a fábrica roda nos servidores do GitHub e o painel na Vercel.

**Painel:** https://clover-fabrica.vercel.app

## As 8 estações

| # | Estação | O que faz (grátis) |
|---|---|---|
| 1 | Pauta | Escolhe a próxima história de `dados/historias.txt` (90 histórias, sem repetir) |
| 2 | Roteiro | Gemini escreve o texto, o título, a descrição e as hashtags |
| 3 | Narração | Voz neural em português (edge-tts) |
| 4 | Cenas | Pinturas clássicas da própria história (Wikimedia, domínio público) com movimento lento, misturadas com vídeos de paisagem do Pixabay ou Pexels |
| 5 | Montagem | Junta as cenas e a narração (ffmpeg) |
| 6 | Shorts | Legenda animada, frase de impacto, música ambiente, 9:16 |
| 7 | Thumbnail | Capa do vídeo |
| 8 | Agenda | Coloca o vídeo na fila de aprovação e avisa você |

Cada estação é um passo separado no GitHub Actions, por isso o painel mostra ao vivo em qual
estação o vídeo está.

## O painel

- **Fábrica:** as 8 estações ao vivo, números do canal, botão "Fazer um vídeo agora" (com tema
  opcional) e a atividade recente.
- **Aprovação:** os vídeos esperando você. Assista, **Aprove**, **Refaça** (pode escrever o que mudar,
  ex.: "mais curto", "comece pela batalha") ou **Descarte**.
- **Agenda:** os aprovados prontos para postar (baixar, copiar título, "Já postei"), os programados
  e os publicados.
- **Vídeos**, **Histórias** (faça qualquer história da lista na hora) e **Configurações** (o que
  já está pronto e o que falta).
- Barra lateral de vidro que recolhe, busca, modo noturno, funciona no celular e no computador.

Cada botão do painel vira um pedido em `dados/pedidos/`, que faz a fábrica rodar na hora.

## Por que você posta (por enquanto)

O YouTube **trava como privado, sem direito a recurso,** todo vídeo enviado pela API por um projeto
que ainda não passou pela auditoria da Google
([ajuda do YouTube](https://support.google.com/youtube/answer/7300965)). Então, depois de aprovar,
você baixa o vídeo pelo painel e posta pelo app do YouTube (1 minuto). Isso também é a revisão
humana que o YouTube exige para monetizar. Se a auditoria for aprovada, ligue o envio automático
(veja no fim): aí aprovar já programa o vídeo no YouTube.

---

## Instalação (dá para fazer tudo pelo celular)

### 1. Chave do Gemini (roteiro)
Em https://aistudio.google.com/apikey, entre com sua conta Google e toque em **Create API key**.

### 2. Chave do Pixabay (paisagens, opcional)
Sem ela os vídeos já saem com pinturas clássicas da história. Com ela, a fábrica mistura paisagens.
O Pexels pausou a emissão de novas chaves; use o Pixabay:
1. Crie uma conta grátis em https://pixabay.com (ou entre com o Google).
2. Abra https://pixabay.com/api/docs/ já logado: a sua chave aparece em verde na parte
   **Parameters › key** ("Your API key"). Copie.

### 3. Cadastrar no GitHub
No repositório: **Settings › Secrets and variables › Actions › New repository secret**:

| Nome | Valor |
|---|---|
| `GEMINI_API_KEY` | chave do passo 1 |
| `PIXABAY_API_KEY` | chave do passo 2 (opcional) |
| `PEXELS_API_KEY` | (opcional, se você já tiver uma chave do Pexels) |
| `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` | (opcional, avisos no celular; veja abaixo) |

### 4. Conectar o painel
Abra https://clover-fabrica.vercel.app e siga a tela **Conectar a fábrica**: ela abre o GitHub para
criar uma chave só para o painel. Na página do GitHub:
1. Em **Repository access**, escolha **Only select repositories › canaldark**.
2. Em **Permissions**, deixe **Actions** e **Contents** com **Read and write**.
3. Toque em **Generate token**, copie e cole no painel.

A chave fica salva só no seu aparelho. Para tirar: **Configurações › Desconectar**.

### 5. Primeiro vídeo
No painel: **Fábrica › Produzir**. Em uns 3 minutos o vídeo aparece em **Aprovação**.
A partir daí é automático: um vídeo novo todo dia às 9h (horário de Brasília).

> Já existe um vídeo **[TESTE]** na fila de aprovação, feito pela fábrica sem nenhuma chave, para
> você ver o painel funcionando. Pode descartar.

### Telegram (opcional)
1. No Telegram, abra o **@BotFather**, mande `/newbot` e escolha um nome. Guarde o **token**.
2. Abra o seu bot e mande `/start`.
3. No navegador, abra `https://api.telegram.org/bot<TOKEN>/getUpdates` e copie o número depois de
   `"chat":{"id":`: é o **chat id**.
4. Cadastre `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` nos Secrets.

O bot manda cada vídeo novo com os botões **Aprovar**, **Refazer** e **Abrir o painel**, e aceita
`/novo`, `/refazer`, `/status` e respostas ao vídeo com o que mudar (confere de hora em hora).

---

## Ajustes (opcionais)
Em **Settings › Secrets and variables › Actions › Variables**:

| Variável | Padrão | O que faz |
|---|---|---|
| `HORARIOS` | `9` | Hora(s) de Brasília do vídeo do dia. `9,18` = dois por dia. |
| `DURACAO_ALVO_SEG` | `60` | Duração do Short (máximo 170). |
| `VOZ` | `pt-BR-AntonioNeural` | Também: `pt-BR-FranciscaNeural`, `pt-BR-ThalitaMultilingualNeural`. |
| `VELOCIDADE_VOZ` | `+8%` | Ritmo da narração. |
| `VOLUME_MUSICA` | `0.15` | Volume da música; `0` tira a música. |
| `NOME_CANAL` | `Histórias da Bíblia` | Usado no roteiro. |
| `GEMINI_MODELO` | `gemini-3.8-flash,gemini-flash-latest,gemini-3.5-flash-lite` | Modelos tentados em ordem. |
| `PAINEL_URL` | `https://clover-fabrica.vercel.app` | Link do painel nos avisos do Telegram. |

- **Histórias:** edite `dados/historias.txt` (uma por linha: `título | referência`).
- **Música:** sem nada, a fábrica gera uma trilha ambiente na hora (sem direitos autorais). Para usar
  as suas, coloque `.mp3` em `musica/` (ex.: da Biblioteca de áudio do YouTube, sem atribuição).

## Limites e custos
- **GitHub Actions:** repositório privado tem 2.000 minutos/mês. A conferência de hora em hora usa
  ~500 por mês, cada vídeo ~3 minutos e cada botão do painel ~1 minuto.
- **Vercel:** plano Hobby, grátis.
- **Gemini / Pexels / Telegram:** bem dentro dos limites gratuitos.

## Monetização
- Shorts entram no Programa de Parcerias com **1.000 inscritos + 10 milhões de visualizações de
  Shorts em 90 dias** (ou 4.000 horas em vídeos longos). O tamanho do Short não muda isso.
- O YouTube não monetiza conteúdo repetitivo ou feito em massa: revise, peça ajustes e varie.
- Ao postar, marque **Conteúdo alterado ou sintético: Sim** (a narração é de IA). Segundo o YouTube,
  isso não afeta a monetização.

## Se algo der errado
A estação que falhou fica vermelha no painel, o Telegram avisa e a fábrica tenta de novo na hora
seguinte (até 3 vezes por dia). O registro completo fica em **Actions** no GitHub. Para testar a
montagem sem chaves: painel › Fábrica › **Fazer vídeo de teste**.

## Envio automático ao YouTube (só depois da auditoria)
1. Peça a auditoria no [formulário da API do YouTube](https://support.google.com/youtube/contact/yt_api_form).
2. Em https://console.cloud.google.com crie um projeto, ative a **YouTube Data API v3**, configure a
   tela de consentimento como **Externo** e toque em **Publicar app**.
3. Crie um **ID do cliente OAuth › Aplicativo da Web** com o redirecionamento
   `https://developers.google.com/oauthplayground`.
4. No [OAuth Playground](https://developers.google.com/oauthplayground), use suas credenciais (⚙️),
   autorize `https://www.googleapis.com/auth/youtube.upload` com a conta do canal e pegue o
   **refresh token** (ou rode `scripts/obter_token_youtube.py` num computador).
5. Secrets `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`; variáveis `YT_ENVIO_AUTOMATICO` = `sim`
   e `YT_HORARIO` = `18:00` (ou `12:00,18:00`).

Com isso, **aprovar no painel já programa o vídeo no próximo horário livre**.

## Estrutura
- `fabrica/`: o motor (estações em `etapas.py`, ações em `acoes.py`, Gemini, voz, cenas, montagem).
- `painel/`: o site (HTML/CSS/JS sem dependências) e a API em `painel/api/` (funções da Vercel).
- `.github/workflows/fabrica.yml`: agenda de hora em hora, pedidos do painel e os 8 passos.
- `dados/`: histórias, histórico, fila e pedidos.
