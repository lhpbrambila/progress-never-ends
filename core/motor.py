# -*- coding: utf-8 -*-
"""Motor de simulação idle de A Última Vigília.

O estado inteiro vive em um dicionário serializável (``Motor.s``). A simulação avança por
tempo (``avancar(dt)``), em passos curtos e fixos, de modo que o resultado independe da
velocidade da máquina ou da taxa de quadros da interface.

O herói nunca morre: quando o perigo supera suas forças ele recua, descansa e volta. O ritmo
de progressão foi calibrado para durar anos com o mesmo personagem (ver tools/balanco.py).
"""
import random
import time

from . import dados as D
from . import dados_inimigos as DN
from . import dados_itens as DI
from . import eventos as EV
from . import itens as I
from . import talentos as T
from .util import fmt_duracao, limitar

FASES = {
    "marcha": "Marchando pela Região",
    "combate": "Em Combate",
    "recuperacao": "Recuperando Forças",
    "forja": "Forjando e Aprimorando",
    "consolidacao": "Consolidando Patamar",
}

DURACAO_FORJA = 4.0
DURACAO_CONSOLIDACAO = 3.0
LIMITE_CRONICA = 300
OFFLINE_MAX_S = 24 * 3600     # teto do progresso offline contabilizado
OFFLINE_MIN_S = 60            # abaixo disso, retoma sem relatório
CATEGORIAS_SEMPRE = ("marco", "alerta", "relato")

# ---- ritmo da progressão (ajustável; veja tools/balanco.py)
XP_C = 20.0                   # XP para o nível n: XP_C * n ** XP_A
XP_A = 3.0
FRAG_POR_NIVEL = 0.05         # fragmentos por abate = (1..3) + nível * FRAG_POR_NIVEL
ESFORCO_CICLO = 0.12          # cada volta da Roda deixa os inimigos 12% mais fortes
INIMIGO_HP_K, INIMIGO_HP_EXP = 30.0, 1.5      # vitalidade do inimigo = K * nível ** EXP
INIMIGO_DANO_K, INIMIGO_DANO_EXP = 3.0, 1.1   # dano por golpe = 4 + K * nível ** EXP
CHEFE_HP, CHEFE_DANO = 3.0, 1.0               # multiplicadores dos guardiões
CHEFE_CRESC = 0.01                            # guardiões ficam mais duros com o nível do herói
CHEFE_CRESC_MAX = 2.0
# O mundo reage ao excedente de poder do herói (maestrias, talentos, refino) além do esperado
# para o nível: assim o perigo se mantém por anos, sem o herói virar intocável.
REF_DANO, REF_PV, ADAPT_EXP = 16.0, 60.0, 0.8
TALENTO_A_CADA = 5            # um talento a cada 5 níveis (mais um por guardião inédito)


def xp_proximo_nivel(nivel):
    return int(XP_C * nivel ** XP_A)


def xp_proxima_maestria(nivel):
    return 12 * 1.2 ** (nivel - 1)


def stats_inimigo(nivel, ciclo=0):
    """Valores base de um inimigo de determinado nível, antes dos multiplicadores do tipo."""
    f = 1 + ESFORCO_CICLO * ciclo
    return {
        "hp": INIMIGO_HP_K * nivel ** INIMIGO_HP_EXP * f,
        "dano": (4 + INIMIGO_DANO_K * nivel ** INIMIGO_DANO_EXP) * f,
        "xp": 9 * nivel ** 1.25,
    }


def novo_estado(nome, origem, classe, atributos, caminho=None, agora=None):
    """Monta o estado de uma jornada nova. 'atributos' já inclui o bônus de origem."""
    agora = agora or time.time()
    rng = random.Random()
    cl = D.CLASSES[classe]
    equip = {"arma": I.gerar_item(rng, "arma", 1, raridade=0, nome_fixo=cl["arma"])}
    for slot in D.SLOTS:
        if slot != "arma":
            equip[slot] = I.item_inicial(rng, slot, 1)
    return {
        "versao": 2,
        "criado_em": agora,
        "salvo_em": agora,
        "tempo_jogado": 0.0,
        "personagem": {
            "nome": nome, "origem": origem, "classe": classe,
            "caminho": T.caminho_valido(classe, caminho),
            "nivel": 1, "xp": 0.0,
            "atributos": dict(atributos),
            "pv": 1.0, "fadiga": 0.0, "fragmentos": 0,
            "equip": equip,
            "maestrias": {k: {"nivel": 1, "xp": 0.0} for k in D.MAESTRIAS},
            "talentos": {},
        },
        "regiao": 0, "ciclo": 0, "progresso": 0.0, "recuos_seguidos": 0,
        "fase": "marcha", "fase_t": 0.0,
        "inimigo": None, "t_jogador": 0.0, "t_inimigo": 0.0, "cd_tecnica": cl["tecnica"]["cd"],
        "veneno": None, "prox_evento": 120.0, "unicos": [], "afixos_vistos": [],
        "forja_slot": None, "nivelou": False,
        "marcos": [], "cronica": [], "cron_n": 0,
        "stats": {
            "abates": 0, "chefes": 0, "leguas": 0.0, "recuos": 0, "itens": 0, "desmontados": 0,
            "refinos_ok": 0, "refinos_falha": 0, "dano_causado": 0.0, "dano_sofrido": 0.0,
            "criticos": 0, "perigos": 0, "maior_golpe": 0.0,
            "eventos_ok": 0, "eventos_falha": 0, "elites": 0, "unicos": 0,
        },
    }


