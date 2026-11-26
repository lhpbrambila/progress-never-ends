# -*- coding: utf-8 -*-
"""Geração, avaliação e refinamento de equipamentos, conjuntos e itens únicos."""
from . import dados as D
from . import dados_itens as DI
from .util import fmt_dec

CHAVES_EFEITO = list(DI.NOMES_EFEITO)

MULT_RARIDADE = [1.0, 1.15, 1.35, 1.6, 2.0]
N_AFIXOS = [0, 1, 1, 2, 3]
N_MODS = [0, 0, 1, 2, 3]
PESOS_RARIDADE = [60.0, 26.0, 10.0, 3.5, 0.5]
CHANCE_CONJUNTO = 0.22
CUSTO_CRESC = 0.1       # quanto o custo do refino cresce com o grau (cúbico)
DESMONTE_K = 0.05       # fragmentos por nível de item ao desmontar


# ---------------------------------------------------------------- efeitos
def somar(destino, origem, mult=1.0):
    for k, v in origem.items():
        destino[k] = destino.get(k, 0.0) + v * mult
    return destino


def pct(v):
    x = v * 100
    if abs(x - round(x)) < 0.05:
        return "%d%%" % round(x)
    return fmt_dec(x, 1) + "%"


def descrever_efeito(chave, v):
    return "+%s %s" % (pct(v), DI.NOMES_EFEITO[chave])


def descrever_efeitos(efeitos):
    return "; ".join(descrever_efeito(k, v) for k, v in efeitos.items() if v)


# -------------------------------------------------------------- construção
def _escolher_raridade(rng, ilvl, chefe, elite=0):
    pesos = []
    nivel = min(ilvl, 400)
    for i, p in enumerate(PESOS_RARIDADE):
        w = p * (1 + nivel * 0.012 * i) * (1 + 0.5 * elite * i)
        if chefe and i < 2:
            w = 0.0
        pesos.append(w)
    return rng.choices(range(5), weights=pesos)[0]


def _montar(rng, slot, ilvl, raridade, nome):
    mult = MULT_RARIDADE[raridade]
    base, por_nivel = DI.PODER_SLOT[slot]
    item = {
        "slot": slot, "nome": nome, "raridade": raridade, "ilvl": int(ilvl),
        "poder": round((base + por_nivel * ilvl) * mult, 2),
        "afixos": {}, "mods": [], "refino": 0,
    }
    atributos = list(D.ATRIBUTOS)
    rng.shuffle(atributos)
    for attr in atributos[:N_AFIXOS[raridade]]:
        item["afixos"][attr] = round((0.5 + 0.2 * ilvl) * mult * rng.uniform(0.8, 1.2), 2)
    return item


def _sortear_mods(rng, slot, raridade):
    candidatos = [k for k, m in DI.MODS.items() if slot in m["slots"]]
    rng.shuffle(candidatos)
    escala = 1 + 0.25 * (raridade - 2)
    return [{"id": k, "v": round(DI.MODS[k]["base"] * rng.uniform(0.8, 1.2) * escala, 4)}
            for k in candidatos[:N_MODS[raridade]]]


def _nome(rng, slot, raridade):
    base, genero = rng.choice(D.BASES_ITEM[slot])
    adj = rng.choice(D.ADJETIVOS[raridade])[0 if genero == "m" else 1]
    nome = "%s %s" % (base, adj)
    if raridade >= 2:
        nome += " " + rng.choice(D.EPITETOS)
    return nome


def gerar_item(rng, slot, ilvl, chefe=False, raridade=None, nome_fixo=None, elite=0):
    """Item comum gerado aleatoriamente. 'nome_fixo' = (nome, gênero) usado em kits iniciais."""
    if raridade is None:
        raridade = _escolher_raridade(rng, ilvl, chefe, elite)
    nome = nome_fixo[0] if nome_fixo else _nome(rng, slot, raridade)
    item = _montar(rng, slot, ilvl, raridade, nome)
    if raridade >= 2:
        item["mods"] = _sortear_mods(rng, slot, raridade)
        if not nome_fixo:
            item["lore"] = rng.randrange(len(DI.LORE_ITEM[slot]))
    return item


def item_inicial(rng, slot, ilvl=1):
    return _montar(rng, slot, max(1, ilvl), 0, DI.INICIAIS[slot])


def gerar_peca_conjunto(rng, sid, slot, ilvl, raridade):
    raridade = max(2, raridade)
    item = _montar(rng, slot, ilvl, raridade, DI.SETS[sid]["pecas"][slot])
    item["mods"] = _sortear_mods(rng, slot, raridade)
    item["conjunto"] = sid
    return item


def gerar_unico(rng, uid, ilvl):
    u = DI.UNICOS[uid]
    item = _montar(rng, u["slot"], ilvl, 4, u["nome"])
    item["unico"] = uid
    return item


