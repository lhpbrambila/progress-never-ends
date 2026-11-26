# -*- coding: utf-8 -*-
"""Testes dos sistemas: afixos, fases de guardião, conjuntos, únicos, eventos, talentos e migração."""
import json
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (criacao, dados as D, dados_inimigos as DN, dados_itens as DI, dados_talentos as DT,
                  eventos as E, itens as I, persistencia as P, talentos as T)
from core.motor import Motor, retomar
from test_core import novo_motor, BaseComPasta

AQUI = os.path.dirname(os.path.abspath(__file__))


class TestInimigos(unittest.TestCase):
    def test_todos_afixos_tem_texto(self):
        for k, a in DN.AFIXOS.items():
            self.assertTrue(a["nome"] and a["desc"] and a["ativa"], k)
        for k in ("venenoso", "regenerador", "espinhoso", "impiedoso"):
            self.assertIn(k, DN.AFIXOS)

    def test_guardioes_tem_fases_validas(self):
        self.assertEqual(len(DN.FASES_GUARDIAO), len(D.REGIOES))
        for fases in DN.FASES_GUARDIAO:
            self.assertGreaterEqual(len(fases), 1)
            for f in fases:
                self.assertTrue(0 < f["limiar"] < 1)
                self.assertTrue(f["texto"])
                if f.get("afixo"):
                    self.assertIn(f["afixo"], DN.AFIXOS)

    def test_fase_dispara_uma_vez_e_altera_inimigo(self):
        m = novo_motor()
        e = m._criar_inimigo("Guardião", 10, 1, 1, True, fases=[dict(f, ok=False) for f in DN.FASES_GUARDIAO[0]])
        dano0 = e["dano"]
        e["hp"] = e["hp_max"] * 0.5
        m._checar_fases(e)
        self.assertGreater(e["dano"], dano0)
        d1 = e["dano"]
        m._checar_fases(e)
        self.assertEqual(e["dano"], d1)

    def test_afixos_aparecem_em_simulacao_e_heroi_nunca_morre(self):
        m = novo_motor("sacerdote", semente=9)
        m.silencioso = True
        vistos = set()
        orig = m._criar_inimigo

        def espia(*a, **k):
            e = orig(*a, **k)
            vistos.update(e["afixos"])
            return e
        m._criar_inimigo = espia
        for _ in range(48):
            m.avancar(3600, passo=2.0)
            self.assertGreaterEqual(m.p["pv"], 1.0)
        self.assertGreaterEqual(len(vistos), 4)


class TestEquipamentos(unittest.TestCase):
    def test_seis_slots(self):
        self.assertEqual(set(D.SLOTS), {"arma", "armadura", "elmo", "botas", "anel", "reliquia"})
        for slot in D.SLOTS:
            self.assertIn(slot, D.BASES_ITEM)
            self.assertIn(slot, DI.PODER_SLOT)

    def test_conjuntos_bonus_por_pecas(self):
        rng = random.Random(1)
        sid = "luto"
        pecas = list(DI.SETS[sid]["pecas"])
        equip = {}
        self.assertEqual(I.efeitos_conjuntos(equip), {})
        for i, slot in enumerate(pecas[:4]):
            equip[slot] = I.gerar_peca_conjunto(rng, sid, slot, 20, 3)
            esperado = {}
            for n, b in DI.SETS[sid]["bonus"].items():
                if i + 1 >= n:
                    I.somar(esperado, b)
            self.assertEqual(I.efeitos_conjuntos(equip), esperado, "%d peças" % (i + 1))
        self.assertTrue(I.efeitos_conjuntos(equip))

    def test_unicos_completos(self):
        rng = random.Random(2)
        self.assertEqual(len(DI.UNICOS), len(D.REGIOES))
        for uid, u in DI.UNICOS.items():
            it = I.gerar_unico(rng, uid, 30)
            self.assertEqual(it["raridade"], 4)
            self.assertTrue(I.lore_item(it))
            self.assertTrue(I.efeitos_item(it))
            self.assertEqual(I.rotulo_raridade(it), "Único")

    def test_mods_nomeados_e_lore(self):
        rng = random.Random(3)
        for _ in range(200):
            it = I.gerar_item(rng, rng.choice(D.SLOTS), 40, raridade=3)
            self.assertEqual(len(it["mods"]), 2)
            self.assertTrue(I.linhas_mods(it))
            self.assertTrue(I.lore_item(it))

    def test_refino_ate_30_e_custos_crescentes(self):
        it = I.gerar_item(random.Random(1), "arma", 50, raridade=2)
        custos = []
        for r in range(D.REFINO_MAX):
            it["refino"] = r
            custos.append(I.custo_refino(it))
        self.assertEqual(custos, sorted(custos))
        self.assertGreater(custos[-1], 100 * custos[0])
        self.assertEqual(D.REFINO_MAX, 30)

    def test_unico_cai_no_primeiro_guardiao(self):
        m = novo_motor("guardiao", semente=4)
        m.silencioso = True
        m.avancar(3 * 86400, passo=3.0)
        self.assertIn(DI.UNICO_POR_REGIAO[0], m.s["unicos"])


