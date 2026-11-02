"""Ações sobre os vídeos, venham elas do painel, do Telegram ou do botão "Run workflow" do GitHub."""
from . import config, estado, telegram, youtube

TAREFAS_DE_PRODUCAO = ("novo", "extra", "refazer", "teste", "instagram")


def enfileirar(e: dict, tarefa: dict) -> bool:
    """Põe a tarefa na fila se ela ainda não estiver lá. Devolve True se entrou."""
    if tarefa in e["fila"]:
        return False
    e["fila"].append(tarefa)
    return True


def video_do_dia_pendente(e: dict) -> bool:
    agora = estado.agora()
    previstos = sum(1 for h in config.HORARIOS if agora.hour >= h)
    feitos = sum(1 for v in estado.historico()
                 if v.get("tipo") == "novo" and v.get("data", "")[:10] == estado.hoje())
    na_fila = sum(1 for t in e["fila"] if t["tipo"] == "novo")
    return feitos + na_fila < previstos


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
        tipo = "novo" if video_do_dia_pendente(e) else "extra"
        enfileirar(e, {"tipo": tipo, "tema": tema})
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
