# -*- coding: utf-8 -*-
"""Geração, avaliação e refinamento de equipamentos."""
from . import dados as D

MULT_RARIDADE = [1.0, 1.15, 1.35, 1.6, 2.0]
N_AFIXOS = [0, 1, 1, 2, 3]
PESOS_RARIDADE = [60.0, 26.0, 10.0, 3.5, 0.5]
BONUS_REFINO = 0.06  # cada +1 de refino aumenta poder e afixos em 6%


def _escolher_raridade(rng, ilvl, chefe):
    pesos = []
    for i, p in enumerate(PESOS_RARIDADE):
        w = p * (1 + ilvl * 0.012 * i)
        if chefe and i < 2:
            w = 0.0
        pesos.append(w)
    return rng.choices(range(5), weights=pesos)[0]


def _poder_base(slot, ilvl, mult):
    if slot == "arma":
        return (3 + 1.6 * ilvl) * mult
    if slot == "armadura":
        return (2 + 1.5 * ilvl) * mult
    return (2 + 1.0 * ilvl) * mult


def _nome(rng, slot, raridade):
    base, genero = rng.choice(D.BASES_ITEM[slot])
    return _montar_nome(rng, base, genero, raridade)


def _montar_nome(rng, base, genero, raridade):
    adj = rng.choice(D.ADJETIVOS[raridade])[0 if genero == "m" else 1]
    nome = "%s %s" % (base, adj)
    if raridade >= 2:
        nome += " " + rng.choice(D.EPITETOS)
    return nome


def gerar_item(rng, slot, ilvl, chefe=False, raridade=None, nome_fixo=None):
    """Cria um item novo. 'nome_fixo' = (base, genero) usado no kit inicial."""
    if raridade is None:
        raridade = _escolher_raridade(rng, ilvl, chefe)
    mult = MULT_RARIDADE[raridade]
    afixos = {}
    n = N_AFIXOS[raridade]
    candidatos = list(D.ATRIBUTOS)
    rng.shuffle(candidatos)
    for attr in candidatos[:n]:
        afixos[attr] = round((0.5 + 0.2 * ilvl) * mult * rng.uniform(0.8, 1.2), 2)
    if nome_fixo:
        nome = "%s" % nome_fixo[0]
    else:
        nome = _nome(rng, slot, raridade)
    return {
        "slot": slot,
        "nome": nome,
        "raridade": raridade,
        "ilvl": int(ilvl),
        "poder": round(_poder_base(slot, ilvl, mult), 2),
        "afixos": afixos,
        "refino": 0,
    }


def fator_refino(item):
    return 1.0 + BONUS_REFINO * item.get("refino", 0)


def poder(item):
    return item["poder"] * fator_refino(item)


def afixos(item):
    f = fator_refino(item)
    return {a: v * f for a, v in item["afixos"].items()}


def valor(item):
    """Pontuação usada para decidir se um item novo substitui o equipado."""
    return poder(item) + 1.5 * sum(afixos(item).values())


def custo_refino(item):
    r = item["refino"]
    return int(6 + 4 * (r + 1) ** 1.5 + item["ilvl"] * 1.2)


def chance_refino(item, bonus_maestria):
    return max(0.30, min(0.98, 0.95 - 0.06 * item["refino"] + bonus_maestria))


def fragmentos_ao_desmontar(item):
    return int(2 + item["ilvl"] * 0.5 * (1 + item["raridade"] * 0.5))


def rotulo(item):
    r = item.get("refino", 0)
    return "%s%s" % (item["nome"], (" +%d" % r) if r else "")


def descricao_curta(item):
    if not item:
        return "(vazio)"
    return "%s [%s]" % (rotulo(item), D.RARIDADES[item["raridade"]])
