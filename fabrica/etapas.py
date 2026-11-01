"""As 8 estações da fábrica. Cada uma roda como um passo separado no GitHub Actions, para o painel
mostrar ao vivo em qual estação o vídeo está. O andamento fica salvo em saida/trabalho.json."""
import json
import shutil
from pathlib import Path

from . import cenas, config, estado, github, montagem, narracao, roteiro, telegram, youtube

ETAPAS = [("pauta", "1 Pauta"), ("roteiro", "2 Roteiro"), ("narracao", "3 Narração"),
          ("cenas", "4 Cenas"), ("montagem", "5 Montagem"), ("shorts", "6 Shorts"),
          ("thumbnail", "7 Thumbnail"), ("agenda", "8 Agenda")]
ARQ_TRABALHO = config.SAIDA / "trabalho.json"
ROTEIRO_EXEMPLO = config.DADOS / "roteiro_exemplo.json"


def ler_trabalho() -> dict | None:
    try:
        return json.loads(ARQ_TRABALHO.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def salvar_trabalho(t: dict) -> None:
    ARQ_TRABALHO.parent.mkdir(parents=True, exist_ok=True)
    ARQ_TRABALHO.write_text(json.dumps(t, ensure_ascii=False, indent=2), encoding="utf-8")


def iniciar(tarefa: dict) -> dict:
    video_id = estado.agora().strftime("%Y%m%d-%H%M%S")
    pasta = config.SAIDA / video_id
    pasta.mkdir(parents=True, exist_ok=True)
    t = {"tarefa": tarefa, "id": video_id, "pasta": str(pasta), "etapa": 0}
    salvar_trabalho(t)
    return t


# ---- Estações ---------------------------------------------------------------
def _pauta(t: dict) -> None:
    tarefa = t["tarefa"]
    if tarefa["tipo"] == "refazer":
        original = estado.achar_video(tarefa["origem"])
        if not original:
            raise RuntimeError("Não achei o vídeo original para refazer.")
        titulo, ref = original["historia"], original.get("referencia", "")
    elif tarefa["tipo"] == "teste":
        exemplo = json.loads(ROTEIRO_EXEMPLO.read_text(encoding="utf-8"))
        titulo, ref = exemplo["historia"], exemplo["referencia"]
    elif tarefa.get("tema"):
        titulo, ref = roteiro.achar_historia(tarefa["tema"]) or (tarefa["tema"], "")
    else:
        titulo, ref = roteiro.proxima_historia()
    t.update(historia=titulo, referencia=ref, ajuste=tarefa.get("ajuste", ""))
    print(f"Pauta: {titulo} {f'({ref})' if ref else ''}")


def _roteiro(t: dict) -> None:
    if t["tarefa"]["tipo"] == "teste" or t.get("roteiro_pronto"):
        texto = t.get("roteiro_pronto") or json.loads(ROTEIRO_EXEMPLO.read_text(encoding="utf-8"))
    else:
        recentes = [v["titulo"] for v in estado.historico()[-8:] if v.get("titulo")]
        texto = roteiro.gerar_roteiro(t["historia"], t["referencia"], t.get("ajuste", ""), recentes)
    t["roteiro"] = texto
    Path(t["pasta"], "roteiro.json").write_text(json.dumps(texto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Título: {texto['titulo']} ({len(texto['cenas'])} cenas)")


def _narracao(t: dict) -> None:
    partes = []
    for i, cena in enumerate(t["roteiro"]["cenas"]):
        audio = Path(t["pasta"], f"voz_{i:02d}.mp3")
        palavras = narracao.narrar(cena["texto"], audio)
        partes.append({"audio": str(audio), "palavras": palavras,
                       "dur": montagem.duracao(audio) + montagem.PAUSA, "video": None})
    t["partes"] = partes
    print(f"Narração: {sum(p['dur'] for p in partes):.0f} s")


def _cenas(t: dict) -> None:
    e = estado.ler_estado()
    evitar = set(e["clipes_usados"])
    for i, (cena, parte) in enumerate(zip(t["roteiro"]["cenas"], t["partes"])):
        arquivo = Path(t["pasta"], f"cena_{i:02d}.mp4")
        if cenas.baixar_cena(cena["busca"], arquivo, evitar, parte["dur"]):
            parte["video"] = str(arquivo)
    if t.get("salvar_estado", True):  # o teste local não mexe nos dados do repositório
        e["clipes_usados"] = list(dict.fromkeys(e["clipes_usados"] + sorted(evitar)))
        estado.salvar_estado(e)


def _montagem(t: dict) -> None:
    t["base"] = montagem.montar_base(t["partes"], Path(t["pasta"]))


def _shorts(t: dict) -> None:
    short = montagem.finalizar(t["base"], t["roteiro"].get("capa", ""), Path(t["pasta"]))
    t["short"], t["duracao"] = str(short), montagem.duracao(short)
    print(f"Short pronto: {t['duracao']:.0f} s, {short.stat().st_size / 1e6:.1f} MB")


def _thumbnail(t: dict) -> None:
    texto = t["roteiro"].get("capa") or t["roteiro"]["titulo"]
    t["capa"] = str(montagem.capa(Path(t["base"]["video_mudo"]), texto, Path(t["pasta"], "capa.jpg")))


def _agenda(t: dict, enviar: bool) -> None:
    """Põe o vídeo na fila de aprovação: guarda a prévia, registra e avisa."""
    texto, tarefa = t["roteiro"], t["tarefa"]
    item = {"id": t["id"], "tipo": tarefa["tipo"], "status": "aguardando", "historia": t["historia"],
            "referencia": texto.get("referencia") or t["referencia"],
            "titulo": ("[TESTE] " if tarefa["tipo"] == "teste" else "") + texto["titulo"],
            "descricao": texto.get("descricao", ""), "tags": texto.get("tags", []),
            "data": estado.agora().isoformat(timespec="seconds"), "duracao_seg": round(t["duracao"])}
    if t.get("ajuste"):
        item["ajuste"] = t["ajuste"]
    if tarefa.get("origem"):
        item["origem"] = tarefa["origem"]
    if not enviar:
        return
    if github.ativo():
        github.enviar_previas(t["id"], [(Path(t["short"]), "video/mp4"), (Path(t["capa"]), "image/jpeg")])
        item["previa"] = True
    item["telegram"] = telegram.avisar_novo(Path(t["short"]), item)
    estado.adicionar_video(item)
    if tarefa.get("origem"):
        estado.atualizar_video(tarefa["origem"], status="substituido", substituido_por=t["id"])


def publicar_aprovados() -> None:
    """Envia ao YouTube os vídeos aprovados (só quando o envio automático está ligado)."""
    e = estado.ler_estado()
    pendentes = [x for x in e["fila"] if x["tipo"] == "publicar"]
    if not pendentes or not youtube.configurado():
        return
    for tarefa in pendentes:
        e["fila"].remove(tarefa)
        estado.salvar_estado(e)
        video = estado.achar_video(tarefa["id"])
        if not video or video.get("status") != "aprovado":
            continue
        pasta = config.SAIDA / f"publicar-{video['id']}"
        pasta.mkdir(parents=True, exist_ok=True)
        try:
            arquivo = github.baixar_previa(f"{video['id']}.mp4", pasta / "short.mp4")
            try:
                capa = github.baixar_previa(f"{video['id']}.jpg", pasta / "capa.jpg")
            except Exception:
                capa = None
            ocupados = {v["youtube"]["agendado_para"] for v in estado.historico()
                        if v.get("status") == "programado" and (v.get("youtube") or {}).get("agendado_para")}
            yt = youtube.enviar(arquivo, capa, video, ocupados)
            atualizado = estado.atualizar_video(video["id"], status="programado", youtube=yt)
            telegram.avisar_programado(atualizado)
        except Exception as erro:
            print(f"Não consegui enviar ao YouTube: {erro}")
            telegram.enviar_texto(f"⚠️ Não consegui enviar “{telegram.html(video['titulo'])}” ao YouTube. "
                                  f"Aprove de novo mais tarde.\n\nErro: <code>{telegram.html(str(erro)[:300])}</code>")
        finally:
            shutil.rmtree(pasta, ignore_errors=True)


ESTACOES = {"pauta": _pauta, "roteiro": _roteiro, "narracao": _narracao, "cenas": _cenas,
            "montagem": _montagem, "shorts": _shorts, "thumbnail": _thumbnail}


def executar_etapa(nome: str, enviar: bool = True) -> None:
    numero = next(i for i, (n, _) in enumerate(ETAPAS, 1) if n == nome)
    t = ler_trabalho()
    if nome == "agenda":
        if t and t["etapa"] == numero - 1:
            _agenda(t, enviar)
            if enviar:
                _limpar(t)
                ARQ_TRABALHO.unlink(missing_ok=True)
        if enviar:
            publicar_aprovados()
            _limpar_previas_antigas()
        return
    if not t:
        print(f"Nada para fazer na estação {nome}.")
        return
    if t["etapa"] != numero - 1:
        raise RuntimeError(f"Estação fora de ordem: {nome} (o trabalho está na etapa {t['etapa']}).")
    ESTACOES[nome](t)
    t["etapa"] = numero
    salvar_trabalho(t)


def produzir_tudo(tarefa: dict, enviar: bool = True, roteiro_pronto: dict | None = None) -> dict:
    """Roda as 8 estações seguidas no mesmo processo (usado no teste local)."""
    t = iniciar(tarefa)
    t["salvar_estado"] = enviar
    if roteiro_pronto:
        t["roteiro_pronto"] = roteiro_pronto
    salvar_trabalho(t)
    for nome, _ in ETAPAS:
        executar_etapa(nome, enviar)
    return t


def _limpar(t: dict) -> None:
    pasta = Path(t["pasta"])
    for arq in [*pasta.glob("cena_*.mp4"), *pasta.glob("voz_*.mp3"), pasta / "video_mudo.mp4",
                pasta / "narracao.wav", pasta / "musica.wav"]:
        arq.unlink(missing_ok=True)


def _limpar_previas_antigas() -> None:
    if not github.ativo():
        return
    videos = [v for v in estado.historico() if v.get("previa")]
    manter = {v["id"] for v in videos[-config.MANTER_PREVIAS:]}
    manter |= {v["id"] for v in videos if v.get("status") in ("aguardando", "aprovado")}
    github.limpar_previas(manter)


def registrar_falha() -> None:
    """Chamado quando um passo falha: descobre a estação, conta a falha e avisa."""
    t = ler_trabalho()
    e = estado.ler_estado()
    if t:
        estacao = ETAPAS[min(t["etapa"], len(ETAPAS) - 1)][1]
        tarefa = t["tarefa"]
        if tarefa["tipo"] == "novo":
            n = estado.registrar_falha(e)
            if n >= config.MAX_FALHAS_POR_DIA:
                msg = f"⚠️ O vídeo de hoje parou na estação {estacao} ({n} tentativas). Paro por hoje e volto amanhã."
            else:
                msg = (f"⚠️ O vídeo de hoje parou na estação {estacao} (tentativa {n} de "
                       f"{config.MAX_FALHAS_POR_DIA}). Tento de novo na próxima hora.")
        else:
            msg = f"⚠️ Um pedido parou na estação {estacao}. Pode pedir de novo daqui a pouco."
        e["ultima_falha"] = {"estacao": estacao, "quando": estado.agora().isoformat(timespec="seconds"),
                             "tipo": tarefa["tipo"]}
        ARQ_TRABALHO.unlink(missing_ok=True)
    else:
        msg = "⚠️ A fábrica teve um problema ao ler os pedidos."
        e["ultima_falha"] = {"estacao": "Pedidos", "quando": estado.agora().isoformat(timespec="seconds")}
    estado.salvar_estado(e)
    if config.LINK_EXECUCAO:
        msg += f"\n\nDetalhes: {config.LINK_EXECUCAO}"
    telegram.enviar_texto(msg, botoes=telegram._botao_painel())
    print(msg)
