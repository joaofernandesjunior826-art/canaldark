"""Trilha do Reels: uma batida lo-fi gerada na hora (bateria, baixo e piano elétrico).

Tudo é sintetizado aqui, sem nenhum arquivo de música: grátis e sem direitos autorais. A bateria
entra quando o site aparece ("O site:") e para no cartão final, onde o último acorde fica soando.
"""
import array
import math
import random
import subprocess
import wave
from pathlib import Path

TAXA = 44100

# Progressões (notas MIDI do acorde e do baixo). Um acorde por compasso.
PROGRESSOES = [
    [([53, 57, 60, 64], 41), ([52, 55, 59, 62], 40), ([50, 53, 57, 60], 38), ([48, 52, 55, 59], 36)],  # Fmaj7 Em7 Dm7 Cmaj7
    [([50, 53, 57, 60, 64], 38), ([55, 59, 62, 65], 43), ([48, 52, 55, 59, 62], 36), ([57, 60, 64, 67], 45)],  # Dm9 G7 Cmaj9 Am7
    [([57, 60, 64, 67], 45), ([53, 57, 60, 64], 41), ([48, 52, 55, 59], 36), ([55, 59, 62, 65], 43)],  # Am7 Fmaj7 Cmaj7 G7
    [([52, 55, 59, 62], 40), ([57, 60, 64, 67], 45), ([50, 54, 57, 60], 38), ([55, 59, 62, 66], 43)],  # Em7 Am7 D7 Gmaj7
]


def _hz(nota: int) -> float:
    return 440.0 * 2 ** ((nota - 69) / 12)


def _acorde(notas: list[int], dur: float, desafino: float) -> list[float]:
    """Piano elétrico simples: fundamental + harmônicos que somem rápido, ataque macio."""
    n = int(dur * TAXA)
    saida = [0.0] * n
    for nota in notas:
        f = _hz(nota) * desafino
        w1, w2, w3 = 2 * math.pi * f / TAXA, 4 * math.pi * f / TAXA, 6 * math.pi * f / TAXA
        ganho = 0.16 / len(notas) ** 0.5
        for i in range(n):
            t = i / TAXA
            env = min(1.0, t / 0.012) * (0.3 + 0.7 * math.exp(-1.6 * t))
            saida[i] += ganho * env * (math.sin(w1 * i) + 0.28 * math.exp(-5 * t) * math.sin(w2 * i)
                                       + 0.08 * math.exp(-9 * t) * math.sin(w3 * i))
    return saida


def _baixo(nota: int, dur: float) -> list[float]:
    n = int(dur * TAXA)
    w = 2 * math.pi * _hz(nota) / TAXA
    return [0.34 * min(1.0, (i / TAXA) / 0.01) * math.exp(-1.1 * i / TAXA) * (math.sin(w * i) + 0.15 * math.sin(2 * w * i))
            for i in range(n)]


def _bumbo() -> list[float]:
    n = int(0.42 * TAXA)
    saida, fase = [], 0.0
    for i in range(n):
        t = i / TAXA
        fase += 2 * math.pi * (48 + 95 * math.exp(-28 * t)) / TAXA
        saida.append(0.95 * math.exp(-7.5 * t) * math.sin(fase))
    return saida


def _caixa(rnd: random.Random) -> list[float]:
    n = int(0.26 * TAXA)
    saida, filtrado = [], 0.0
    for i in range(n):
        t = i / TAXA
        filtrado += 0.45 * (rnd.uniform(-1, 1) - filtrado)  # ruído um pouco mais escuro
        saida.append(0.42 * math.exp(-16 * t) * filtrado + 0.18 * math.exp(-28 * t) * math.sin(2 * math.pi * 185 * t))
    return saida


def _chimbal(rnd: random.Random) -> list[float]:
    n = int(0.07 * TAXA)
    saida, baixo = [], 0.0
    for i in range(n):
        x = rnd.uniform(-1, 1)
        baixo += 0.35 * (x - baixo)
        saida.append(0.16 * math.exp(-70 * i / TAXA) * (x - baixo))  # só os agudos
    return saida