class TestEventos(unittest.TestCase):
    def test_catalogo(self):
        ids = [e["id"] for e in __import__("core.dados_eventos", fromlist=["x"]).EVENTOS]
        self.assertGreaterEqual(len(ids), 12)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("ponte_caida", ids)

    def test_chance_cresce_com_atributo_e_cai_com_dificuldade(self):
        self.assertGreater(E.chance_sucesso(60, 20, 1.0), E.chance_sucesso(10, 20, 1.0))
        self.assertGreater(E.chance_sucesso(30, 20, 0.8), E.chance_sucesso(30, 20, 1.6))
        for a in (0, 5, 500, 10 ** 6):
            self.assertTrue(0.10 <= E.chance_sucesso(a, 30, 1.0) <= 0.95)

    def test_evento_vai_para_cronica_e_resultado_depende_do_heroi(self):
        m = novo_motor(semente=6)
        m.silencioso = False
        for _ in range(30):
            E.resolver(m)
        cats = [x["c"] for x in m.s["cronica"]]
        self.assertGreaterEqual(cats.count("evento"), 90)
        st = m.s["stats"]
        self.assertEqual(st["eventos_ok"] + st["eventos_falha"], 30)
        self.assertGreaterEqual(m.p["pv"], 1.0)

    def test_eventos_ocorrem_na_simulacao(self):
        m = novo_motor(semente=2)
        m.silencioso = True
        m.avancar(12 * 3600, passo=2.0)
        st = m.s["stats"]
        self.assertGreater(st["eventos_ok"] + st["eventos_falha"], 10)


