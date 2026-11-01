"""Etapa 4: monta o Short (1080x1920) com ffmpeg: cenas + narração + legenda + música + capa."""
import random
import re
import subprocess
from pathlib import Path

from . import config

W, H, FPS = config.LARGURA, config.ALTURA, config.FPS
PAUSA = 0.25  # respiro entre cenas, em segundos


def ff(*args: str) -> None:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou: {' '.join(cmd)}\n{r.stderr[-2000:]}")


def duracao(arq: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(arq)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def clipe_da_cena(origem: Path | None, dur: float, destino: Path) -> None:
    """Corta/ajusta o vídeo da cena para o tamanho vertical, com leve zoom e escurecido."""
    filtro = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"fps={FPS},setsar=1,eq=brightness=-0.06:saturation=0.9,format=yuv420p")
    if origem:
        entrada = ["-stream_loop", "-1", "-i", str(origem)]
    else:  # sem vídeo: fundo em movimento nas cores do canal
        cores = random.choice([("0x1b1209", "0x5a3a12"), ("0x0b0f1d", "0x3a2a52"),
                               ("0x120a05", "0x6b4a1f")])
        entrada = ["-f", "lavfi", "-i",
                   f"gradients=s={W}x{H}:c0={cores[0]}:c1={cores[1]}:speed=0.01:r={FPS}"]
    ff(*entrada, "-t", f"{dur:.3f}", "-vf", filtro, "-an", "-c:v", "libx264",
       "-preset", "veryfast", "-crf", "20", "-r", str(FPS), str(destino))


def _tempo_ass(seg: float) -> str:
    h, resto = divmod(max(seg, 0), 3600)
    m, s = divmod(resto, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def legenda_ass(palavras: list[dict], destino: Path) -> None:
    """Legenda estilo Shorts: blocos de até 3 palavras, grandes, um pouco abaixo do meio."""
    cabecalho = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,DejaVu Sans,82,&H00FFFFFF,&H0000D7FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,2,80,80,560,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    blocos, atual = [], []
    for p in palavras:
        atual.append(p)
        if len(atual) == 3 or re.search(r"[.,!?;:]$", p["texto"]):
            blocos.append(atual)
            atual = []
    if atual:
        blocos.append(atual)

    linhas = []
    for i, bloco in enumerate(blocos):
        fim = blocos[i + 1][0]["ini"] if i + 1 < len(blocos) else bloco[-1]["fim"] + 0.3
        fim = min(fim, bloco[-1]["fim"] + 0.6)
        # Destaca em dourado a palavra que está sendo falada.
        for j, p in enumerate(bloco):
            p_fim = bloco[j + 1]["ini"] if j + 1 < len(bloco) else fim
            texto = " ".join(
                ("{\\c&H0000D7FF&}" + q["texto"].upper() + "{\\c&H00FFFFFF&}") if k == j
                else q["texto"].upper() for k, q in enumerate(bloco))
            animacao = "{\\fscx108\\fscy108\\t(0,90,\\fscx100\\fscy100)}" if j == 0 else ""
            linhas.append(f"Dialogue: 0,{_tempo_ass(p['ini'])},{_tempo_ass(p_fim)},Base,,0,0,0,,"
                          f"{animacao}{texto}")
    destino.write_text(cabecalho + "\n".join(linhas) + "\n", encoding="utf-8")


def _musica() -> Path | None:
    faixas = [p for p in config.MUSICA.glob("*") if p.suffix.lower() in (".mp3", ".m4a", ".wav", ".ogg")]
    return random.choice(faixas) if faixas else None


def montar(cenas: list[dict], pasta: Path) -> Path:
    """cenas: [{audio, palavras, video|None}]. Devolve o caminho do Short final."""
    clipes, audios, todas_palavras = [], [], []
    inicio = 0.0
    for i, cena in enumerate(cenas):
        dur = duracao(cena["audio"]) + PAUSA
        clipe = pasta / f"clipe_{i:02d}.mp4"
        clipe_da_cena(cena["video"], dur, clipe)
        clipes.append(clipe)
        audios.append((cena["audio"], dur))
        todas_palavras += [{**p, "ini": p["ini"] + inicio, "fim": p["fim"] + inicio}
                           for p in cena["palavras"]]
        inicio += dur

    # Junta os clipes (todos com o mesmo formato, então não precisa recodificar).
    lista = pasta / "clipes.txt"
    lista.write_text("".join(f"file '{c.name}'\n" for c in clipes), encoding="utf-8")
    video_mudo = pasta / "video_mudo.mp4"
    ff("-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(video_mudo))

    # Narração contínua, com a pausa no fim de cada cena.
    entradas, filtros = [], []
    for i, (audio, dur) in enumerate(audios):
        entradas += ["-i", str(audio)]
        filtros.append(f"[{i}:a]aresample=44100,apad,atrim=0:{dur:.3f}[a{i}]")
    filtros.append("".join(f"[a{i}]" for i in range(len(audios))) + f"concat=n={len(audios)}:v=0:a=1[out]")
    narracao = pasta / "narracao.wav"
    ff(*entradas, "-filter_complex", ";".join(filtros), "-map", "[out]", str(narracao))

    ass = pasta / "legenda.ass"
    legenda_ass(todas_palavras, ass)

    total = inicio
    final = pasta / "short.mp4"
    musica = _musica()
    entradas = ["-i", str(video_mudo), "-i", str(narracao)]
    if musica:
        print(f"Música de fundo: {musica.name}")
        entradas += ["-stream_loop", "-1", "-i", str(musica)]
        audio_filtro = (f"[2:a]volume={config.VOLUME_MUSICA},afade=t=out:st={max(total - 2, 0):.2f}:d=2[m];"
                        f"[1:a][m]amix=inputs=2:duration=first:normalize=0[aout]")
    else:
        audio_filtro = "[1:a]anull[aout]"
    _final(entradas, ass, audio_filtro, total, final)
    return final


def _final(entradas, ass: Path, audio_filtro: str, total: float, final: Path) -> None:
    # O filtro "ass" é chamado de dentro da pasta para evitar problemas com caminhos.
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *entradas, "-filter_complex",
           f"[0:v]ass={ass.name}[vout];{audio_filtro}", "-map", "[vout]", "-map", "[aout]",
           "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
           str(final)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ass.parent)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg (montagem final) falhou:\n{r.stderr[-2000:]}")


def _fonte_negrito() -> str:
    r = subprocess.run(["fc-match", "-f", "%{file}", "DejaVu Sans:bold"], capture_output=True, text=True)
    return r.stdout.strip() or "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def capa(video: Path, texto: str, destino: Path) -> Path:
    """Capa 1080x1920: um quadro do vídeo + o texto de impacto."""
    arq_texto = destino.with_suffix(".txt")
    palavras = texto.upper().split()
    meio = (len(palavras) + 1) // 2
    arq_texto.write_text(" ".join(palavras[:meio]) + "\n" + " ".join(palavras[meio:]), encoding="utf-8")
    ff("-ss", "1.5", "-i", str(video), "-frames:v", "1", "-vf",
       f"eq=brightness=-0.15,drawtext=fontfile={_fonte_negrito()}:textfile={arq_texto}:"
       f"text_align=C:fontsize=120:fontcolor=0xFFD700:borderw=8:bordercolor=black:line_spacing=20:"
       f"x=(w-text_w)/2:y=(h-text_h)/2",
       "-q:v", "2", str(destino))
    return destino
