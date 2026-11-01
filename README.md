# Fábrica de Shorts: Histórias da Bíblia

Todo dia ela faz sozinha um YouTube Short contando uma história da Bíblia e manda para o seu
**Telegram**. Você assiste: se gostar, posta no YouTube em 1 minuto; se não gostar, pede para refazer.
Tudo de graça, rodando nos servidores do GitHub. Seu celular pode até estar desligado na hora.

| Etapa | Como é feito (grátis) |
|---|---|
| História do dia | Lista de 90 histórias em `dados/historias.txt`, sem repetir |
| Roteiro, título, descrição | API do Gemini (plano gratuito) |
| Narração | edge-tts (vozes neurais da Microsoft em português) |
| Cenas | Vídeos verticais do Pexels (Pixabay como reserva) |
| Montagem | ffmpeg: legenda animada, frase de impacto no começo, música ambiente |
| Entrega e aprovação | Bot do Telegram |

## Por que você posta (e não o robô)

O YouTube **trava como privado, sem direito a recurso,** todo vídeo enviado pela API por um projeto
que ainda não passou pela auditoria da Google
([ajuda do YouTube](https://support.google.com/youtube/answer/7300965)). Ou seja: mandar direto para o
canal agora geraria vídeos que nunca poderiam ser públicos. Por isso o Short chega no seu Telegram
pronto, com título e descrição para copiar, e você posta pelo app do YouTube.

Isso também é a sua revisão: o YouTube não paga por conteúdo feito em massa sem cuidado humano.
Se um dia a Google aprovar a auditoria do seu projeto, dá para ligar o envio automático (veja no fim).

## Seu dia a dia

1. Por volta das 9h chega no Telegram o vídeo do dia com dois recados:
   - **Gostou?** Abra o vídeo, toque em ⋮ › *Salvar na galeria*. No app do YouTube: **+** › *Enviar um vídeo* ›
     escolha o vídeo › cole o título (toque no texto do Telegram para copiar) › *Publicar* ou *Programar*.
   - **Não gostou?** Toque em **🔄 Refazer** ou **responda ao vídeo** dizendo o que mudar
     (ex.: "mais curto", "comece pela batalha"). A nova versão chega na hora seguinte.
2. Comandos que você pode mandar para o bot a qualquer hora:
   - `/novo` faz um vídeo extra com a próxima história da lista
   - `/novo Sansão e Dalila` faz um vídeo extra sobre o tema que você escrever
   - `/refazer` ou `/refazer com mais suspense` refaz o último vídeo
   - `/status` mostra a fila e o último vídeo

A fábrica confere o Telegram de hora em hora, das 7h às 23h.

---

## Instalação (uns 15 minutos, dá para fazer tudo pelo navegador do celular)

### 1. Chave do Gemini (roteiro)
Entre em https://aistudio.google.com/apikey com sua conta Google e toque em **Create API key**. Copie a chave.

### 2. Chave do Pexels (cenas)
Crie uma conta em https://www.pexels.com/api/ e peça a chave (sai na hora).
Opcional: crie também em https://pixabay.com/api/docs/ (reserva, se o Pexels não achar algo).

### 3. Bot do Telegram (entrega)
1. No Telegram, abra o **@BotFather**, mande `/newbot` e escolha um nome. Ele te dá o **token**.
2. Abra o seu bot novo e mande `/start`.
3. No navegador, abra `https://api.telegram.org/bot<TOKEN>/getUpdates` (troque `<TOKEN>` pelo token).
   Procure `"chat":{"id":` e copie o número que vem depois: é o **chat id**.

### 4. Cadastrar no GitHub
No repositório: **Settings › Secrets and variables › Actions › New repository secret**. Crie:

| Nome | Valor |
|---|---|
| `GEMINI_API_KEY` | chave do passo 1 |
| `PEXELS_API_KEY` | chave do passo 2 |
| `PIXABAY_API_KEY` | (opcional) |
| `TELEGRAM_BOT_TOKEN` | token do passo 3 |
| `TELEGRAM_CHAT_ID` | número do passo 3 |

### 5. Primeiro vídeo
Aba **Actions › Fábrica de Shorts › Run workflow › Run workflow**. Em uns 5 minutos o vídeo chega
no Telegram. Pronto: a partir daí é automático.

> Para pausar: **Actions › Fábrica de Shorts › ⋯ › Disable workflow**.

---

## Ajustes (opcionais)
Em **Settings › Secrets and variables › Actions › aba Variables**:

| Variável | Padrão | O que faz |
|---|---|---|
| `HORARIOS` | `9` | Hora(s) de Brasília do vídeo do dia. `9,18` = dois por dia. |
| `DURACAO_ALVO_SEG` | `60` | Duração aproximada do Short (máximo 180). |
| `VOZ` | `pt-BR-AntonioNeural` | Também: `pt-BR-FranciscaNeural`, `pt-BR-ThalitaMultilingualNeural`. |
| `VELOCIDADE_VOZ` | `+8%` | Ritmo da narração. |
| `VOLUME_MUSICA` | `0.15` | Volume da música; `0` tira a música. |
| `NOME_CANAL` | `Histórias da Bíblia` | Usado no roteiro. |
| `GEMINI_MODELO` | `gemini-3.8-flash,gemini-flash-latest,gemini-3.5-flash-lite` | Modelos tentados em ordem. |

- **Histórias:** edite `dados/historias.txt` (uma por linha: `título | referência`). O que já virou
  vídeo fica em `dados/historico.json`. Quando a lista acaba, ela recomeça com roteiros novos.
- **Música:** sem nada, a fábrica gera uma trilha ambiente na hora (acordes suaves, sem direitos
  autorais). Para usar músicas suas, coloque arquivos `.mp3` na pasta `musica/`; a cada vídeo uma é
  sorteada. Use músicas liberadas, como as da Biblioteca de áudio do YouTube Studio que não pedem atribuição.

## Limites e custos
Tudo dentro dos planos gratuitos:
- **GitHub Actions:** repositório privado tem 2.000 minutos por mês. A conferência de hora em hora usa
  cerca de 1 minuto cada (~500 por mês) e cada vídeo uns 5 minutos (~150 por mês com 1 vídeo por dia).
- **Gemini:** um pedido por vídeo, bem abaixo do limite diário gratuito.
- **Pexels:** 200 buscas por hora; cada vídeo usa umas 12.
- **Telegram:** vídeos de até 50 MB (a fábrica já limita o tamanho).

## Sobre monetização
- Shorts entram no Programa de Parcerias com **1.000 inscritos + 10 milhões de visualizações de Shorts
  em 90 dias** (ou 4.000 horas de exibição em vídeos longos). O valor vem da divisão de receita do feed de
  Shorts, então o tamanho do Short não muda nada: 60 s costuma segurar melhor a audiência do que 3 min.
- O YouTube não monetiza conteúdo repetitivo ou produzido em massa. Revise cada vídeo, peça ajustes,
  varie temas, e de vez em quando troque a voz ou as músicas.
- Ao postar, marque **Conteúdo alterado ou sintético: Sim**, porque a narração é feita por IA.
  Segundo o YouTube, isso não afeta a monetização.
- Pexels e Pixabay permitem uso comercial sem atribuição.

## Se algo der errado
O bot avisa no Telegram com o motivo e tenta de novo na hora seguinte (até 3 vezes por dia).
Os detalhes ficam em **Actions** (cada execução tem o registro completo), e os vídeos ficam 7 dias
em *Artifacts* de cada execução.

## Rodar no computador (opcional)
```bash
pip install -r requirements.txt   # e instale o ffmpeg
export GEMINI_API_KEY=...  PEXELS_API_KEY=...
python -m fabrica teste --tema "Davi e Golias"   # o vídeo sai em saida/
```

---

## Envio automático ao YouTube (opcional, só depois da auditoria)
Só ligue isto se a Google aprovar a auditoria do seu projeto
([formulário de auditoria da API do YouTube](https://support.google.com/youtube/contact/yt_api_form)).
Antes disso, os vídeos enviados ficam travados como privados.

1. Em https://console.cloud.google.com crie um projeto e ative a **YouTube Data API v3**.
2. Configure a tela de consentimento OAuth como **Externo** e toque em **Publicar app**
   (sem isso, a autorização expira em 7 dias).
3. Crie uma credencial **ID do cliente OAuth › Aplicativo da Web** com o redirecionamento
   `https://developers.google.com/oauthplayground`.
4. Em https://developers.google.com/oauthplayground, na engrenagem ⚙️ marque *Use your own OAuth
   credentials*, autorize o escopo `https://www.googleapis.com/auth/youtube.upload` com a conta do canal e
   troque o código pelo **refresh token** (ou rode `scripts/obter_token_youtube.py` num computador).
5. Crie os secrets `YT_CLIENT_ID`, `YT_CLIENT_SECRET` e `YT_REFRESH_TOKEN`, e as variáveis
   `YT_ENVIO_AUTOMATICO` = `sim` e, se quiser agendar, `YT_HORARIO` = `18:00`.

Com isso, cada vídeo vai direto para o canal (agendado no próximo `YT_HORARIO`) e o Telegram só avisa.