class TestTalentos(unittest.TestCase):
    def test_todas_as_vocacoes_e_caminhos(self):
        self.assertEqual(set(DT.TALENTOS), set(D.CLASSES))
        self.assertEqual(len(D.CLASSES), 8)
        self.assertEqual(len(D.ORIGENS), 8)
        for cl, dados in DT.TALENTOS.items():
            self.assertEqual(len(dados["caminhos"]), 2, cl)
            self.assertEqual(len(dados["talentos"]), 6, cl)
            for cam in dados["caminhos"].values():
                for tid in cam["prioridade"]:
                    self.assertIn(tid, dados["talentos"], cl)

    def test_proximo_respeita_caminho_e_limite(self):
        for cl in D.CLASSES:
            for cam, _, _ in T.caminhos(cl):
                tal = {}
                for _ in range(400):
                    tid = T.proximo(cl, cam, tal)
                    if tid is None:
                        break
                    tal[tid] = tal.get(tid, 0) + 1
                self.assertTrue(all(v <= T.RANK_MAX for v in tal.values()))
                # os talentos prioritários do caminho recebem mais graus
                pri = DT.TALENTOS[cl]["caminhos"][cam]["prioridade"]
                self.assertGreaterEqual(sum(tal.get(k, 0) for k in pri), 0.8 * sum(tal.values()))

    def test_caminho_invalido_cai_no_padrao(self):
        self.assertEqual(T.caminho_valido("monge", "xyz"), T.caminho_padrao("monge"))

    def test_talentos_concedidos_e_afetam_derivados(self):
        m = novo_motor(semente=3)
        m.silencioso = True
        antes = m.derivados()["dano"]
        m.avancar(2 * 86400, passo=3.0)
        self.assertGreaterEqual(T.total(m.p["talentos"]), m.p["nivel"] // 5)
        self.assertTrue(T.efeitos(m.p["classe"], m.p["talentos"]))
        self.assertGreater(m.derivados()["dano"], antes)

    def test_caminho_escolhido_na_criacao(self):
        attrs = criacao.aplicar_origem(criacao.rolar_atributos(random.Random(1), "penitente"), "marcas")
        m = Motor.novo("A", "marcas", "penitente", attrs, caminho="martirio")
        self.assertEqual(m.p["caminho"], "martirio")
        m2 = Motor.novo("A", "marcas", "penitente", attrs, caminho="lixo")
        self.assertEqual(m2.p["caminho"], T.caminho_padrao("penitente"))


class TestNovasVocacoesOrigens(unittest.TestCase):
    def test_todas_as_vocacoes_jogam(self):
        for cl in D.CLASSES:
            for o in list(D.ORIGENS)[:8:3]:
                attrs = criacao.aplicar_origem(criacao.rolar_atributos(random.Random(1), cl), o)
                m = Motor.novo("T", o, cl, attrs, semente=1)
                m.silencioso = True
                m.avancar(3600, passo=2.0)
                self.assertGreater(m.s["stats"]["abates"], 50, cl)


class TestMigracao(BaseComPasta):
    def _v1(self):
        with open(os.path.join(AQUI, "fixtures", "save_v1.json"), encoding="utf-8") as f:
            return json.load(f)

    def test_save_v1_carrega_e_continua(self):
        estado = self._v1()
        self.assertEqual(estado.get("versao"), 1)
        nivel = estado["personagem"]["nivel"]
        m, _ = retomar(estado)
        self.assertEqual(set(m.p["equip"]), set(D.SLOTS))
        self.assertIn("talentos", m.p)
        self.assertGreaterEqual(T.total(m.p["talentos"]), nivel // 5)
        self.assertGreaterEqual(m.p["nivel"], nivel)
        m.silencioso = True
        m.avancar(7200, passo=2.0)
        self.assertGreaterEqual(m.p["pv"], 1.0)

    def test_v1_vira_v2_ao_salvar_e_normalizacao_idempotente(self):
        m, _ = retomar(self._v1())
        P.salvar(m.s)
        s2 = P.carregar()
        self.assertEqual(s2["versao"], P.VERSAO_SAVE)
        m2, _ = retomar(s2)
        self.assertEqual(json.dumps(m.p["talentos"], sort_keys=True), json.dumps(m2.p["talentos"], sort_keys=True))
        self.assertEqual(set(m2.p["equip"]), set(D.SLOTS))

    def test_save_atual_ida_e_volta(self):
        m = novo_motor(semente=8)
        m.silencioso = True
        m.avancar(6 * 3600, passo=2.0)
        P.salvar(m.s)
        m2, _ = retomar(P.carregar())
        self.assertEqual(m2.p["nivel"], m.p["nivel"])
        self.assertEqual(m2.p["talentos"], m.p["talentos"])


class TestLongoPrazo(unittest.TestCase):
    def test_heroi_segue_evoluindo_por_semanas(self):
        m = novo_motor("monge", semente=5)
        m.silencioso = True
        niveis = []
        for _ in range(4):
            m.avancar(7 * 86400, passo=8.0)
            niveis.append(m.p["nivel"])
            self.assertGreaterEqual(m.p["pv"], 1.0)
        self.assertEqual(niveis, sorted(niveis))
        self.assertGreater(niveis[-1], niveis[0] + 20)


if __name__ == "__main__":
    unittest.main()