class Motor:
    def __init__(self, estado, semente=None):
        self.s = estado
        self.rng = random.Random(semente)
        self.silencioso = False
        self._der = None
        self._ef = None
        self._normalizar()
        p = self.s["personagem"]
        if p["pv"] <= 1.0 and not self.s["cronica"]:
            p["pv"] = self.derivados()["pv_max"]

    # ------------------------------------------------------------ construção
    @classmethod
    def novo(cls, nome, origem, classe, atributos, semente=None, caminho=None):
        s = novo_estado(nome, origem, classe, atributos, caminho)
        m = cls(s, semente)
        m.registrar("marco", D.TEXTOS["inicio"].format(
            nome=nome, origem=D.ORIGENS[origem]["nome"], classe=D.CLASSES[classe]["nome"]))
        m.registrar("info", D.TEXTOS["chegada"].format(regiao=D.REGIOES[0]["nome"], desc=D.REGIOES[0]["desc"]))
        return m

    def _normalizar(self):
        """Completa campos que saves de versões anteriores não tinham (migração idempotente)."""
        s, p = self.s, self.s["personagem"]
        s["versao"] = 2
        p["caminho"] = T.caminho_valido(p["classe"], p.get("caminho"))
        p.setdefault("talentos", {})
        for slot in D.SLOTS:
            if not p["equip"].get(slot):
                p["equip"][slot] = I.item_inicial(self.rng, slot, p["nivel"])
        for k in D.MAESTRIAS:
            p["maestrias"].setdefault(k, {"nivel": 1, "xp": 0.0})
        s.setdefault("veneno", None)
        s.setdefault("prox_evento", s["tempo_jogado"] + 120.0)
        s.setdefault("unicos", [])
        s.setdefault("afixos_vistos", [])
        for k in ("eventos_ok", "eventos_falha", "elites", "unicos"):
            s["stats"].setdefault(k, 0)
        e = s.get("inimigo")
        if e:
            e.setdefault("afixos", [])
            e.setdefault("fases", [])
            e.setdefault("escudo", 0.0)
            e.setdefault("dot", None)
            e.setdefault("base", e["nome"])
        # talentos devidos pelo nível e pelos guardiões já derrotados
        esperado = p["nivel"] // TALENTO_A_CADA + sum(1 for m in s["marcos"] if m["id"].startswith("guardiao_"))
        faltam = esperado - T.total(p["talentos"])
        if faltam > 0:
            antigo, self.silencioso = self.silencioso, True
            for _ in range(faltam):
                self._conceder_talento()
            self.silencioso = antigo
        self.invalidar()

    # --------------------------------------------------------------- crônica
    def registrar(self, cat, texto):
        if self.silencioso and cat not in CATEGORIAS_SEMPRE:
            return
        s = self.s
        s["cron_n"] += 1
        s["cronica"].append({"n": s["cron_n"], "t": round(s["tempo_jogado"], 1), "c": cat, "m": texto})
        if len(s["cronica"]) > LIMITE_CRONICA:
            del s["cronica"][: len(s["cronica"]) - LIMITE_CRONICA]

    # -------------------------------------------------------------- consultas
    @property
    def p(self):
        return self.s["personagem"]

    def regiao_atual(self):
        return D.REGIOES[self.s["regiao"]]

    def nome_regiao(self):
        n = self.regiao_atual()["nome"]
        c = self.s["ciclo"]
        return n if c == 0 else "%s (Ciclo %d)" % (n, c + 1)

    def invalidar(self):
        self._der = None
        self._ef = None

    def atributos_totais(self):
        tot = dict(self.p["atributos"])
        for it in self.p["equip"].values():
            if it:
                for a, v in I.afixos(it).items():
                    tot[a] += v
        return tot

    def efeitos_totais(self):
        """Soma de todos os bônus percentuais: maestrias, equipamentos, conjuntos e talentos."""
        if self._ef is None:
            p = self.p
            ef = {k: 0.0 for k in I.CHAVES_EFEITO}
            for k, m in p["maestrias"].items():
                defn = D.MAESTRIAS[k]
                ef[defn["efeito"]] += (m["nivel"] - 1) * defn["por_nivel"]
            I.somar(ef, I.efeitos_equipamento(p["equip"]))
            I.somar(ef, T.efeitos(p["classe"], p["talentos"]))
            self._ef = ef
        return self._ef

    def derivados(self):
        if self._der is not None:
            return self._der
        p = self.p
        L = p["nivel"]
        A = self.atributos_totais()
        ef = self.efeitos_totais()
        cl = D.CLASSES[p["classe"]]
        eq = p["equip"]

        def pw(slot):
            return I.poder(eq[slot]) if eq.get(slot) else 0.0

        arma, armadura, elmo, botas, anel, reliquia = (pw(s) for s in D.SLOTS)
        principal = A[cl["principal"]]
        self._der = {
            "atributos": A,
            "pv_max": (60 + A["vitalidade"] * 10 + L * 8 + reliquia * 2.5) * (1 + ef["pv_pct"]),
            "dano": (principal * 1.3 + arma + L * 1.5) * (1 + ef["dano_pct"]),
            "defesa": (armadura + elmo * 0.9 + botas * 0.4 + A["vitalidade"] * 0.6
                       + A["vontade"] * 0.4 + L) * (1 + ef["defesa_pct"]),
            "acerto": min(0.97, 0.80 + A["destreza"] * 0.0015 + ef["precisao"]),
            "crit": min(0.60, 0.04 + A["destreza"] * 0.0012 + A["intelecto"] * 0.0008 + ef["crit"]
                        + 0.25 * anel / (anel + 30 + 4 * L)),
            "crit_mult": 1.75 + ef["crit_dano"],
            "esquiva": min(0.50, 0.10 + 0.20 * botas / (botas + 30 + 5 * L) + ef["esquiva"]),
            "ciclo": max(0.6, 1.9 - A["destreza"] * 0.01 - L * 0.004),
            "regen": (0.045 + A["vontade"] * 0.0005) * (1 + ef["regen_pct"]),
            "resist": 1 + A["vontade"] * 0.012 + ef["fadiga_red"],
            "vel_marcha": 3.0 / (1 + A["destreza"] * 0.004) / (1 + ef["vel_marcha_pct"]),
            "forja": ef["forja"],
            "tecnica_pct": ef["tecnica_pct"],
            "dano_pct": ef["dano_pct"],
            "dano_chefe_pct": ef["dano_chefe_pct"],
            "roubo_vida": ef["roubo_vida"],
            "resist_veneno": min(0.90, ef["resist_veneno"]),
            "reducao_dano": min(0.50, ef["reducao_dano"]),
            "xp_pct": ef["xp_pct"],
            "fragmentos_pct": ef["fragmentos_pct"],
        }
        return self._der

    def info_fase(self):
        """(rótulo, fração 0..1, detalhe) da atividade atual, para as interfaces."""
        s = self.s
        f = s["fase"]
        d = self.derivados()
        rotulo = FASES[f]
        if f == "marcha":
            reg = self.regiao_atual()
            frac = limitar(s["fase_t"] / d["vel_marcha"], 0, 1)
            det = "%s: %d/%d léguas" % (self.nome_regiao(), int(s["progresso"]), reg["extensao"])
        elif f == "combate":
            e = s["inimigo"]
            frac = limitar(e["hp"] / e["hp_max"], 0, 1) if e else 0.0
            if e:
                det = "%s (nível %d) %d/%d" % (e["nome"], e["nivel"], max(0, int(e["hp"])), int(e["hp_max"]))
                if e.get("escudo", 0) > 0:
                    det += " | escudo %d" % int(e["escudo"])
                if s.get("veneno"):
                    det += " | envenenado"
            else:
                det = ""
        elif f == "recuperacao":
            frac = limitar(self.p["pv"] / d["pv_max"], 0, 1)
            det = "Vitalidade e fôlego retornam aos poucos"
        elif f == "forja":
            frac = limitar(s["fase_t"] / DURACAO_FORJA, 0, 1)
            it = self.p["equip"].get(s["forja_slot"])
            det = "Refinando %s" % I.rotulo(it) if it else ""
        else:
            frac = limitar(s["fase_t"] / DURACAO_CONSOLIDACAO, 0, 1)
            det = "Os novos limites do corpo se assentam"
        return rotulo, frac, det

    # ------------------------------------------------------------- avanço
    def avancar(self, dt, passo=0.25):
        restante = dt
        while restante > 1e-9:
            h = min(passo, restante)
            self._passo(h)
            restante -= h

    def _passo(self, h):
        s = self.s
        s["tempo_jogado"] += h
        f = s["fase"]
        if f == "marcha":
            self._marcha(h)
        elif f == "combate":
            self._combate(h)
        elif f == "recuperacao":
            self._recuperacao(h)
        elif f == "forja":
            self._forja(h)
        else:
            self._consolidacao(h)

    def _iniciar(self, fase):
        self.s["fase"] = fase
        self.s["fase_t"] = 0.0

    # ---------------------------------------------------------------- marcha
    def _marcha(self, h):
        s = self.s
        s["fase_t"] += h
        dur = self.derivados()["vel_marcha"]
        while s["fase"] == "marcha" and s["fase_t"] >= dur:
            s["fase_t"] -= dur
            self._passo_marcha()

    def _passo_marcha(self):
        s, p, rng = self.s, self.p, self.rng
        d = self.derivados()
        reg = self.regiao_atual()
        avanco = rng.uniform(1.5, 3.0)
        s["progresso"] += avanco
        s["stats"]["leguas"] += avanco
        p["fadiga"] = min(100.0, p["fadiga"] + 1.6 / d["resist"])
        p["pv"] = min(d["pv_max"], p["pv"] + d["pv_max"] * 0.01)
        self._xp_maestria("resistencia", 0.5)
        if rng.random() < 0.12:
            self.registrar("info", rng.choice(reg["ambiente"]))
        if rng.random() < 0.06:
            self._perigo(reg)
        if s["tempo_jogado"] >= s["prox_evento"] and rng.random() < 0.15:
            subiu = EV.resolver(self)
            s["prox_evento"] = s["tempo_jogado"] + rng.uniform(300, 900)
            if subiu:
                s["nivelou"] = True
                self._iniciar("consolidacao")
                return
        if s["progresso"] >= reg["extensao"]:
            self._chegar_guardiao()
            return
        if p["fadiga"] >= 88 or p["pv"] < 0.4 * d["pv_max"]:
            self._descansar()
            return
        if rng.random() < 0.42:
            self._encontro()

    def _perigo(self, reg):
        p, d = self.p, self.derivados()
        dano = d["pv_max"] * self.rng.uniform(0.03, 0.09)
        p["pv"] = max(1.0, p["pv"] - dano)
        p["fadiga"] = min(100.0, p["fadiga"] + 4)
        self.s["stats"]["perigos"] += 1
        self.s["stats"]["dano_sofrido"] += dano
        self.registrar("perigo", D.TEXTOS["perigo"].format(
            texto=self.rng.choice(reg["perigos"]), dano=int(dano)))

    def _nivel_inimigo(self):
        s = self.s
        reg = self.regiao_atual()
        frac = limitar(s["progresso"] / reg["extensao"], 0, 1)
        n = int(reg["nivel_base"] + frac * (reg["nivel_chefe"] - reg["nivel_base"] - 1))
        return n + s["ciclo"] * D.NIVEIS_POR_CICLO

    def _sortear_afixos(self, nivel, minimo=0, maximo=None):
        """Afixos de um inimigo comum. Quanto maior o nível e o ciclo, mais comuns e mais numerosos."""
        rng, s = self.rng, self.s
        if minimo == 0 and nivel < 5:
            return []
        n = minimo
        if minimo == 0:
            chance = min(0.50, 0.12 + 0.0008 * nivel + 0.04 * s["ciclo"])
            if rng.random() > chance:
                return []
            n = 1
            if nivel >= 25 and rng.random() < 0.18:
                n = 2
            if nivel >= 100 and rng.random() < 0.06:
                n = 3
        return rng.sample(list(DN.AFIXOS), min(n, len(DN.AFIXOS)))

    def _criar_inimigo(self, nome, nivel, hp_mult, dano_mult, chefe, afixos=(), fases=None):
        b = stats_inimigo(nivel, self.s["ciclo"])
        d, L = self.derivados(), max(1, self.p["nivel"])
        adapta_hp = max(1.0, d["dano"] / (REF_DANO * L)) ** ADAPT_EXP
        adapta_dano = max(1.0, d["pv_max"] / (REF_PV * L)) ** ADAPT_EXP
        cresc = min(CHEFE_CRESC_MAX, 1.0 + CHEFE_CRESC * L) if chefe else 1.0
        hp = b["hp"] * hp_mult * adapta_hp * (CHEFE_HP if chefe else 1.0) * (1 + (cresc - 1) * 0.5)
        dano = b["dano"] * dano_mult * adapta_dano * (CHEFE_DANO if chefe else 1.0) * cresc
        vel = 2.0 if chefe else self.rng.uniform(2.0, 2.6)
        xp = b["xp"] * (6 if chefe else 1.0) * (1 + 0.5 * len(afixos))
        for a in afixos:
            hp *= DN.AFIXOS[a].get("hp", 1.0)
            dano *= DN.AFIXOS[a].get("dano", 1.0)
            vel *= DN.AFIXOS[a].get("vel", 1.0)
        tag = " [%s]" % ", ".join(DN.AFIXOS[a]["nome"] for a in afixos) if afixos else ""
        return {
            "nome": nome + tag, "base": nome, "nivel": nivel, "hp": hp, "hp_max": hp,
            "dano": dano, "vel": vel,
            "evasao": 0.04 + nivel * 0.002 if nivel < 100 else 0.24,
            "xp": xp, "chefe": chefe,
            "afixos": list(afixos), "fases": [dict(f, ok=False) for f in (fases or [])],
            "escudo": 0.0, "dot": None, "ressurgiu": False,
        }

    def _encontro(self):
        reg = self.regiao_atual()
        nome, hpm, dmm = self.rng.choice(reg["inimigos"])
        nivel = self._nivel_inimigo()
        e = self._criar_inimigo(nome, nivel, hpm, dmm, False, self._sortear_afixos(nivel))
        self._iniciar_combate(e, self.rng.choice(D.TEXTOS["encontro"]))

    def _iniciar_combate(self, e, texto):
        s = self.s
        s["inimigo"] = e
        s["fase"] = "combate"
        s["fase_t"] = 0.0
        s["t_jogador"] = 0.0
        s["t_inimigo"] = 0.0
        s["veneno"] = None
        self.registrar("combate", texto.format(inimigo=e["nome"], n=e["nivel"]))
        if e["afixos"] and not e["chefe"]:
            self._marco("primeiro_elite", D.TEXTOS["elite"])
        for a in e["afixos"]:
            if a not in s["afixos_vistos"]:
                s["afixos_vistos"].append(a)
                self.registrar("info", "Característica %s: %s" % (DN.AFIXOS[a]["nome"], DN.AFIXOS[a]["desc"]))

    def _chegar_guardiao(self):
        s, p = self.s, self.p
        reg = self.regiao_atual()
        nivel_chefe = reg["nivel_chefe"] + s["ciclo"] * D.NIVEIS_POR_CICLO
        if p["nivel"] < nivel_chefe - 1:
            s["progresso"] = reg["extensao"] * 0.35
            self.registrar("alerta", D.TEXTOS["gate"].format(inimigo=reg["guardiao"], n=nivel_chefe - 1))
            return
        extras = self._sortear_afixos(nivel_chefe, minimo=min(2, (s["ciclo"] + 1) // 2)) if s["ciclo"] else []
        e = self._criar_inimigo(reg["guardiao"], nivel_chefe, 1.0, 1.0, True, extras,
                                DN.FASES_GUARDIAO[s["regiao"]])
        self._iniciar_combate(e, self.rng.choice(D.TEXTOS["chefe"]))

    # ---------------------------------------------------------------- combate
    def _combate(self, h):
        s = self.s
        e = s["inimigo"]
        if e is None:
            self._decidir()
            return
        d = self.derivados()
        self._status(e, d, h)
        if s["fase"] != "combate" or s["inimigo"] is not e:
            return
        s["t_jogador"] += h
        s["t_inimigo"] += h
        while s["t_jogador"] >= d["ciclo"]:
            s["t_jogador"] -= d["ciclo"]
            self._ataque_jogador(e, d)
            if s["fase"] != "combate" or s["inimigo"] is not e:
                return
        while s["t_inimigo"] >= e["vel"]:
            s["t_inimigo"] -= e["vel"]
            self._ataque_inimigo(e, d)
            if s["fase"] != "combate" or s["inimigo"] is not e:
                return

    def _status(self, e, d, h):
        """Efeitos contínuos: dano ao longo do tempo, regeneração e veneno."""
        s, p = self.s, self.p
        dot = e.get("dot")
        if dot:
            tick = min(h, dot["t"])
            self._dano_inimigo(e, dot["dps"] * tick)
            dot["t"] -= h
            if dot["t"] <= 0:
                e["dot"] = None
        if "regenerador" in e["afixos"] and e["hp"] > 0:
            e["hp"] = min(e["hp_max"], e["hp"] + e["hp_max"] * 0.008 * h)
        if e["hp"] <= 0:
            self._inimigo_cai(e)
            return
        self._checar_fases(e)
        v = s.get("veneno")
        if v:
            tick = min(h, v["t"])
            dano = v["dps"] * tick * (1 - d["resist_veneno"])
            p["pv"] = max(1.0, p["pv"] - dano)
            s["stats"]["dano_sofrido"] += dano
            v["t"] -= h
            if v["t"] <= 0:
                s["veneno"] = None
            if self._checar_recuo(e, d):
                return

    def _dano_inimigo(self, e, dano):
        """Aplica dano ao inimigo, consumindo o escudo primeiro. Retorna o dano total causado."""
        esc = e.get("escudo", 0.0)
        if esc > 0:
            absorvido = min(esc, dano)
            e["escudo"] = esc - absorvido
            e["hp"] -= dano - absorvido
        else:
            e["hp"] -= dano
        return dano

    def _checar_fases(self, e):
        if not e["fases"] or e["hp"] <= 0:
            return
        frac = e["hp"] / e["hp_max"]
        for f in e["fases"]:
            if f["ok"] or frac > f["limiar"]:
                continue
            f["ok"] = True
            self.registrar("alerta", f["texto"])
            if "dano" in f:
                e["dano"] *= f["dano"]
            if "vel" in f:
                e["vel"] *= f["vel"]
            if "escudo" in f:
                e["escudo"] += e["hp_max"] * f["escudo"]
            if "cura" in f:
                e["hp"] = min(e["hp_max"], e["hp"] + e["hp_max"] * f["cura"])
            if f.get("afixo") and f["afixo"] not in e["afixos"]:
                e["afixos"].append(f["afixo"])

    def _inimigo_cai(self, e):
        """Retorna True se o inimigo realmente morreu (False se ressurgiu)."""
        if "insepulto" in e["afixos"] and not e.get("ressurgiu"):
            e["ressurgiu"] = True
            e["hp"] = e["hp_max"] * 0.35
            self.registrar("alerta", DN.AFIXOS["insepulto"]["ativa"].format(inimigo=e["base"]))
            return False
        self._vitoria(e)
        return True

    def _checar_recuo(self, e, d):
        p = self.p
        if p["pv"] <= 0.2 * d["pv_max"]:
            p["pv"] = max(p["pv"], 1.0)
            self._recuar(e)
            return True
        return False

    def _ataque_jogador(self, e, d):
        s, p, rng = self.s, self.p, self.rng
        cl = D.CLASSES[p["classe"]]
        tec = cl["tecnica"]
        fad = 1 - 0.25 * (p["fadiga"] / 100.0) ** 2
        s["cd_tecnica"] -= 1
        usar_tecnica = s["cd_tecnica"] <= 0
        acerto = limitar(d["acerto"] - e["evasao"], 0.35, 0.97)
        if not usar_tecnica and rng.random() > acerto:
            self._xp_maestria("precisao", 0.5)
            self.registrar("detalhe", rng.choice(D.TEXTOS["erro"]).format(inimigo=e["nome"]))
            return
        dano = d["dano"] * fad * rng.uniform(0.85, 1.15)
        if usar_tecnica:
            dano *= tec["mult"] * (1 + d["tecnica_pct"])
            s["cd_tecnica"] = tec["cd"]
            self._xp_maestria("tecnica", 4)
            if tec["cura"]:
                p["pv"] = min(d["pv_max"], p["pv"] + d["pv_max"] * tec["cura"])
        if e["chefe"]:
            dano *= 1 + d["dano_chefe_pct"]
        critico = rng.random() < d["crit"]
        if critico:
            dano *= d["crit_mult"]
            s["stats"]["criticos"] += 1
            self._xp_maestria("precisao", 3)
        dano = max(1.0, dano)
        if "blindado" in e["afixos"]:
            dano *= 0.70
        self._dano_inimigo(e, dano)
        if usar_tecnica and tec.get("dot"):
            e["dot"] = {"dps": dano * tec["dot"]["frac"] / tec["dot"]["dur"], "t": tec["dot"]["dur"]}
        if d["roubo_vida"]:
            p["pv"] = min(d["pv_max"], p["pv"] + dano * d["roubo_vida"])
        st = s["stats"]
        st["dano_causado"] += dano
        st["maior_golpe"] = max(st["maior_golpe"], dano)
        self._xp_maestria("armas", 1)
        dd = int(dano)
        if usar_tecnica:
            self.registrar("combate", tec["texto"].format(tecnica=tec["nome"], inimigo=e["nome"], dano=dd))
        elif critico:
            self.registrar("combate", rng.choice(D.TEXTOS["critico"]).format(inimigo=e["nome"], dano=dd))
        else:
            self.registrar("detalhe", rng.choice(D.TEXTOS["ataque"]).format(inimigo=e["nome"], dano=dd))
        if e["hp"] <= 0:
            self._inimigo_cai(e)
            return
        self._checar_fases(e)
        if "espinhoso" in e["afixos"]:
            refl = min(dano * 0.05, d["pv_max"] * 0.02)
            p["pv"] = max(1.0, p["pv"] - refl)
            st["dano_sofrido"] += refl
            self.registrar("detalhe", DN.AFIXOS["espinhoso"]["ativa"].format(inimigo=e["nome"], dano=int(refl)))
            self._checar_recuo(e, d)

    def _ataque_inimigo(self, e, d):
        s, p, rng = self.s, self.p, self.rng
        if rng.random() < d["esquiva"]:
            self.registrar("detalhe", rng.choice(D.TEXTOS["desvio"]).format(inimigo=e["nome"]))
            return
        mitigacao = d["defesa"] / (d["defesa"] + 30 + 7 * e["nivel"])
        base = e["dano"] * rng.uniform(0.85, 1.15)
        if "impiedoso" in e["afixos"]:
            mitigacao *= 0.70
            base *= 1.15
        dano = max(1.0, base * (1 - mitigacao) * (1 - d["reducao_dano"]))
        p["pv"] -= dano
        s["stats"]["dano_sofrido"] += dano
        p["fadiga"] = min(100.0, p["fadiga"] + 0.4 / d["resist"])
        self._xp_maestria("guarda", 1)
        dd = int(dano)
        if dano >= 0.25 * d["pv_max"]:
            self.registrar("combate", D.TEXTOS["devastador"].format(inimigo=e["nome"], dano=dd))
        else:
            self.registrar("detalhe", rng.choice(D.TEXTOS["dano_recebido"]).format(inimigo=e["nome"], dano=dd))
        if "sanguinario" in e["afixos"]:
            e["hp"] = min(e["hp_max"], e["hp"] + dano * 0.35)
        if "aterrador" in e["afixos"]:
            p["fadiga"] = min(100.0, p["fadiga"] + 1.5 / d["resist"])
        if "venenoso" in e["afixos"] and rng.random() < 0.55:
            dps = 0.10 * e["dano"]
            atual = s.get("veneno")
            if atual is None:
                self.registrar("perigo", DN.AFIXOS["venenoso"]["ativa"].format(inimigo=e["nome"]))
                s["veneno"] = {"dps": dps, "t": 8.0}
            else:
                atual["dps"] = max(atual["dps"], dps)
                atual["t"] = 8.0
        if self._checar_recuo(e, d):
            return
        p["pv"] = max(p["pv"], 1.0)

    def _recuar(self, e):
        s, p = self.s, self.p
        reg = self.regiao_atual()
        s["stats"]["recuos"] += 1
        s["recuos_seguidos"] += 1
        s["veneno"] = None
        perda = reg["extensao"] * (0.25 if e["chefe"] else 0.10)
        s["progresso"] = max(0.0, s["progresso"] - perda)
        if e["chefe"]:
            s["progresso"] = min(s["progresso"], reg["extensao"] * 0.75)
        p["fadiga"] = min(100.0, p["fadiga"] + 10)
        s["inimigo"] = None
        self.registrar("alerta", self.rng.choice(D.TEXTOS["recuo"]).format(inimigo=e["nome"]))
        if s["recuos_seguidos"] >= 3 and (s["regiao"] > 0 or s["ciclo"] > 0):
            if s["regiao"] > 0:
                s["regiao"] -= 1
            else:
                s["regiao"] = len(D.REGIOES) - 1
                s["ciclo"] -= 1
            s["progresso"] = self.regiao_atual()["extensao"] * 0.5
            s["recuos_seguidos"] = 0
            self.registrar("alerta", D.TEXTOS["descida"])
        self._marco("primeiro_recuo", "Marco: primeiro recuo. Fugir também é uma forma de sobreviver.")
        self._descansar()

    def _vitoria(self, e):
        s, p, rng = self.s, self.p, self.rng
        d = self.derivados()
        s["inimigo"] = None
        if s.get("veneno"):
            s["veneno"] = None
            self.registrar("detalhe", D.TEXTOS["veneno_fim"])
        xp = int(e["xp"] * (1 + d["xp_pct"]))
        st = s["stats"]
        st["abates"] += 1
        s["recuos_seguidos"] = 0
        if e["afixos"] and not e["chefe"]:
            st["elites"] += 1
        self.registrar("combate", rng.choice(D.TEXTOS["vitoria"]).format(inimigo=e["nome"], xp=xp))
        self._marco("primeiro_sangue", "Marco: primeiro inimigo abatido. A jornada deixa de ser apenas um caminho.")
        frag = (rng.uniform(1, 3) + e["nivel"] * FRAG_POR_NIVEL) * (3 if e["chefe"] else 1)
        p["fragmentos"] += int(frag * (1 + d["fragmentos_pct"]))
        if e["chefe"] or rng.random() < 0.30 + 0.12 * len(e["afixos"]):
            self._receber_item(I.sortear_loot(rng, e["nivel"], chefe=e["chefe"], regiao=s["regiao"],
                                              elite=0 if e["chefe"] else len(e["afixos"])))
        if e["chefe"]:
            self._soltar_unico(e)
            self._derrotar_chefe(e)
        subiu = self._ganhar_xp(xp)
        if subiu:
            s["nivelou"] = True
            self._iniciar("consolidacao")
        else:
            self._decidir()

    def _derrotar_chefe(self, e):
        s = self.s
        reg = self.regiao_atual()
        s["stats"]["chefes"] += 1
        idx = s["regiao"]
        if self._marco("guardiao_%d_%d" % (s["ciclo"], idx), reg["marco"]):
            self._conceder_talento()
        s["progresso"] = 0.0
        s["recuos_seguidos"] = 0
        if idx < len(D.REGIOES) - 1:
            s["regiao"] += 1
        else:
            s["regiao"] = 0
            s["ciclo"] += 1
            self._marco("ciclo_%d" % s["ciclo"], D.TEXTOS["ciclo"].format(n=s["ciclo"] + 1))
        nova = self.regiao_atual()
        self.registrar("info", D.TEXTOS["chegada"].format(regiao=self.nome_regiao(), desc=nova["desc"]))

    # ---------------------------------------------------------------- itens
    def _soltar_unico(self, e):
        s, rng = self.s, self.rng
        uid = DI.UNICO_POR_REGIAO[s["regiao"]]
        primeira = uid not in s["unicos"]
        if not primeira and rng.random() >= 0.15:
            return
        item = I.gerar_unico(rng, uid, e["nivel"])
        if primeira:
            s["unicos"].append(uid)
            s["stats"]["unicos"] += 1
            self._marco("unico_" + uid, D.TEXTOS["unico"].format(
                inimigo=e["base"], item=item["nome"], lore=DI.UNICOS[uid]["lore"]))
        else:
            self.registrar("item", D.TEXTOS["unico_extra"].format(inimigo=e["base"], item=item["nome"]))
        self._receber_item(item)

    def _receber_item(self, item):
        p = self.p
        self.s["stats"]["itens"] += 1
        atual = p["equip"].get(item["slot"])
        rar = I.rotulo_raridade(item)
        if item["raridade"] == 4 and not item.get("unico"):
            self._marco("primeiro_lendario", "Marco: um item lendário é seu. Há coisas que escolhem quem as carrega.")
        if atual is None or I.valor(item) > I.valor(atual):
            antes = I.contagem_conjuntos(p["equip"])
            p["equip"][item["slot"]] = item
            if atual:
                self._desmontar(atual)
            self.invalidar()
            self.registrar("item", D.TEXTOS["equipou"].format(item=I.rotulo(item), raridade=rar))
            self._avisar_conjuntos(antes)
        else:
            self._desmontar(item)
            self.registrar("item" if item["raridade"] >= 2 else "detalhe",
                           D.TEXTOS["achado"].format(item=I.rotulo(item), raridade=rar))

    def _avisar_conjuntos(self, antes):
        depois = I.contagem_conjuntos(self.p["equip"])
        for sid, n in depois.items():
            for pecas, bonus in sorted(DI.SETS[sid]["bonus"].items()):
                if antes.get(sid, 0) < pecas <= n:
                    self.registrar("item", D.TEXTOS["conjunto"].format(
                        nome=DI.SETS[sid]["nome"], n=pecas, efeitos=I.descrever_efeitos(bonus)))

    def _desmontar(self, item):
        self.p["fragmentos"] += I.fragmentos_ao_desmontar(item)
        self.s["stats"]["desmontados"] += 1

    def _proxima_forja(self):
        p = self.p
        melhor = None
        for ordem, slot in enumerate(D.SLOTS):
            it = p["equip"].get(slot)
            if not it or it["refino"] >= D.REFINO_MAX:
                continue
            if p["fragmentos"] >= I.custo_refino(it):
                chave = (it["refino"], ordem)
                if melhor is None or chave < melhor[0]:
                    melhor = (chave, slot)
        return melhor[1] if melhor else None

    def _forja(self, h):
        s = self.s
        s["fase_t"] += h
        if s["fase_t"] >= DURACAO_FORJA:
            self._refinar(s["forja_slot"])
            self._decidir()

    def _refinar(self, slot):
        p, s = self.p, self.s
        it = p["equip"].get(slot)
        if not it:
            return
        custo = I.custo_refino(it)
        if p["fragmentos"] < custo or it["refino"] >= D.REFINO_MAX:
            return
        p["fragmentos"] -= custo
        self._xp_maestria("forja", 5)
        if self.rng.random() < I.chance_refino(it, self.derivados()["forja"]):
            it["refino"] += 1
            s["stats"]["refinos_ok"] += 1
            self.invalidar()
            self.registrar("forja", D.TEXTOS["forja_ok"].format(item=it["nome"], n=it["refino"]))
            if it["refino"] == 5:
                self._marco("refino_5", "Marco: um equipamento alcança +5. O ferro agora lembra a mão que o forjou.")
            if it["refino"] == 10:
                self._marco("refino_10", "Marco: um equipamento alcança +10. Poucos ferreiros jamais viram tal temperança.")
            if it["refino"] == 20:
                self._marco("refino_20", "Marco: um equipamento alcança +20. O metal já não é metal; é promessa.")
            if it["refino"] == 30:
                self._marco("refino_30", "Marco: um equipamento alcança +30, o limite do ofício. Nada mais pode ser pedido ao ferro.")
        else:
            s["stats"]["refinos_falha"] += 1
            self.registrar("forja", D.TEXTOS["forja_falha"].format(item=it["nome"]))

    # --------------------------------------------------------- recuperação
    def _descansar(self):
        self._iniciar("recuperacao")
        self.registrar("info", self.rng.choice(D.TEXTOS["descanso"]))

    def _recuperacao(self, h):
        p = self.p
        d = self.derivados()
        p["pv"] = min(d["pv_max"], p["pv"] + d["pv_max"] * d["regen"] * h)
        p["fadiga"] = max(0.0, p["fadiga"] - 5.0 * h)
        self._xp_maestria("sobrevivencia", 0.3 * h)
        if p["pv"] >= 0.97 * d["pv_max"] and p["fadiga"] <= 12:
            self.registrar("info", D.TEXTOS["descanso_fim"])
            self._decidir()

    def _decidir(self):
        """Escolhe a próxima atividade após qualquer etapa."""
        p, s = self.p, self.s
        d = self.derivados()
        if p["pv"] < 0.4 * d["pv_max"] or p["fadiga"] >= 88:
            if s["fase"] != "recuperacao":
                self._descansar()
            return
        slot = self._proxima_forja()
        if slot:
            s["forja_slot"] = slot
            self._iniciar("forja")
            self.registrar("forja", self.rng.choice(D.TEXTOS["forja_inicio"]).format(
                item=I.rotulo(p["equip"][slot])))
        else:
            self._iniciar("marcha")

    # --------------------------------------------------- progressão de nível
    def _consolidacao(self, h):
        s = self.s
        s["fase_t"] += h
        if s["fase_t"] >= DURACAO_CONSOLIDACAO:
            s["nivelou"] = False
            self._decidir()

    def _ganhar_xp(self, xp):
        p = self.p
        p["xp"] += xp
        subiu = False
        cl = D.CLASSES[p["classe"]]
        attrs = list(D.ATRIBUTOS)
        pesos = [cl["pesos"][a] for a in attrs]
        while p["xp"] >= xp_proximo_nivel(p["nivel"]):
            p["xp"] -= xp_proximo_nivel(p["nivel"])
            p["nivel"] += 1
            for a in self.rng.choices(attrs, weights=pesos, k=4):
                p["atributos"][a] += 1
            subiu = True
            self.invalidar()
            self.registrar("nivel", D.TEXTOS["nivel"].format(n=p["nivel"]))
            if p["nivel"] in D.MARCOS_NIVEL:
                self._marco("nivel_%d" % p["nivel"], D.MARCOS_NIVEL[p["nivel"]])
            if p["nivel"] % 100 == 0 and p["nivel"] > 100:
                self._marco("nivel_%d" % p["nivel"],
                            "Marco: nível %d. Anos de estrada, e a Roda continua a girar sob os seus passos." % p["nivel"])
            if p["nivel"] % TALENTO_A_CADA == 0:
                self._conceder_talento()
        if subiu:
            d = self.derivados()
            p["pv"] = min(d["pv_max"], p["pv"] + d["pv_max"] * 0.3)
        return subiu

    def _conceder_talento(self):
        p = self.p
        tid = T.proximo(p["classe"], p["caminho"], p["talentos"])
        if tid is None:
            attr = D.CLASSES[p["classe"]]["principal"]
            p["atributos"][attr] += 2
            self.registrar("talento", D.TEXTOS["talento_max"].format(attr=D.NOMES_ATRIBUTOS[attr]))
        else:
            p["talentos"][tid] = p["talentos"].get(tid, 0) + 1
            defn = T.definicao(p["classe"], tid)
            self.registrar("talento", D.TEXTOS["talento"].format(
                nome=defn["nome"], n=p["talentos"][tid], desc=defn["desc"]))
        self.invalidar()

    def _xp_maestria(self, chave, qtd):
        m = self.p["maestrias"][chave]
        if m["nivel"] >= D.NIVEL_MAX_MAESTRIA:
            return
        m["xp"] += qtd
        while m["nivel"] < D.NIVEL_MAX_MAESTRIA and m["xp"] >= xp_proxima_maestria(m["nivel"]):
            m["xp"] -= xp_proxima_maestria(m["nivel"])
            m["nivel"] += 1
            self.invalidar()
            if m["nivel"] % 5 == 0:
                self.registrar("nivel", D.TEXTOS["maestria"].format(nome=D.MAESTRIAS[chave]["nome"], n=m["nivel"]))

    def _marco(self, id_marco, texto):
        """Registra um marco inédito. Retorna True se ele ainda não existia."""
        s = self.s
        if any(m["id"] == id_marco for m in s["marcos"]):
            return False
        s["marcos"].append({"id": id_marco, "t": round(s["tempo_jogado"], 1), "texto": texto})
        self.registrar("marco", texto)
        return True

    # --------------------------------------------------------------- offline
    def resumo(self):
        s = self.s
        return {
            "nivel": self.p["nivel"], "regiao": s["regiao"], "ciclo": s["ciclo"],
            "stats": dict(s["stats"]), "marcos": len(s["marcos"]), "tempo": s["tempo_jogado"],
            "talentos": T.total(self.p["talentos"]),
        }

    def simular_offline(self, segundos):
        """Simula o intervalo em que o jogo esteve fechado. Retorna as linhas do relatório."""
        truncado = segundos > OFFLINE_MAX_S
        sim = min(segundos, OFFLINE_MAX_S)
        antes = self.resumo()
        n_marcos_antes = len(self.s["marcos"])
        self.silencioso = True
        try:
            self.avancar(sim, passo=1.0)
        finally:
            self.silencioso = False
        depois = self.resumo()
        sa, sd = antes["stats"], depois["stats"]
        linhas = ["Você esteve ausente por %s." % fmt_duracao(segundos)]
        if truncado:
            linhas.append("Apenas as primeiras %s foram contabilizadas." % fmt_duracao(OFFLINE_MAX_S))
        linhas.append("Nível: %d -> %d (+%d)" % (antes["nivel"], depois["nivel"], depois["nivel"] - antes["nivel"]))
        linhas.append("Inimigos abatidos: %d (marcados: %d, guardiões: %d)" % (
            sd["abates"] - sa["abates"], sd["elites"] - sa["elites"], sd["chefes"] - sa["chefes"]))
        linhas.append("Léguas percorridas: %d | Eventos na estrada: %d" % (
            int(sd["leguas"] - sa["leguas"]),
            (sd["eventos_ok"] + sd["eventos_falha"]) - (sa["eventos_ok"] + sa["eventos_falha"])))
        linhas.append("Recuos: %d | Itens obtidos: %d | Refinos: %d bem-sucedidos, %d falhos" % (
            sd["recuos"] - sa["recuos"], sd["itens"] - sa["itens"],
            sd["refinos_ok"] - sa["refinos_ok"], sd["refinos_falha"] - sa["refinos_falha"]))
        if depois["talentos"] > antes["talentos"]:
            linhas.append("Talentos obtidos: %d" % (depois["talentos"] - antes["talentos"]))
        linhas.append("Local atual: %s" % self.nome_regiao())
        novos = self.s["marcos"][n_marcos_antes:]
        for m in novos[-5:]:
            linhas.append(m["texto"])
        self.registrar("relato", "Relato do intervalo: " + " ".join(linhas[:6]))
        return linhas


def retomar(estado, agora=None, semente=None):
    """Reconstrói o Motor a partir de um save, aplicando o progresso offline.

    Retorna (motor, linhas_do_relatorio). A lista é vazia se a ausência foi curta.
    """
    agora = agora or time.time()
    motor = Motor(estado, semente)
    decorrido = agora - estado.get("salvo_em", agora)
    linhas = []
    if decorrido >= OFFLINE_MIN_S:
        linhas = motor.simular_offline(decorrido)
    return motor, linhas
