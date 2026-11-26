# -*- coding: utf-8 -*-
"""Escolha automática e efeitos dos talentos por vocação."""
from . import dados_talentos as DT
from .itens import somar

RANK_MAX = DT.RANK_MAX


def caminhos(classe):
    """Lista de (id, nome, descrição) dos caminhos da vocação. O primeiro é o padrão."""
    return [(k, c["nome"], c["desc"]) for k, c in DT.TALENTOS[classe]["caminhos"].items()]


def caminho_padrao(classe):
    return next(iter(DT.TALENTOS[classe]["caminhos"]))


def caminho_valido(classe, caminho):
    return caminho if caminho in DT.TALENTOS[classe]["caminhos"] else caminho_padrao(classe)


def definicao(classe, talento):
    return DT.TALENTOS[classe]["talentos"][talento]


def proximo(classe, caminho, talentos):
    """Talento que o caminho escolheria agora (equilibra prioridade e graus já obtidos)."""
    prioridade = DT.TALENTOS[classe]["caminhos"][caminho_valido(classe, caminho)]["prioridade"]
    melhor = None
    for tid, peso in prioridade.items():
        r = talentos.get(tid, 0)
        if r >= RANK_MAX:
            continue
        score = peso / (r + 1)
        if melhor is None or score > melhor[0]:
            melhor = (score, tid)
    return melhor[1] if melhor else None


def efeitos(classe, talentos):
    ef = {}
    for tid, r in talentos.items():
        if tid in DT.TALENTOS[classe]["talentos"]:
            somar(ef, DT.TALENTOS[classe]["talentos"][tid]["efeito"], r)
    return ef


def total(talentos):
    return sum(talentos.values())
