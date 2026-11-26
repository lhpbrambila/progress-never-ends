# -*- coding: utf-8 -*-
"""Eventos de jornada: escolha da opção, teste de atributo e aplicação dos efeitos."""
from . import dados as D
from . import dados_eventos as DE
from . import itens as I
from .util import limitar

FRAG_BASE = 2.0


def chance_sucesso(atributo, nivel, dif):
    """Chance de êxito: relaciona o atributo do herói ao nível do desafio."""
    ref = (6 + nivel) * dif
    return limitar(0.15 + 0.80 * atributo / (atributo + ref), 0.10, 0.95)


def sortear(rng, regiao):
    elegiveis = [e for e in DE.EVENTOS if e["regioes"] is None or regiao in e["regioes"]]
    return rng.choices(elegiveis, weights=[e["peso"] for e in elegiveis])[0]


def melhor_opcao(motor, evento, nivel):
    """A opção em que o herói tem mais chance de êxito (escolha automática pela vocação)."""
    A = motor.derivados()["atributos"]
    return max(evento["opcoes"], key=lambda o: chance_sucesso(A[o["attr"]], nivel, o["dif"]))


def ganho_fragmentos(motor, nivel, mult):
    from .motor import FRAG_POR_NIVEL
    return int((FRAG_BASE + FRAG_POR_NIVEL * nivel) * mult * (1 + motor.derivados()["fragmentos_pct"]))


def aplicar_efeitos(motor, efeitos, nivel):
    """Aplica os efeitos de um resultado. Retorna True se o herói subiu de nível."""
    s, p = motor.s, motor.p
    d = motor.derivados()
    subiu = False
    for chave, v in efeitos.items():
        if chave == "xp":
            from .motor import stats_inimigo
            xp = int(stats_inimigo(nivel, s["ciclo"])["xp"] * v * (1 + d["xp_pct"]))
            subiu = motor._ganhar_xp(xp) or subiu
        elif chave == "fragmentos":
            p["fragmentos"] += ganho_fragmentos(motor, nivel, v)
        elif chave == "cura":
            p["pv"] = min(d["pv_max"], p["pv"] + d["pv_max"] * v)
        elif chave == "dano":
            dano = d["pv_max"] * v
            p["pv"] = max(1.0, p["pv"] - dano)
            s["stats"]["dano_sofrido"] += dano
        elif chave == "fadiga":
            p["fadiga"] = limitar(p["fadiga"] + v, 0.0, 100.0)
        elif chave == "perda_fragmentos":
            p["fragmentos"] = int(p["fragmentos"] * (1 - v))
        elif chave == "maestria":
            motor._xp_maestria(v[0], v[1])
        elif chave == "item":
            motor._receber_item(I.sortear_loot(motor.rng, nivel, regiao=s["regiao"], raridade_min=int(v)))
    return subiu


def resolver(motor):
    """Sorteia e resolve um evento. Retorna True se o herói subiu de nível."""
    s, rng = motor.s, motor.rng
    nivel = max(1, motor._nivel_inimigo())
    ev = sortear(rng, s["regiao"])
    op = melhor_opcao(motor, ev, nivel)
    chance = chance_sucesso(motor.derivados()["atributos"][op["attr"]], nivel, op["dif"])
    sucesso = rng.random() < chance
    resultado = op["ok"] if sucesso else op["falha"]
    motor.registrar("evento", ev["intro"])
    motor.registrar("evento", op["acao"])
    motor.registrar("evento", resultado["texto"])
    s["stats"]["eventos_ok" if sucesso else "eventos_falha"] += 1
    return aplicar_efeitos(motor, resultado["efeitos"], nivel)