def sortear_loot(rng, ilvl, chefe=False, regiao=0, elite=0, raridade_min=0):
    """Item caído de um inimigo. Itens raros ou melhores podem ser peças do conjunto da região."""
    slot = rng.choices(list(DI.PESO_SLOT), weights=list(DI.PESO_SLOT.values()))[0]
    raridade = max(raridade_min, _escolher_raridade(rng, ilvl, chefe, elite))
    sid = DI.SET_POR_REGIAO[min(regiao, len(DI.SET_POR_REGIAO) - 1)]
    if raridade >= 2 and rng.random() < CHANCE_CONJUNTO:
        return gerar_peca_conjunto(rng, sid, rng.choice(list(DI.SETS[sid]["pecas"])), ilvl, raridade)
    return gerar_item(rng, slot, ilvl, raridade=raridade)


# --------------------------------------------------------------- avaliação
def fator_refino(item):
    r = item.get("refino", 0)
    return 1.0 + 0.06 * min(r, 12) + 0.03 * max(0, r - 12)


def poder(item):
    return item["poder"] * fator_refino(item)


def afixos(item):
    f = fator_refino(item)
    return {a: v * f for a, v in item["afixos"].items()}


def efeitos_item(item):
    """Efeitos percentuais de um item: afixos nomeados (com refino) e efeito do item único."""
    ef = {}
    f = fator_refino(item)
    for m in item.get("mods", []):
        k = DI.MODS[m["id"]]["efeito"]
        ef[k] = ef.get(k, 0.0) + m["v"] * f
    if item.get("unico"):
        somar(ef, DI.UNICOS[item["unico"]]["efeito"])
    return ef


def contagem_conjuntos(equip):
    cont = {}
    for it in equip.values():
        if it and it.get("conjunto"):
            cont[it["conjunto"]] = cont.get(it["conjunto"], 0) + 1
    return cont


def efeitos_conjuntos(equip):
    ef = {}
    for sid, n in contagem_conjuntos(equip).items():
        for pecas, bonus in DI.SETS[sid]["bonus"].items():
            if n >= pecas:
                somar(ef, bonus)
    return ef


def efeitos_equipamento(equip):
    ef = {}
    for it in equip.values():
        if it:
            somar(ef, efeitos_item(it))
    somar(ef, efeitos_conjuntos(equip))
    return ef


def resumo_conjuntos(equip):
    """Lista de conjuntos com ao menos uma peça equipada, para exibição."""
    saida = []
    for sid, n in contagem_conjuntos(equip).items():
        s = DI.SETS[sid]
        saida.append({
            "id": sid, "nome": s["nome"], "n": n, "total": len(s["pecas"]), "lore": s["lore"],
            "bonus": [(p, b, n >= p) for p, b in sorted(s["bonus"].items())],
        })
    return saida


def valor(item):
    """Pontuação usada para decidir se um item novo substitui o equipado."""
    v = poder(item) + 1.5 * sum(afixos(item).values())
    v += sum(m["v"] for m in item.get("mods", [])) * (4 * item["ilvl"] + 40)
    if item.get("conjunto"):
        v += 0.25 * poder(item)
    if item.get("unico"):
        v += 0.6 * poder(item)
    return v


# ------------------------------------------------------------------- refino
def custo_refino(item):
    r = item["refino"]
    return int((6 + item["ilvl"] * 1.2) * (1 + CUSTO_CRESC * (r + 1) ** 3))


def chance_refino(item, bonus_maestria):
    return max(0.08, min(0.98, 0.95 - 0.05 * item["refino"] + bonus_maestria))


def fragmentos_ao_desmontar(item):
    return int(2 + item["ilvl"] * DESMONTE_K * (1 + item["raridade"] * 0.5))


# ------------------------------------------------------------------ exibição
def rotulo(item):
    r = item.get("refino", 0)
    return "%s%s" % (item["nome"], (" +%d" % r) if r else "")


def rotulo_raridade(item):
    if item.get("unico"):
        return "Único"
    nome = D.RARIDADES[item["raridade"]]
    if item.get("conjunto"):
        nome += ", Conjunto"
    return nome


def descricao_curta(item):
    if not item:
        return "(vazio)"
    return "%s [%s]" % (rotulo(item), rotulo_raridade(item))


def poder_exibido(item):
    """(rótulo, valor) do poder principal do item, como mostrado ao jogador."""
    mult = 2.5 if item["slot"] == "reliquia" else 1.0
    return DI.ROTULO_PODER[item["slot"]], poder(item) * mult


def lore_item(item):
    """Texto narrativo do item (único, conjunto ou genérico), ou None."""
    if item.get("unico"):
        return DI.UNICOS[item["unico"]]["lore"]
    if item.get("conjunto"):
        return DI.SETS[item["conjunto"]]["lore"]
    i = item.get("lore")
    if i is not None:
        return DI.LORE_ITEM[item["slot"]][i % len(DI.LORE_ITEM[item["slot"]])]
    return None


def linhas_mods(item):
    """Uma descrição por afixo nomeado ou efeito único: 'Crueldade: +4% de dano'."""
    linhas = []
    f = fator_refino(item)
    for m in item.get("mods", []):
        d = DI.MODS[m["id"]]
        linhas.append("%s: %s" % (d["nome"], descrever_efeito(d["efeito"], m["v"] * f)))
    if item.get("unico"):
        linhas.append("Efeito único: %s" % descrever_efeitos(DI.UNICOS[item["unico"]]["efeito"]))
    return linhas
