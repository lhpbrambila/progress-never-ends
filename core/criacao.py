# -*- coding: utf-8 -*-
"""Criação de personagem: rolagem, distribuição manual e criação rápida."""
import random

from . import dados as D

BASE_ATRIBUTO = 8
PONTOS_DISTRIBUIVEIS = 20
MAX_ATRIBUTO_INICIAL = 18


def _4d6_descarta_menor(rng):
    dados = sorted(rng.randint(1, 6) for _ in range(4))
    return sum(dados[1:])


def rolar_atributos(rng, classe):
    """Rola cinco valores (4d6, descarta o menor) e os atribui por prioridade da classe."""
    valores = sorted((_4d6_descarta_menor(rng) for _ in range(5)), reverse=True)
    ordem = sorted(D.ATRIBUTOS, key=lambda a: -D.CLASSES[classe]["pesos"][a])
    return dict(zip(ordem, valores))


def distribuicao_inicial():
    return {a: BASE_ATRIBUTO for a in D.ATRIBUTOS}


def validar_distribuicao(attrs):
    """Retorna (ok, mensagem) para uma distribuição manual de pontos."""
    total = sum(attrs.values())
    esperado = BASE_ATRIBUTO * len(D.ATRIBUTOS) + PONTOS_DISTRIBUIVEIS
    for a in D.ATRIBUTOS:
        v = attrs.get(a)
        if v is None or v < BASE_ATRIBUTO or v > MAX_ATRIBUTO_INICIAL:
            return False, "Cada atributo deve ficar entre %d e %d." % (BASE_ATRIBUTO, MAX_ATRIBUTO_INICIAL)
    if total != esperado:
        return False, "Distribua exatamente %d pontos (restam %d)." % (
            PONTOS_DISTRIBUIVEIS, esperado - total)
    return True, ""


def aplicar_origem(attrs, origem):
    final = dict(attrs)
    for a, b in D.ORIGENS[origem]["bonus"].items():
        final[a] += b
    return final


def criacao_rapida(rng=None, nome=None, origem=None, classe=None):
    rng = rng or random.Random()
    origem = origem or rng.choice(list(D.ORIGENS))
    classe = classe or rng.choice(list(D.CLASSES))
    nome = nome or rng.choice(D.NOMES_SUGERIDOS)
    attrs = rolar_atributos(rng, classe)
    return nome, origem, classe, attrs
