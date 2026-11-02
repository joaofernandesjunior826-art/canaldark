"""Ações sobre os vídeos, venham elas do painel, do Telegram ou do botão "Run workflow" do GitHub."""
from datetime import datetime, time, timedelta

from . import config, estado, telegram, youtube

TAREFAS_DE_PRODUCAO = ("novo", "extra", "refazer", "teste", "instagram")


def enfileirar(e: dict, tarefa: dict) -> bool:
    """Põe a tarefa na fila se ela ainda não estiver lá. Devolve True se entrou."""
    if tarefa in e["fila"]:
        return False
    e["fila"].append(tarefa)
    return True


# ---- Agenda de postagem: um vídeo pronto para cada horário ------------------------
OCUPA_HORARIO = ("aguardando", "aprovado", "programado", "publicado")


def _texto(quando: datetime) -> str:
    return quando.isoformat(timespec="minutes")


def horarios_da_janela(agora: datetime | None = None) -> list[datetime]:
    """Horários de postagem das próximas horas (os que ainda dá tempo de preparar e aprovar)."""
    agora = agora or estado.agora()
    inicio, fim = agora + timedelta(minutes=30), agora + timedelta(hours=config.ANTECEDENCIA_HORAS)
    saida = []
    for d in range(3):
        dia = agora.date() + timedelta(days=d)
        for h, m in config.POSTAGEM:
            quando = datetime.combine(dia, time(h, m), tzinfo=config.FUSO)
            if inicio <= quando <= fim:
                saida.append(quando)
    return saida


def horarios_ocupados(e: dict) -> set[str]:
    ocupados = {v["postar_em"] for v in estado.historico() if v.get("postar_em") and v.get("status") in OCUPA_HORARIO}
    ocupados |= {t["horario"] for t in e["fila"] if t.get("horario")}
    from .etapas import ler_trabalho  # o vídeo que está sendo feito agora também conta
    t = ler_trabalho()
    if t and t["tarefa"].get("horario"):
        ocupados.add(t["tarefa"]["horario"])
    return ocupados


def horarios_livres(e: dict, agora: datetime | None = None) -> list[datetime]:
    ocupados = horarios_ocupados(e)
    return [q for q in horarios_da_janela(agora) if _texto(q) not in ocupados]


def preparar_agenda(e: dict) -> int:
    """Põe na fila um vídeo para cada horário das próximas horas que ainda não tem vídeo."""
    novos = 0
    for quando in horarios_livres(e):
        novos += enfileirar(e, {"tipo": "novo", "horario": _texto(quando)})
    return novos


def prioridade(tarefa: dict) -> tuple:
    """Ordem de produção: refazer primeiro; depois o horário mais próximo; os pedidos avulsos
    (Reels, vídeo extra, teste) entram antes dos horários que ainda estão longe."""
    agora = estado.agora()
    if tarefa["tipo"] == "refazer":
        return (0, tarefa.get("horario") or "")
    if tarefa.get("horario"):
        perto = datetime.fromisoformat(tarefa["horario"]) - agora < timedelta(hours=3)
        return (1 if perto else 3, tarefa["horario"])
    return (2, "")


def aplicar(e: dict, pedido: dict) -> str:
    """Executa um pedido {acao, id, tema, ajuste}. Devolve uma frase curta sobre o resultado."""
    acao = (pedido.get("acao") or "").strip().lower()
    video_id = (pedido.get("id") or "").strip()
    tema = (pedido.get("tema") or "").strip()[:200]
    ajuste = (pedido.get("ajuste") or "").strip()[:500]
    video = estado.achar_video(video_id) if video_id else None

    if acao in ("produzir", "novo"):
        if not config.GEMINI_API_KEY:
            return "Falta cadastrar a chave GEMINI_API_KEY nos Secrets do GitHub."
        enfileirar(e, {"tipo": "extra", "tema": tema, "pedido": pedido.get("quando", "")})
        return f"Vídeo {'sobre ' + tema if tema else 'novo'} na fila."
    if acao == "continuar":  # a fábrica chamando a si mesma para o próximo pedido da fila
        return "Seguindo a fila."
    if acao == "teste":
        enfileirar(e, {"tipo": "teste"})
        return "Vídeo de teste na fila."
    if acao == "instagram":  # Reels da Clover: site-conceito de um segmento rolando no notebook
        tarefa = {"tipo": "instagram", "tema": tema, "ajuste": ajuste, "pedido": pedido.get("quando", "")}
        if not config.GEMINI_API_KEY or pedido.get("exemplo"):
            tarefa["exemplo"] = True
        enfileirar(e, tarefa)
        return f"Reels {'de ' + tema if tema else 'com segmento surpresa'} na fila."
    if not video:
        return f"Não achei o vídeo {video_id or '(sem id)'}."

    if acao == "refazer" and video.get("tipo") == "instagram":
        tarefa = {"tipo": "instagram", "tema": video.get("segmento", ""), "ajuste": ajuste, "origem": video["id"]}
        if not config.GEMINI_API_KEY or video.get("titulo", "").startswith("[TESTE]"):
            tarefa["exemplo"] = True
        enfileirar(e, tarefa)
        return f"Refazendo o Reels “{video['titulo']}”."
    if acao == "refazer":
        if not config.GEMINI_API_KEY and video.get("tipo") != "teste":
            return "Falta cadastrar a chave GEMINI_API_KEY nos Secrets do GitHub."
        tarefa = {"tipo": "teste"} if video.get("tipo") == "teste" else \
                 {"tipo": "refazer", "origem": video["id"], "ajuste": ajuste}
        if video.get("postar_em") and tarefa["tipo"] == "refazer":
            tarefa["horario"] = video["postar_em"]   # a versão nova fica no mesmo horário
        enfileirar(e, tarefa)
        return f"Refazendo “{video['titulo']}”."
    if acao == "aprovar":
        if video.get("status") not in ("aguardando", "aprovado"):
            return f"“{video['titulo']}” já está como {estado.STATUS.get(video.get('status'), video.get('status'))}."
        estado.atualizar_video(video["id"], status="aprovado", aprovado_em=estado.agora().isoformat(timespec="seconds"))
        if youtube.configurado():
            enfileirar(e, {"tipo": "publicar", "id": video["id"]})
            return f"“{video['titulo']}” aprovado; vai ser programado no YouTube."
        telegram.avisar_aprovado(estado.achar_video(video["id"]))
        return f"“{video['titulo']}” aprovado e pronto para postar."
    if acao == "descartar":
        estado.atualizar_video(video["id"], status="descartado")
        return f"“{video['titulo']}” descartado."
    if acao == "publicado":
        estado.atualizar_video(video["id"], status="publicado",
                               publicado_em=estado.agora().isoformat(timespec="seconds"))
        return f"“{video['titulo']}” marcado como publicado."
    return f"Ação desconhecida: {acao}"
