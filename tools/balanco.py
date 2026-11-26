# -*- coding: utf-8 -*-
"""Simula anos de jogo sem interface para conferir o ritmo de progressão.

Uso (a partir da pasta do projeto):
    python tools/balanco.py                        # todas as vocações, 3 anos
    python tools/balanco.py --classe monge --anos 5
    python tools/balanco.py --passo 4              # passo maior = mais rápido e menos preciso

Mostra, em marcos de tempo, nível, região, ciclo, abates por hora, recuos, talentos, refino
médio, fatia do tempo em cada atividade e se o herói segue evoluindo (sem travar).
"""
import argparse
import importlib
import multiprocessing as mp
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import criacao, dados as D  # noqa: E402
from core.motor import Motor  # noqa: E402

MARCOS_H = [("1 dia", 24), ("3 dias", 72), ("1 sem", 168), ("2 sem", 336), ("1 mês", 720),
            ("3 meses", 2160), ("6 meses", 4380), ("1 ano", 8760), ("2 anos", 17520),
            ("3 anos", 26280), ("5 anos", 43800), ("10 anos", 87600)]


def aplicar_ajustes(ajustes):
    """'motor.XP_C=20' -> core.motor.XP_C = 20.0 (para testar constantes sem editar o código)."""
    for ajuste in ajustes or []:
        alvo, valor = ajuste.split("=")
        modulo, nome = alvo.split(".")
        setattr(importlib.import_module("core." + modulo), nome, float(valor))


def simular(args):
    classe, anos, passo, semente, ajustes = args
    aplicar_ajustes(ajustes)
    rng = random.Random(semente)
    origem = rng.choice(list(D.ORIGENS))
    attrs = criacao.aplicar_origem(criacao.rolar_atributos(rng, classe), origem)
    m = Motor.novo("Teste", origem, classe, attrs, semente=semente)
    m.silencioso = True
    total = anos * 8760 * 3600
    marcos = [(r, h * 3600) for r, h in MARCOS_H if h * 3600 <= total]
    linhas = []
    t = 0.0
    ult = {"t": 0.0, "abates": 0, "recuos": 0}
    fases = {}
    prox = 0
    while t < total:
        m.avancar(passo, passo=passo)
        t += passo
        fases[m.s["fase"]] = fases.get(m.s["fase"], 0) + 1
        if prox < len(marcos) and t >= marcos[prox][1]:
            st = m.s["stats"]
            horas = (t - ult["t"]) / 3600
            soma = sum(fases.values()) or 1
            eq = m.p["equip"]
            refino = sum(i["refino"] for i in eq.values()) / len(eq)
            linhas.append((marcos[prox][0], m.p["nivel"], m.s["regiao"], m.s["ciclo"],
                           (st["abates"] - ult["abates"]) / horas, st["recuos"] - ult["recuos"],
                           sum(m.p["talentos"].values()), refino,
                           100 * fases.get("forja", 0) / soma, 100 * fases.get("combate", 0) / soma,
                           100 * fases.get("recuperacao", 0) / soma,
                           sum(x["nivel"] for x in m.p["maestrias"].values()) / len(m.p["maestrias"]),
                           m.derivados()["pv_max"], m.derivados()["dano"]))
            ult = {"t": t, "abates": st["abates"], "recuos": st["recuos"]}
            fases = {}
            prox += 1
    return classe, linhas


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classe", choices=list(D.CLASSES))
    ap.add_argument("--anos", type=float, default=3)
    ap.add_argument("--passo", type=float, default=3.0)
    ap.add_argument("--semente", type=int, default=1)
    ap.add_argument("--set", action="append", dest="ajustes", metavar="MOD.NOME=VALOR",
                    help="sobrescreve uma constante, ex.: --set motor.XP_C=25 --set itens.CUSTO_CRESC=0.05")
    a = ap.parse_args()
    classes = [a.classe] if a.classe else list(D.CLASSES)
    with mp.Pool(min(len(classes), os.cpu_count() or 1)) as pool:
        resultados = pool.map(simular, [(c, a.anos, a.passo, a.semente, a.ajustes) for c in classes])
    cab = "%-8s %5s %3s %3s %8s %6s %4s %6s %6s %6s %6s %5s %9s %8s"
    print(cab % ("marco", "nível", "reg", "cic", "abates/h", "recuos", "tal.", "refino",
                 "%forja", "%comb", "%desc", "maest", "PV máx", "dano"))
    for classe, linhas in resultados:
        print("\n== %s" % D.CLASSES[classe]["nome"])
        for l in linhas:
            print("%-8s %5d %3d %3d %8.0f %6d %4d %6.1f %6.1f %6.1f %6.1f %5.1f %9.0f %8.0f" % l)


if __name__ == "__main__":
    principal()
