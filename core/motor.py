# -*- coding: utf-8 -*-
"""Motor de simulação idle de Crônicas de Cinzas.

O estado inteiro vive em um dicionário serializável (``Motor.s``). A simulação avança por
tempo (``avancar(dt)``), em passos curtos e fixos, de modo que o resultado independe da
velocidade da máquina ou da taxa de quadros da interface.
"""
import random
import time

from . import dados as D
from . import itens as I
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


def xp_proximo_nivel(nivel):
    return int(30 * nivel ** 2.3)


def xp_proxima_maestria(nivel):
    return 12 * 1.22 ** (nivel - 1)


def stats_inimigo(nivel):
    """Valores base de um inimigo de determinado nível, antes dos multiplicadores do tipo."""
    return {
        "hp": 24 * nivel ** 1.4,
        "dano": 4 + 1.5 * nivel ** 1.18,
        "xp": 9 * nivel ** 1.25,
    }


def novo_estado(nome, origem, classe, atributos, agora=None):
    """Monta o estado de uma jornada nova. 'atributos' já inclui o bônus de origem."""
    agora = agora or time.time()
    rng = random.Random()
    cl = D.CLASSES[classe]
    equip = {
        "arma": I.gerar_item(rng, "arma", 1, raridade=0, nome_fixo=cl["arma"]),
        "armadura": I.gerar_item(rng, "armadura", 1, raridade=0, nome_fixo=("Gibão Remendado", "m")),
        "reliquia": I.gerar_item(rng, "reliquia", 1, raridade=0, nome_fixo=("Medalhão Sem Brilho", "m")),
    }
    s = {
        "versao": 1,
        "criado_em": agora,
        "salvo_em": agora,
        "tempo_jogado": 0.0,
        "personagem": {
            "nome": nome, "origem": origem, "classe": classe,
            "nivel": 1, "xp": 0.0,
            "atributos": dict(atributos),
            "pv": 1.0, "fadiga": 0.0, "fragmentos": 0,
            "equip": equip,
            "maestrias": {k: {"nivel": 1, "xp": 0.0} for k in D.MAESTRIAS},
        },
        "regiao": 0, "ciclo": 0, "progresso": 0.0, "recuos_seguidos": 0,
        "fase": "marcha", "fase_t": 0.0,
        "inimigo": None, "t_jogador": 0.0, "t_inimigo": 0.0, "cd_tecnica": cl["tecnica"]["cd"],
        "forja_slot": None, "nivelou": False,
        "marcos": [], "cronica": [], "cron_n": 0,
        "stats": {
            "abates": 0, "chefes": 0, "leguas": 0.0, "recuos": 0, "itens": 0, "desmontados": 0,
            "refinos_ok": 0, "refinos_falha": 0, "dano_causado": 0.0, "dano_sofrido": 0.0,
            "criticos": 0, "perigos": 0, "maior_golpe": 0.0,
        },
    }
    return s


