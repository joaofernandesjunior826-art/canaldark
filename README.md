# Fábrica de Shorts: Histórias da Bíblia

Produz sozinha, todo dia, um YouTube Short contando uma história da Bíblia, **sem gastar nada**:

| Etapa | Ferramenta (grátis) |
|---|---|
| Escolha da história | Lista em `dados/historias.txt` (90 histórias, sem repetir) |
| Roteiro, título, descrição e tags | API do Gemini (plano gratuito) |
| Narração em português | edge-tts (vozes neurais da Microsoft) |
| Cenas | Vídeos verticais do Pexels (e Pixabay como reserva) |
| Montagem, legenda animada, música e capa | ffmpeg |
| Envio ao YouTube | API do YouTube, como **privado** |
| Aviso para você aprovar | Bot do Telegram (o vídeo chega no seu celular) |

Tudo roda nos servidores do GitHub (GitHub Actions) no horário marcado. Seu celular só serve para aprovar.

**Como você aprova:** o Short chega no Telegram com um link. Se gostou, abra o app YouTube Studio e mude de *Privado* para *Público* (ou *Programado*). Se não gostou, apague.

---

## Passo a passo (dá para fazer tudo pelo celular, no navegador)

### 1. Chave do Gemini (roteiro)
1. Acesse https://aistudio.google.com/apikey e entre com sua conta Google.
2. Toque em **Create API key** e copie a chave.

### 2. Chave do Pexels (cenas)
1. Crie conta em https://www.pexels.com/api/ e peça a chave (é imediato).
2. Opcional: crie também em https://pixabay.com/api/docs/ (reserva, caso o Pexels não ache algo).

### 3. Bot do Telegram (aviso no celular)
1. No Telegram, abra **@BotFather**, envie `/newbot`, escolha um nome. Ele te dá o **token**.
2. Abra o seu bot novo e envie qualquer mensagem (ex.: "oi").
3. No navegador, abra `https://api.telegram.org/bot<TOKEN>/getUpdates` (troque `<TOKEN>`).
   Procure `"chat":{"id":123456789` — esse número é o **chat id**.

### 4. Acesso ao YouTube (envio automático)
1. Em https://console.cloud.google.com crie um projeto (ex.: "fabrica-shorts").
2. Em **APIs e serviços > Biblioteca**, ative a **YouTube Data API v3**.
3. Em **Tela de consentimento OAuth** (ou "Google Auth Platform"): tipo **Externo**, preencha nome e e-mail.
   Em **Público-alvo**, adicione seu e-mail como usuário de teste e depois toque em **Publicar app**
   (status "Em produção"). *Sem publicar, a autorização expira a cada 7 dias.* Não precisa enviar para verificação.
4. Em **Credenciais > Criar credenciais > ID do cliente OAuth**, tipo **Aplicativo da Web**.
   Em *URIs de redirecionamento autorizados* coloque: `https://developers.google.com/oauthplayground`.
   Guarde o **Client ID** e o **Client secret**.
5. Abra https://developers.google.com/oauthplayground, toque na engrenagem ⚙️, marque
   **Use your own OAuth credentials** e cole o Client ID e o Client secret.
6. No campo de escopos (à esquerda), digite `https://www.googleapis.com/auth/youtube.upload`,
   toque em **Authorize APIs** e entre com a conta **do canal**. Vai aparecer "app não verificado":
   toque em *Avançado > Acessar* (o app é seu).
7. Toque em **Exchange authorization code for tokens** e copie o **Refresh token**.

> Enquanto a Google não auditar o projeto, todo vídeo enviado pela API fica **privado**. Isso já é a sua etapa de aprovação.

### 5. Cadastrar tudo no GitHub
No repositório: **Settings > Secrets and variables > Actions > New repository secret**. Crie:

| Nome | Valor |
|---|---|
| `GEMINI_API_KEY` | chave do passo 1 |
| `PEXELS_API_KEY` | chave do passo 2 |
| `PIXABAY_API_KEY` | (opcional) |
| `TELEGRAM_BOT_TOKEN` | token do BotFather |
| `TELEGRAM_CHAT_ID` | número do chat |
| `YT_CLIENT_ID` | do passo 4 |
| `YT_CLIENT_SECRET` | do passo 4 |
| `YT_REFRESH_TOKEN` | do passo 4 |

Só o Gemini é obrigatório para testar. Sem Pexels o fundo vira um degradê animado; sem YouTube o vídeo chega só no Telegram.

### 6. Testar
Aba **Actions > Fábrica de Shorts > Run workflow**. Em uns 3 a 5 minutos o Short chega no Telegram.
O vídeo também fica para download na própria execução (seção *Artifacts*).

Depois disso ele roda sozinho todo dia às 09:17 (Brasília). Para mudar o horário ou fazer 2 por dia,
edite o `cron` em `.github/workflows/fabrica.yml`.

---

## Ajustes opcionais
Em **Settings > Secrets and variables > Actions > Variables**:

| Variável | Padrão | O que faz |
|---|---|---|
| `DURACAO_ALVO_SEG` | `70` | Duração aproximada. Shorts aceitam até 180 s. |
| `VOZ` | `pt-BR-AntonioNeural` | Outras: `pt-BR-FranciscaNeural`, `pt-BR-ThalitaMultilingualNeural` |
| `VELOCIDADE_VOZ` | `+8%` | Ritmo da narração |
| `NOME_CANAL` | `Histórias da Bíblia` | Usado no roteiro |
| `YT_PRIVACIDADE` | `private` | `private`, `unlisted` ou `public` (só vale depois da auditoria da Google) |
| `GEMINI_MODELO` | `gemini-flash-latest,...` | Modelos tentados em ordem |
| `VOLUME_MUSICA` | `0.12` | Volume da música de fundo |

**Música de fundo:** coloque arquivos `.mp3` na pasta `musica/` (use músicas livres, como as da
Biblioteca de áudio do YouTube Studio). A cada vídeo uma é sorteada. Sem música, vai só a narração.

**Histórias:** edite `dados/historias.txt`. O que já virou vídeo fica em `dados/historico.json`.

## Rodar no computador ou no Termux
```bash
pip install -r requirements.txt     # e tenha o ffmpeg instalado
export GEMINI_API_KEY=...  PEXELS_API_KEY=...
python -m fabrica --sem-enviar                       # só gera em saida/
python -m fabrica --historia "Davi e Golias"         # história específica
```

## Sobre monetização (importante)
- Shorts entram no Programa de Parcerias com **1.000 inscritos + 10 milhões de visualizações de Shorts em 90 dias**
  (ou 4.000 horas de vídeos longos). A duração do Short não muda isso: ele é pago pela divisão de receita
  do feed de Shorts, seja de 30 s ou de 3 min.
- O YouTube não monetiza conteúdo **repetitivo ou produzido em massa**. Revise cada vídeo, varie as
  histórias e, se puder, troque às vezes a voz, as músicas e o estilo.
- Os vídeos são enviados marcados como **conteúdo sintético** (voz de IA), como o YouTube exige.
- Pexels e Pixabay permitem uso comercial sem atribuição.

## Custos
Zero, dentro dos limites gratuitos: Gemini (limite diário de pedidos), Pexels (200 buscas/hora),
GitHub Actions (ilimitado em repositório público; 2.000 min/mês em privado, e cada Short usa ~4 min),
YouTube API (10.000 unidades/dia; cada envio usa ~1.600, ou seja, até 6 por dia).
