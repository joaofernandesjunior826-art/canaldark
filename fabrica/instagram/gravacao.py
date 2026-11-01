"""Grava o Reels: o site-conceito rolando dentro do notebook, a frase de abertura e o final da Clover.

Como fica rápido (mesmo no computador do GitHub):
  1. A cena do notebook (cena.html) é fotografada uma vez só, em camadas: fundo, máscara da tela,
     brilho do vidro e frase de abertura. O cartão final da Clover é gravado à parte (3,6 s).
  2. O site é gravado quadro a quadro, reto, em 1280x800 (o tempo é controlado aqui, então o
     movimento sai liso mesmo num computador lento).
  3. O ffmpeg encaixa cada quadro do site na tela do notebook (perspectiva), aproxima a câmera
     devagar, põe a frase e emenda o final com a trilha.
"""
import base64
import functools
import os
import shutil
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LARGURA, ALTURA, FPS = 1080, 1920, 30
SITE_L, SITE_A = 1280, 800
CENA = Path(__file__).with_name("cena.html")
VENDOR = Path(__file__).with_name("vendor")  # three.js (licença MIT), para o notebook 3D
DURACAO = 30.0          # duração do Reels
INICIO_FINAL = 26.4     # quando o cartão final começa a aparecer
TRANSICAO = 0.5         # duração da passagem para o cartão final
ZOOM_MAXIMO = 0.085     # a câmera aproxima 8,5% ao longo do vídeo


class _Silencioso(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class Servidor:
    """Servidor local só para a pasta do vídeo (a página precisa ler as fotos e o site)."""

    def __init__(self, pasta: Path):
        manipulador = functools.partial(_Silencioso, directory=str(pasta))
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), manipulador)
        self.url = f"http://127.0.0.1:{self.http.server_address[1]}"
        threading.Thread(target=self.http.serve_forever, daemon=True).start()

    def fechar(self):
        self.http.shutdown()
        self.http.server_close()


def _abrir_navegador(pw):
    """Chromium da Playwright, se instalado; senão um Chrome do sistema (o GitHub já tem um)."""
    argumentos = ["--hide-scrollbars", "--force-color-profile=srgb", "--font-render-hinting=none",
                  "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
                  "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--enable-webgl"]
    tentativas = [{"executable_path": os.environ["CHROME_PATH"]}] if os.environ.get("CHROME_PATH") else []
    tentativas.append({})
    for nome in ("chromium", "google-chrome", "google-chrome-stable", "chromium-browser"):
        achado = shutil.which(nome)
        if achado:
            tentativas.append({"executable_path": achado})
    erros = []
    for extra in tentativas:
        try:
            return pw.chromium.launch(headless=True, args=argumentos, **extra)
        except Exception as e:  # tenta o próximo navegador
            erros.append(str(e).splitlines()[0][:160])
    raise RuntimeError("Não consegui abrir o navegador para gravar o site: " + " | ".join(erros))


def _ffmpeg(cmd: list[str], entrada=None) -> subprocess.Popen:
    return subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *cmd], stdin=entrada)