class Motor:
    def __init__(self, estado, semente=None):
        self.s = estado
        self.rng = random.Random(semente)
        self.silencioso = False
        self._der = None
        self._der_nivel = None
        p = self.s["personagem"]
        if p["pv"] <= 1.0 and not self.s["cronica"]:
            p["pv"] = self.derivados()["pv_max"]

    # ------------------------------------------------------------ construção
    @classmethod
    def novo(cls, nome, origem, classe, atributos, semente=None):
        s = novo_estado(nome, origem, classe, atributos)
        m = cls(s, semente)
        m.registrar("marco", D.TEXTOS["inicio"].format(
            nome=nome, origem=D.ORIGENS[origem]["nome"], classe=D.CLASSES[classe]["nome"]))
        m.registrar("info", D.TEXTOS["chegada"].format(regiao=D.REGIOES[0]["nome"], desc=D.REGIOES[0]["desc"]))
        return m

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

    def atributos_totais(self):
        tot = dict(self.p["atributos"])
        for it in self.p["equip"].values():
            if it:
                for a, v in I.afixos(it).items():
                    tot[a] += v
        return tot

    def efeitos_maestrias(self):
        ef = {"dano_pct": 0.0, "crit": 0.0, "defesa_pct": 0.0, "fadiga_red": 0.0,
              "regen_pct": 0.0, "forja": 0.0, "tecnica_pct": 0.0}
        for k, m in self.p["maestrias"].items():
            definicao = D.MAESTRIAS[k]
            ef[definicao["efeito"]] += (m["nivel"] - 1) * definicao["por_nivel"]
        return ef

    def derivados(self):
        if self._der is not None:
            return self._der
        p = self.p
        L = p["nivel"]
        A = self.atributos_totais()
        cl = D.CLASSES[p["classe"]]
        eq = p["equip"]
        m = self.efeitos_maestrias()
        poder_arma = I.poder(eq["arma"]) if eq.get("arma") else 0.0
        poder_arm = I.poder(eq["armadura"]) if eq.get("armadura") else 0.0
        vigor = I.poder(eq["reliquia"]) * 2.5 if eq.get("reliquia") else 0.0
        principal = A[cl["principal"]]
        self._der = {
            "atributos": A,
            "pv_max": 60 + A["vitalidade"] * 10 + L * 8 + vigor,
            "dano": (principal * 1.3 + poder_arma + L * 1.5) * (1 + m["dano_pct"]),
            "defesa": (poder_arm + A["vitalidade"] * 0.6 + A["vontade"] * 0.4 + L) * (1 + m["defesa_pct"]),
            "acerto": min(0.97, 0.80 + A["destreza"] * 0.0015),
            "crit": min(0.60, 0.04 + A["destreza"] * 0.0012 + A["intelecto"] * 0.0008 + m["crit"]),
            "ciclo": max(0.6, 1.9 - A["destreza"] * 0.01 - L * 0.004),
            "regen": (0.045 + A["vontade"] * 0.0005) * (1 + m["regen_pct"]),
            "resist": 1 + A["vontade"] * 0.012 + m["fadiga_red"],
            "vel_marcha": 3.0 / (1 + A["destreza"] * 0.004),
            "forja": m["forja"],
            "tecnica_pct": m["tecnica_pct"],
            "dano_pct": m["dano_pct"],
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
            det = "%s (nível %d) %d/%d" % (e["nome"], e["nivel"], max(0, int(e["hp"])), int(e["hp_max"])) if e else ""
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

    def _criar_inimigo(self, nome, nivel, hp_mult, dano_mult, chefe):
        b = stats_inimigo(nivel)
        hp = b["hp"] * hp_mult * (4.5 if chefe else 1.0)
        return {
            "nome": nome, "nivel": nivel, "hp": hp, "hp_max": hp,
            "dano": b["dano"] * dano_mult * (1.5 if chefe else 1.0),
            "vel": 2.0 if chefe else self.rng.uniform(2.0, 2.6),
            "evasao": 0.04 + nivel * 0.002 if nivel < 100 else 0.24,
            "xp": b["xp"] * (6 if chefe else 1.0),
            "chefe": chefe,
        }

    def _encontro(self):
        reg = self.regiao_atual()
        nome, hpm, dmm = self.rng.choice(reg["inimigos"])
        e = self._criar_inimigo(nome, self._nivel_inimigo(), hpm, dmm, False)
        self._iniciar_combate(e, self.rng.choice(D.TEXTOS["encontro"]))

    def _iniciar_combate(self, e, texto):
        s = self.s
        s["inimigo"] = e
        s["fase"] = "combate"
        s["fase_t"] = 0.0
        s["t_jogador"] = 0.0
        s["t_inimigo"] = 0.0
        self.registrar("combate", texto.format(inimigo=e["nome"], n=e["nivel"]))

    def _chegar_guardiao(self):
        s, p = self.s, self.p
        reg = self.regiao_atual()
        nivel_chefe = reg["nivel_chefe"] + s["ciclo"] * D.NIVEIS_POR_CICLO
        if p["nivel"] < nivel_chefe - 1:
            s["progresso"] = reg["extensao"] * 0.35
            self.registrar("alerta", D.TEXTOS["gate"].format(inimigo=reg["guardiao"], n=nivel_chefe - 1))
            return
        e = self._criar_inimigo(reg["guardiao"], nivel_chefe, 1.0, 1.0, True)
        self._iniciar_combate(e, self.rng.choice(D.TEXTOS["chefe"]))

    # ---------------------------------------------------------------- combate
    def _combate(self, h):
        s = self.s
        e = s["inimigo"]
        if e is None:
            self._decidir()
            return
        d = self.derivados()
        s["t_jogador"] += h
        s["t_inimigo"] += h
        while s["t_jogador"] >= d["ciclo"]:
            s["t_jogador"] -= d["ciclo"]
            self._ataque_jogador(e, d)
            if e["hp"] <= 0:
                self._vitoria(e)
                return
        while s["t_inimigo"] >= e["vel"]:
            s["t_inimigo"] -= e["vel"]
            self._ataque_inimigo(e, d)
            if s["fase"] != "combate":
                return

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
        critico = rng.random() < d["crit"]
        if critico:
            dano *= 1.75
            s["stats"]["criticos"] += 1
            self._xp_maestria("precisao", 3)
        dano = max(1.0, dano)
        e["hp"] -= dano
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

    def _ataque_inimigo(self, e, d):
        s, p, rng = self.s, self.p, self.rng
        if rng.random() > 0.90:
            self.registrar("detalhe", rng.choice(D.TEXTOS["desvio"]).format(inimigo=e["nome"]))
            return
        mitigacao = d["defesa"] / (d["defesa"] + 30 + 7 * e["nivel"])
        dano = max(1.0, e["dano"] * rng.uniform(0.85, 1.15) * (1 - mitigacao))
        p["pv"] -= dano
        s["stats"]["dano_sofrido"] += dano
        p["fadiga"] = min(100.0, p["fadiga"] + 0.4 / d["resist"])
        self._xp_maestria("guarda", 1)
        dd = int(dano)
        if dano >= 0.25 * d["pv_max"]:
            self.registrar("combate", D.TEXTOS["devastador"].format(inimigo=e["nome"], dano=dd))
        else:
            self.registrar("detalhe", rng.choice(D.TEXTOS["dano_recebido"]).format(inimigo=e["nome"], dano=dd))
        if p["pv"] <= 0.2 * d["pv_max"]:
            p["pv"] = max(p["pv"], 1.0)
            self._recuar(e)
        p["pv"] = max(p["pv"], 1.0)

    def _recuar(self, e):
        s, p = self.s, self.p
        reg = self.regiao_atual()
        s["stats"]["recuos"] += 1
        s["recuos_seguidos"] += 1
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
        s["inimigo"] = None
        xp = int(e["xp"])
        st = s["stats"]
        st["abates"] += 1
        s["recuos_seguidos"] = 0
        self.registrar("combate", rng.choice(D.TEXTOS["vitoria"]).format(inimigo=e["nome"], xp=xp))
        self._marco("primeiro_sangue", "Marco: primeiro inimigo abatido. A jornada deixa de ser apenas um caminho.")
        frag = int((rng.uniform(1, 3) + e["nivel"] * 0.5) * (3 if e["chefe"] else 1))
        p["fragmentos"] += frag
        if e["chefe"] or rng.random() < 0.30:
            slot = rng.choices(D.SLOTS, weights=[0.4, 0.4, 0.2])[0]
            self._receber_item(I.gerar_item(rng, slot, e["nivel"], chefe=e["chefe"]))
        if e["chefe"]:
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
        self._marco("guardiao_%d_%d" % (s["ciclo"], idx), reg["marco"])
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
    def _receber_item(self, item):
        p = self.p
        self.s["stats"]["itens"] += 1
        atual = p["equip"].get(item["slot"])
        rar = D.RARIDADES[item["raridade"]]
        if item["raridade"] == 4:
            self._marco("primeiro_lendario", "Marco: um item lendário é seu. Há coisas que escolhem quem as carrega.")
        if atual is None or I.valor(item) > I.valor(atual):
            p["equip"][item["slot"]] = item
            if atual:
                self._desmontar(atual, silencioso=True)
            self.invalidar()
            self.registrar("item", D.TEXTOS["equipou"].format(item=I.rotulo(item), raridade=rar))
        else:
            self._desmontar(item, silencioso=True)
            self.registrar("item" if item["raridade"] >= 2 else "detalhe",
                           D.TEXTOS["achado"].format(item=I.rotulo(item), raridade=rar))

    def _desmontar(self, item, silencioso=False):
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
        if subiu:
            d = self.derivados()
            p["pv"] = min(d["pv_max"], p["pv"] + d["pv_max"] * 0.3)
        return subiu

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
        s = self.s
        if any(m["id"] == id_marco for m in s["marcos"]):
            return
        s["marcos"].append({"id": id_marco, "t": round(s["tempo_jogado"], 1), "texto": texto})
        self.registrar("marco", texto)

    # --------------------------------------------------------------- offline
    def resumo(self):
        s = self.s
        return {
            "nivel": self.p["nivel"], "regiao": s["regiao"], "ciclo": s["ciclo"],
            "stats": dict(s["stats"]), "marcos": len(s["marcos"]), "tempo": s["tempo_jogado"],
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
        linhas.append("Inimigos abatidos: %d (guardiões: %d)" % (
            sd["abates"] - sa["abates"], sd["chefes"] - sa["chefes"]))
        linhas.append("Léguas percorridas: %d" % int(sd["leguas"] - sa["leguas"]))
        linhas.append("Recuos: %d | Itens obtidos: %d | Refinos: %d bem-sucedidos, %d falhos" % (
            sd["recuos"] - sa["recuos"], sd["itens"] - sa["itens"],
            sd["refinos_ok"] - sa["refinos_ok"], sd["refinos_falha"] - sa["refinos_falha"]))
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
