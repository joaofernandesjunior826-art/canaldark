"""Etapa 4: monta o Short (1080x1920) com ffmpeg: cenas, narração, legenda, música e capa."""
import json
import math
import random
import subprocess
from pathlib import Path

from . import config

W, H, FPS = config.LARGURA, config.ALTURA, config.FPS
PAUSA = 0.25          # respiro entre cenas, em segundos
LIMITE_MB = 45        # o Telegram aceita vídeos de bot até 50 MB


def ff(*args, cwd: Path | None = None) -> None:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou:\n{r.stderr[-1500:]}")


def duracao(arq: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(arq)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


# ---- Cenas ------------------------------------------------------------------
def clipe_da_cena(origem: Path | None, dur: float, destino: Path) -> None:
    """Ajusta o vídeo da cena para o formato vertical, no tempo exato da narração."""
    filtro = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"fps={FPS},setsar=1,eq=brightness=-0.05:saturation=0.92,format=yuv420p")
    if origem:
        fonte = duracao(origem)
        if fonte >= dur + 0.5:  # sobra vídeo: começa num ponto sorteado
            entrada = ["-ss", f"{random.uniform(0, min(4.0, fonte - dur - 0.3)):.2f}", "-i", origem]
        elif fonte > 0 and fonte * 2.2 >= dur:  # um pouco curto: câmera lenta para cobrir a cena
            entrada = ["-i", origem]
            filtro = f"setpts={dur / fonte * 1.02:.4f}*PTS," + filtro
        else:
            entrada = ["-stream_loop", "-1", "-i", origem]
    else:  # sem vídeo: fundo em movimento em tons de pergaminho e noite
        c0, c1 = random.choice([("0x1b1209", "0x5a3a12"), ("0x0b0f1d", "0x3a2a52"),
                                ("0x120a05", "0x6b4a1f")])
        entrada = ["-f", "lavfi", "-i", f"gradients=s={W}x{H}:c0={c0}:c1={c1}:speed=0.01:r={FPS}"]
    ff(*entrada, "-t", f"{dur:.3f}", "-vf", filtro, "-an", "-c:v", "libx264",
       "-preset", "veryfast", "-crf", "20", "-r", FPS, destino)


# ---- Legenda ----------------------------------------------------------------
def _limpar_ass(texto: str) -> str:
    return texto.replace("{", "(").replace("}", ")").replace("\\", "/").replace("\n", " ")