class Estudio:
    def __init__(self, pasta: Path):
        from playwright.sync_api import sync_playwright
        self.pasta = pasta
        shutil.copy(CENA, pasta / "cena.html")
        shutil.copytree(VENDOR, pasta / "vendor", dirs_exist_ok=True)
        self.servidor = Servidor(pasta)
        self.pw = sync_playwright().start()
        self.navegador = _abrir_navegador(self.pw)

    def fechar(self):
        for acao in (self.navegador.close, self.pw.stop, self.servidor.fechar):
            try:
                acao()
            except Exception:
                pass

    def _pagina(self, largura: int, altura: int, caminho: str):
        pagina = self.navegador.new_page(viewport={"width": largura, "height": altura}, device_scale_factor=1)
        pagina.set_default_timeout(120_000)
        pagina.goto(f"{self.servidor.url}/{caminho}", wait_until="networkidle")
        return pagina, pagina.context.new_cdp_session(pagina)

    @staticmethod
    def _foto(cdp, formato="jpeg", qualidade=92, recorte=None) -> bytes:
        arg = {"format": formato, "optimizeForSpeed": True}
        if formato == "jpeg":
            arg["quality"] = qualidade
        if recorte:
            x, y, w, h = recorte
            arg["clip"] = {"x": x, "y": y, "width": w, "height": h, "scale": 1}
        return base64.b64decode(cdp.send("Page.captureScreenshot", arg)["data"])

    # ---- 1. A cena do notebook, em camadas ----
    def fotografar_cena(self, opcoes: dict) -> dict:
        p = self.pasta
        pagina, cdp = self._pagina(LARGURA, ALTURA, "cena.html")
        pagina.wait_for_function("window.pronto === true")
        inicio = time.time()
        pagina.evaluate("op => configurar(op)", opcoes)
        print(f"  notebook 3D desenhado em {time.time() - inicio:.0f} s")
        pagina.evaluate("() => camada('cena')")
        (p / "camada_fundo.png").write_bytes(self._foto(cdp, "png"))
        pagina.evaluate("() => camada('tela')")
        (p / "camada_tela.png").write_bytes(self._foto(cdp, "png"))
        medidas = pagina.evaluate("() => medidas()")
        transparente = {"color": {"r": 0, "g": 0, "b": 0, "a": 0}}
        cdp.send("Emulation.setDefaultBackgroundColorOverride", transparente)
        pagina.evaluate("() => camada('vidro')")
        (p / "camada_frente.png").write_bytes(self._foto(cdp, "png"))
        pagina.evaluate("() => camada('gancho')")
        for nome in ("g1", "g2"):
            x, y, w, h = medidas[nome]
            caixa = (int(x) - 2, int(y) - 2, int(w) + 5, int(h) + 5)
            (p / f"camada_{nome}.png").write_bytes(self._foto(cdp, "png", recorte=caixa))
            medidas[nome] = caixa
        cdp.send("Emulation.setDefaultBackgroundColorOverride", {})
        # cartão final, quadro a quadro
        pagina.evaluate("() => camada('final')")
        n = round((DURACAO - INICIO_FINAL) * FPS)
        ff = _ffmpeg(["-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264",
                      "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", str(p / "camada_final.mp4")],
                     entrada=subprocess.PIPE)
        try:
            for i in range(n):
                pagina.evaluate("t => quadroFinal(t)", i / FPS)
                ff.stdin.write(self._foto(cdp, "jpeg", 94))
        finally:
            ff.stdin.close()
            ff.wait()
        pagina.close()
        if ff.returncode != 0:
            raise RuntimeError("Não consegui gravar o cartão final.")
        return medidas

    # ---- 2 e 3. O site, quadro a quadro, já encaixado no notebook ----
    def gravar(self, medidas: dict, trilha: Path | None, destino: Path) -> Path:
        pagina, cdp = self._pagina(SITE_L, SITE_A, "site.html")
        pagina.evaluate("""async () => {
          await document.fonts.ready;
          await Promise.all([...document.images].map((im) => im.complete ? 0 : new Promise((ok) => { im.onload = im.onerror = ok; })));
        }""")
        info = pagina.evaluate("() => prepararSite({inicio: 1.1, inicioRolagem: 4.2, fim: 25.2})")
        print(f"  site com {info['altura']} px e {len(info['paradas'])} paradas")

        fim_principal = INICIO_FINAL + TRANSICAO
        n = round(fim_principal * FPS) + 1
        cmd = self._comando(medidas, trilha, destino, fim_principal)
        ff = _ffmpeg(cmd, entrada=subprocess.PIPE)
        inicio = time.time()
        try:
            for i in range(n):
                pagina.evaluate("t => quadroSite(t)", i / FPS)
                try:
                    ff.stdin.write(self._foto(cdp, "jpeg", 93))
                except BrokenPipeError:
                    break  # o ffmpeg parou; o erro dele aparece no registro
                if i and i % (FPS * 5) == 0:
                    print(f"  gravando: {i / FPS:.0f} de {fim_principal:.0f} s "
                          f"({(time.time() - inicio) / i * 1000:.0f} ms por quadro)", flush=True)
        finally:
            ff.stdin.close()
            ff.wait()
        pagina.close()
        if ff.returncode != 0:
            raise RuntimeError("O ffmpeg não conseguiu montar o Reels.")
        print(f"  Reels montado em {time.time() - inicio:.0f} s")
        return destino

    def _comando(self, m: dict, trilha: Path | None, destino: Path, fim_principal: float) -> list[str]:
        p = self.pasta
        cantos = m["cantos"]
        xs, ys = [c[0] for c in cantos], [c[1] for c in cantos]
        bx, by = int(min(xs)) - 1, int(min(ys)) - 1
        bw, bh = int(max(xs)) + 2 - bx, int(max(ys)) + 2 - by
        bw, bh = bw + bw % 2, bh + bh % 2
        rel = [(x - bx, y - by) for x, y in cantos]
        quad = ":".join(f"x{i}={x:.2f}:y{i}={y:.2f}" for i, (x, y) in enumerate(rel))
        # câmera: aproxima devagar na direção da tela (sem nunca mostrar borda preta)
        tx, ty = sum(xs) / 4, sum(ys) / 4
        e = f"(clip(in/{fim_principal * FPS:.1f},0,1)*clip(in/{fim_principal * FPS:.1f},0,1)*(3-2*clip(in/{fim_principal * FPS:.1f},0,1)))"
        z = f"(1+{ZOOM_MAXIMO}*{e})"
        folga_x, folga_y = LARGURA / 2 * (1 - 1 / (1 + ZOOM_MAXIMO)) * 0.9, ALTURA / 2 * (1 - 1 / (1 + ZOOM_MAXIMO)) * 0.9
        dx = max(-folga_x, min(folga_x, tx - LARGURA / 2))
        dy = max(-folga_y, min(folga_y, ty - ALTURA / 2))
        cx, cy = f"({LARGURA / 2}+{dx:.2f}*{e})", f"({ALTURA / 2}+{dy:.2f}*{e})"
        hw, hh = f"({LARGURA / 2}/{z})", f"({ALTURA / 2}/{z})"
        camera = (f"perspective=x0='{cx}-{hw}':y0='{cy}-{hh}':x1='{cx}+{hw}':y1='{cy}-{hh}':"
                  f"x2='{cx}-{hw}':y2='{cy}+{hh}':x3='{cx}+{hw}':y3='{cy}+{hh}':sense=source:eval=frame:interpolation=linear")
        g1x, g1y, _, _ = m["g1"]
        g2x, g2y, _, _ = m["g2"]

        def surge(inicio):  # a frase sobe um pouco enquanto aparece
            return f"'{{y}}+26*pow(max(0,1-(t-{inicio})/0.35),3)'"

        fixo = f"loop=loop=-1:size=1:start=0,setpts=N/{FPS}/TB"  # imagem parada: decodifica uma vez só
        filtros = ";".join([
            f"[0:v]format=yuv420p,{fixo}[fundo]",
            f"[1:v]scale={bw}:{bh}:flags=lanczos,format=yuv444p,perspective={quad}:sense=destination:interpolation=cubic,format=yuva444p[site]",
            f"[2:v]format=gray,crop={bw}:{bh}:{bx}:{by},{fixo}[mascara]",
            "[site][mascara]alphamerge[sitem]",
            f"[fundo][sitem]overlay={bx}:{by}:format=yuv420[c1]",
            f"[3:v]format=yuva420p,{fixo}[vidro]",
            "[c1][vidro]overlay=0:0:format=yuv420[c2]",
            f"[c2]{camera}[cam]",
            f"[4:v]format=yuva420p,{fixo},fade=t=in:st=0.25:d=0.25:alpha=1[g1]",
            f"[5:v]format=yuva420p,{fixo},fade=t=in:st=1.0:d=0.25:alpha=1[g2]",
            f"[cam][g1]overlay=x={g1x}:y={surge(0.25).format(y=g1y)}:format=yuv420[c3]",
            f"[c3][g2]overlay=x={g2x}:y={surge(1.0).format(y=g2y)}:format=yuv420[c4]",
            f"[c4]trim=duration={fim_principal:.3f},setpts=PTS-STARTPTS,fps={FPS},settb=AVTB,format=yuv420p[principal]",
            f"[6:v]setpts=PTS-STARTPTS,fps={FPS},settb=AVTB,format=yuv420p[final]",
            f"[principal][final]xfade=transition=fade:duration={TRANSICAO}:offset={INICIO_FINAL}[v]",
        ])
        imagem = lambda nome: ["-framerate", str(FPS), "-i", str(p / nome)]
        cmd = [*imagem("camada_fundo.png"),
               "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
               *imagem("camada_tela.png"), *imagem("camada_frente.png"), *imagem("camada_g1.png"), *imagem("camada_g2.png"),
               "-i", str(p / "camada_final.mp4")]
        if trilha and Path(trilha).exists():
            cmd += ["-i", str(trilha)]
            audio = ["-map", "7:a", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
            audio = ["-map", "7:a", "-c:a", "aac", "-b:a", "128k"]
        cmd += ["-filter_complex", filtros, "-map", "[v]", *audio, "-t", f"{DURACAO}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-maxrate", "9M", "-bufsize", "18M",
                "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart", str(destino)]
        return cmd