def _somar(destino: list[float], som: list[float], inicio: float, ganho: float = 1.0) -> None:
    i0 = int(inicio * TAXA)
    for j, v in enumerate(som):
        if i0 + j >= len(destino):
            break
        if i0 + j >= 0:
            destino[i0 + j] += v * ganho


def gerar(destino: Path, dur: float = 20.0, entrada_bateria: float = 1.1, fim_bateria: float = 17.0,
          semente: int | None = None) -> Path:
    rnd = random.Random(semente)
    bpm = rnd.choice([88, 92, 96, 100])
    tempo = 60 / bpm
    compasso = 4 * tempo
    progressao = rnd.choice(PROGRESSOES)
    n = int(dur * TAXA)
    esq, dir_ = [0.0] * n, [0.0] * n

    # acordes e baixo: a grade começa na entrada da bateria (o primeiro acorde já soa antes, crescendo)
    cache = {}
    k = -1
    while entrada_bateria + k * compasso < dur:
        inicio = entrada_bateria + k * compasso
        notas, raiz = progressao[k % len(progressao)]
        chave = tuple(notas)
        if chave not in cache:
            cache[chave] = (_acorde(notas, compasso + 1.2, 1.0), _acorde(notas, compasso + 1.2, 1.0035), _baixo(raiz, compasso))
        a_esq, a_dir, baixo = cache[chave]
        ganho = 0.55 if k < 0 else 1.0
        _somar(esq, a_esq, inicio, ganho)
        _somar(dir_, a_dir, inicio, ganho)
        if 0 <= k and inicio < fim_bateria:
            _somar(esq, baixo, inicio)
            _somar(dir_, baixo, inicio)
        k += 1

    # bateria (16 passos por compasso, com um pouco de swing)
    bumbo, caixa, chimbal = _bumbo(), _caixa(rnd), _chimbal(rnd)
    padrao_bumbo = rnd.choice([{0, 7, 10}, {0, 6, 10}, {0, 3, 10}, {0, 8, 11}])
    swing = 0.18 * tempo / 4
    t = entrada_bateria
    passo = 0
    while t < fim_bateria - 0.01:
        p = passo % 16
        atraso = swing if p % 4 == 2 else 0.0
        if p in padrao_bumbo:
            _somar(esq, bumbo, t + atraso)
            _somar(dir_, bumbo, t + atraso)
        if p in (4, 12):
            _somar(esq, caixa, t, 0.95)
            _somar(dir_, caixa, t, 1.05)
        if p % 2 == 0:
            vel = 1.0 if p % 4 == 0 else 0.6
            _somar(esq, chimbal, t + atraso, vel * 0.8)
            _somar(dir_, chimbal, t + atraso, vel * 1.2)
        passo += 1
        t = entrada_bateria + passo * tempo / 4

    pico = max(max(map(abs, esq)), max(map(abs, dir_)), 1e-6)
    escala = 0.89 / pico * 32767
    amostras = array.array("h")
    for a, b in zip(esq, dir_):
        amostras.append(int(a * escala))
        amostras.append(int(b * escala))
    bruto = destino.with_suffix(".bruto.wav")
    with wave.open(str(bruto), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(amostras.tobytes())
    # acabamento: sala pequena, menos graves embolados, volume padrão do Instagram (-14 LUFS)
    filtros = ("highpass=f=32,lowpass=f=11000,aecho=0.85:0.5:60|140:0.22|0.12,"
               "acompressor=threshold=0.25:ratio=2.5:attack=8:release=180,"
               f"afade=t=in:st=0:d=0.6,afade=t=out:st={dur - 1.5:.2f}:d=1.5,loudnorm=I=-14:TP=-1.2:LRA=9")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(bruto), "-af", filtros,
                    "-ar", "48000", "-t", f"{dur}", str(destino)], check=True)
    bruto.unlink(missing_ok=True)
    return destino