def _tempo_ass(seg: float) -> str:
    h, resto = divmod(max(seg, 0), 3600)
    m, s = divmod(resto, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _blocos(palavras: list[dict]) -> list[list[dict]]:
    """Agrupa até 3 palavras (ou ~15 letras), quebrando também nas pausas da fala."""
    blocos, atual = [], []
    for i, p in enumerate(palavras):
        if atual and (len(atual) == 3 or len(" ".join(w["texto"] for w in atual + [p])) > 15):
            blocos.append(atual)
            atual = []
        atual.append(p)
        prox = palavras[i + 1] if i + 1 < len(palavras) else None
        if prox is None or prox["ini"] - p["fim"] > 0.18:
            blocos.append(atual)
            atual = []
    return blocos


def legenda_ass(palavras: list[dict], chamada: str, destino: Path) -> None:
    """Legenda estilo Shorts (palavra falada em dourado) + frase de impacto no topo no começo."""
    cabecalho = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,DejaVu Sans,80,&H00FFFFFF,&H0000D7FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,2,100,100,560,1
Style: Topo,DejaVu Sans,74,&H0000D7FF,&H0000D7FF,&H60000000,&H00000000,-1,0,0,0,100,100,0,0,3,22,0,8,100,100,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    linhas = []
    if chamada:
        linhas.append(f"Dialogue: 1,{_tempo_ass(0)},{_tempo_ass(3.2)},Topo,,0,0,0,,"
                      f"{{\\fad(150,400)}}{_limpar_ass(chamada.upper())}")
    blocos = _blocos(palavras)
    for i, bloco in enumerate(blocos):
        fim_bloco = bloco[-1]["fim"] + 0.35
        if i + 1 < len(blocos):
            fim_bloco = min(fim_bloco, blocos[i + 1][0]["ini"])
        textos = [_limpar_ass(p["texto"].upper()) for p in bloco]
        for j, p in enumerate(bloco):
            fim = bloco[j + 1]["ini"] if j + 1 < len(bloco) else fim_bloco
            texto = " ".join("{\\c&H0000D7FF&}" + t + "{\\c&H00FFFFFF&}" if k == j else t
                             for k, t in enumerate(textos))
            pulo = "{\\fscx110\\fscy110\\t(0,90,\\fscx100\\fscy100)}" if j == 0 else ""
            linhas.append(f"Dialogue: 0,{_tempo_ass(p['ini'])},{_tempo_ass(fim)},Base,,0,0,0,,{pulo}{texto}")
    destino.write_text(cabecalho + "\n".join(linhas) + "\n", encoding="utf-8")


# ---- Áudio ------------------------------------------------------------------
def normalizar(entrada: Path, saida: Path, alvo_lufs: float, filtros_depois: str = "") -> None:
    """Deixa o volume no padrão (duas passadas do loudnorm), para todo vídeo soar igual."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(entrada), "-af",
                        f"loudnorm=I={alvo_lufs}:TP=-2:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    filtro = "anull"
    try:
        m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
        if float(m["input_i"]) > -70:
            filtro = (f"loudnorm=I={alvo_lufs}:TP=-2:LRA=11:measured_I={m['input_i']}:"
                      f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
                      f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    except (ValueError, KeyError):
        print("Aviso: não consegui medir o volume; seguindo sem normalizar.")
    if filtros_depois:
        filtro += "," + filtros_depois
    ff("-i", entrada, "-af", filtro + ",aresample=44100", "-ac", "2", saida)


def _nota(midi: int) -> float:
    return 440 * 2 ** ((midi - 69) / 12)


def trilha_sintetica(dur: float, destino: Path) -> None:
    """Música ambiente gerada na hora (acordes suaves com eco): grátis e sem direitos autorais."""
    progressoes = [
        [[45, 57, 60, 64], [41, 57, 60, 65], [48, 55, 60, 64], [43, 55, 59, 62]],  # Lá m, Fá, Dó, Sol
        [[50, 57, 62, 65], [46, 58, 62, 65], [41, 57, 60, 65], [48, 55, 60, 64]],  # Ré m, Si b, Fá, Dó
        [[40, 55, 59, 64], [48, 55, 60, 64], [43, 55, 59, 62], [50, 57, 62, 66]],  # Mi m, Dó, Sol, Ré
    ]
    acordes = random.choice(progressoes)
    seg, cruz = 7.0, 2.0
    n = max(2, math.ceil((dur + 3) / (seg - cruz)) + 1)
    entradas, filtros = [], []
    for i in range(n):
        notas = acordes[i % len(acordes)]
        canais = []
        for desafino in (1.002, 0.998):  # esquerda e direita levemente diferentes = som mais "largo"
            termos = [f"{0.10 if k == 0 else 0.06}*sin(2*PI*{_nota(m):.3f}*t)"
                      f"+{0.04 if k == 0 else 0.03}*sin(2*PI*{_nota(m) * desafino:.3f}*t)"
                      for k, m in enumerate(notas)]
            canais.append("+".join(termos))
        entradas += ["-f", "lavfi", "-i", f"aevalsrc={'|'.join(canais)}:s=44100:d={seg}"]
    anterior = "[0:a]"
    for i in range(1, n):
        filtros.append(f"{anterior}[{i}:a]acrossfade=d={cruz}:c1=qsin:c2=qsin[x{i}]")
        anterior = f"[x{i}]"
    filtros.append(f"{anterior}lowpass=f=1800,tremolo=f=0.15:d=0.2,"
                   f"aecho=0.8:0.6:90|210|380:0.35|0.25|0.15,atrim=0:{dur:.3f}[saida]")
    ff(*entradas, "-filter_complex", ";".join(filtros), "-map", "[saida]", destino)


def preparar_musica(dur: float, pasta: Path) -> Path | None:
    if config.VOLUME_MUSICA <= 0:
        return None
    faixas = [p for p in config.MUSICA.glob("*")
              if p.suffix.lower() in (".mp3", ".m4a", ".wav", ".ogg", ".flac")]
    bruta = pasta / "musica_bruta.wav"
    if faixas:
        faixa = random.choice(faixas)
        print(f"Música de fundo: {faixa.name}")
        ff("-stream_loop", "-1", "-i", faixa, "-t", f"{dur:.3f}", "-ac", "2", "-ar", "44100", bruta)
    else:
        print("Música de fundo: trilha ambiente gerada automaticamente.")
        trilha_sintetica(dur, bruta)
    pronta = pasta / "musica.wav"
    normalizar(bruta, pronta, -16, f"volume={config.VOLUME_MUSICA},afade=t=in:d=1.5,"
                                    f"afade=t=out:st={max(dur - 2.5, 0):.2f}:d=2.5")
    bruta.unlink(missing_ok=True)
    return pronta


# ---- Montagem final ---------------------------------------------------------
def montar(cenas: list[dict], chamada: str, pasta: Path) -> Path:
    """cenas: [{audio, palavras, video|None, dur}]. Devolve o caminho do Short pronto."""
    clipes, todas_palavras, inicio = [], [], 0.0
    for i, cena in enumerate(cenas):
        clipe = pasta / f"clipe_{i:02d}.mp4"
        clipe_da_cena(cena["video"], cena["dur"], clipe)
        clipes.append(clipe)
        todas_palavras += [{**p, "ini": p["ini"] + inicio, "fim": p["fim"] + inicio}
                           for p in cena["palavras"]]
        inicio += cena["dur"]
    total = inicio

    # Junta os clipes (mesmo formato, então não precisa recodificar).
    lista = pasta / "clipes.txt"
    lista.write_text("".join(f"file '{c.name}'\n" for c in clipes), encoding="utf-8")
    video_mudo = pasta / "video_mudo.mp4"
    ff("-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", video_mudo)

    # Narração contínua, com um respiro no fim de cada cena, no volume padrão.
    entradas, filtros = [], []
    for i, cena in enumerate(cenas):
        entradas += ["-i", cena["audio"]]
        filtros.append(f"[{i}:a]aresample=44100,apad,atrim=0:{cena['dur']:.3f}[a{i}]")
    filtros.append("".join(f"[a{i}]" for i in range(len(cenas))) + f"concat=n={len(cenas)}:v=0:a=1[voz]")
    voz_bruta = pasta / "narracao_bruta.wav"
    ff(*entradas, "-filter_complex", ";".join(filtros), "-map", "[voz]", voz_bruta)
    voz = pasta / "narracao.wav"
    normalizar(voz_bruta, voz, -15)
    voz_bruta.unlink(missing_ok=True)

    musica = preparar_musica(total, pasta)
    ass = pasta / "legenda.ass"
    legenda_ass(todas_palavras, chamada, ass)

    entradas = ["-i", video_mudo, "-i", voz]
    if musica:
        entradas += ["-i", musica]
        audio = "[1:a][2:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.9:level=0[aout]"
    else:
        audio = "[1:a]alimiter=limit=0.9:level=0[aout]"
    # Teto de bitrate para o arquivo caber no Telegram.
    kbps = max(1500, min(8000, int(LIMITE_MB * 8000 / max(total, 1)) - 250))
    final = pasta / "short.mp4"
    # O filtro "ass" roda de dentro da pasta para não ter problema com caminhos.
    ff(*entradas, "-filter_complex", f"[0:v]ass={ass.name}[vout];{audio}",
       "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.3f}",
       "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-maxrate", f"{kbps}k",
       "-bufsize", f"{kbps * 2}k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
       "-movflags", "+faststart", final.name, cwd=pasta)
    return final


def _fonte_negrito() -> str:
    r = subprocess.run(["fc-match", "-f", "%{file}", "DejaVu Sans:bold"], capture_output=True, text=True)
    return r.stdout.strip() or "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def capa(video: Path, texto: str, destino: Path) -> Path:
    """Capa 1080x1920: um quadro do vídeo com a frase de impacto (usada no envio automático).
    Cada linha é desenhada separada: versões novas do ffmpeg mostram a quebra de linha como um quadrado."""
    palavras = texto.upper().split() or ["HISTÓRIAS", "DA", "BÍBLIA"]
    meio = (len(palavras) + 1) // 2
    linhas = [t for t in (" ".join(palavras[:meio]), " ".join(palavras[meio:])) if t]
    altura, filtros, arquivos = 150, ["eq=brightness=-0.15"], []
    for i, linha in enumerate(linhas):
        arq = destino.with_name(f"capa_linha{i}.txt")
        arq.write_text(linha, encoding="utf-8")
        arquivos.append(arq)
        filtros.append(f"drawtext=fontfile={_fonte_negrito()}:textfile={arq}:expansion=none:fontsize=120:"
                       f"fontcolor=0xFFD700:borderw=8:bordercolor=black:x=(w-text_w)/2:"
                       f"y=(h-{altura * len(linhas)})/2+{altura * i}")
    ff("-ss", "1.5", "-i", video, "-frames:v", "1", "-vf", ",".join(filtros), "-q:v", "2", destino)
    for arq in arquivos:
        arq.unlink(missing_ok=True)
    return destino
