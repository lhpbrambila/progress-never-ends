# -*- coding: utf-8 -*-
"""Testes do núcleo: simulação, persistência, progresso offline e criação.

Execute com:  python -m unittest discover -s tests -v
"""
import copy
import json
import os
import random
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import criacao, dados as D, persistencia as P
from core.motor import Motor, OFFLINE_MAX_S, retomar


def novo_motor(classe="penitente", origem="marcas", semente=1):
    attrs = criacao.aplicar_origem(criacao.rolar_atributos(random.Random(semente), classe), origem)
    return Motor.novo("Teste", origem, classe, attrs, semente=semente)


class BaseComPasta(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._antigo = os.environ.get("VIGILIA_DIR")
        os.environ["VIGILIA_DIR"] = self._tmp.name

    def tearDown(self):
        if self._antigo is None:
            os.environ.pop("VIGILIA_DIR", None)
        else:
            os.environ["VIGILIA_DIR"] = self._antigo
        self._tmp.cleanup()


class TestSimulacao(unittest.TestCase):
    def test_determinismo_com_mesma_semente(self):
        a, b = novo_motor(semente=4), novo_motor(semente=4)
        a.avancar(1800)
        b.avancar(1800)
        self.assertEqual(a.s["personagem"]["nivel"], b.s["personagem"]["nivel"])
        self.assertEqual(a.s["stats"]["abates"], b.s["stats"]["abates"])

    def test_tempo_decorrido_e_exato(self):
        m = novo_motor()
        for _ in range(100):
            m.avancar(0.1)
        self.assertAlmostEqual(m.s["tempo_jogado"], 10.0, places=6)

    def test_invariantes_em_longa_simulacao(self):
        for classe in D.CLASSES:
            m = novo_motor(classe, semente=3)
            m.silencioso = True
            for _ in range(12):
                m.avancar(3600, passo=1.0)
                p = m.p
                d = m.derivados()
                self.assertGreaterEqual(p["pv"], 1.0 - 1e-9)
                self.assertLessEqual(p["pv"], d["pv_max"] + 1e-6)
                self.assertGreaterEqual(p["fadiga"], 0.0)
                self.assertLessEqual(p["fadiga"], 100.0)
                self.assertIn(m.s["fase"], ("marcha", "combate", "recuperacao", "forja", "consolidacao"))
            self.assertGreater(p["nivel"], 10, classe)
            self.assertGreater(m.s["stats"]["abates"], 300, classe)

    def test_progride_pelas_regioes_e_registra_marcos(self):
        m = novo_motor("cacador", semente=2)
        m.silencioso = True
        m.avancar(24 * 3600, passo=1.0)
        ids = [x["id"] for x in m.s["marcos"]]
        self.assertIn("guardiao_0_0", ids)
        self.assertGreaterEqual(m.s["regiao"] + 8 * m.s["ciclo"], 4)

    def test_cronica_limitada(self):
        m = novo_motor()
        m.avancar(7200)
        self.assertLessEqual(len(m.s["cronica"]), 300)
        ns = [e["n"] for e in m.s["cronica"]]
        self.assertEqual(ns, sorted(ns))

    def test_textos_em_portugues_sem_marcadores_pendentes(self):
        m = novo_motor()
        m.avancar(3600)
        for e in m.s["cronica"]:
            self.assertNotIn("{", e["m"])
            self.assertNotIn("}", e["m"])


class TestCriacao(unittest.TestCase):
    def test_distribuicao_valida_e_invalida(self):
        ok = criacao.distribuicao_inicial()
        self.assertFalse(criacao.validar_distribuicao(ok)[0])      # faltam pontos
        ok["forca"] += 20
        self.assertFalse(criacao.validar_distribuicao(ok)[0])      # acima do máximo
        ok["forca"] -= 10
        ok["vontade"] += 10
        self.assertTrue(criacao.validar_distribuicao(ok)[0])

    def test_rolagem_dentro_dos_limites(self):
        rng = random.Random(1)
        for _ in range(200):
            for v in criacao.rolar_atributos(rng, "sacerdote").values():
                self.assertTrue(3 <= v <= 18)

    def test_origem_soma_bonus(self):
        base = criacao.distribuicao_inicial()
        final = criacao.aplicar_origem(base, "marcas")
        self.assertEqual(final["vontade"], 10)
        self.assertEqual(base["vontade"], 8)   # não altera o original


class TestPersistencia(BaseComPasta):
    def test_ida_e_volta(self):
        m = novo_motor()
        m.avancar(600)
        P.salvar(m.s)
        lido = P.carregar()
        self.assertEqual(lido["personagem"]["nivel"], m.p["nivel"])
        self.assertEqual(lido["cronica"], m.s["cronica"])
        # o estado carregado continua jogável
        m2 = Motor(lido, semente=1)
        m2.avancar(60)

    def test_save_corrompido_recorre_ao_backup(self):
        m = novo_motor()
        P.salvar(m.s)
        m.avancar(300)
        P.salvar(m.s)                       # cria o .bak com o save anterior
        with open(P.caminho_save(), "w", encoding="utf-8") as f:
            f.write("{ isto não é json")
        lido = P.carregar()
        self.assertIsNotNone(lido)

    def test_sem_save_retorna_none(self):
        self.assertIsNone(P.carregar())
        self.assertFalse(P.existe_save())

    def test_ambos_corrompidos_levanta_erro(self):
        for caminho in (P.caminho_save(), P.caminho_backup()):
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("lixo")
        with self.assertRaises(P.ErroSave):
            P.carregar()

    def test_exportar_importar(self):
        m = novo_motor()
        m.avancar(120)
        caminho = P.exportar(m.s)
        self.assertTrue(os.path.exists(caminho))
        self.assertEqual(P.importar(caminho)["personagem"]["nome"], "Teste")
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump({"versao": 99}, f)
        with self.assertRaises(P.ErroSave):
            P.importar(caminho)

    def test_reset_guarda_copia(self):
        m = novo_motor()
        P.salvar(m.s)
        P.apagar()
        self.assertFalse(P.existe_save())
        pasta = os.path.join(P.diretorio_dados(), "exportacoes")
        self.assertTrue(any(n.startswith("save_anterior_") for n in os.listdir(pasta)))

    def test_escrita_atomica_nao_deixa_tmp(self):
        P.salvar(novo_motor().s)
        self.assertFalse(os.path.exists(P.caminho_save() + ".tmp"))


class TestOffline(BaseComPasta):
    def _estado_antigo(self, segundos):
        m = novo_motor()
        m.avancar(60)
        s = copy.deepcopy(m.s)
        s["salvo_em"] = time.time() - segundos
        return s

    def test_ausencia_curta_nao_gera_relatorio(self):
        s = self._estado_antigo(10)
        motor, linhas = retomar(s)
        self.assertEqual(linhas, [])

    def test_ausencia_longa_progride_e_reporta(self):
        s = self._estado_antigo(3 * 3600)
        antes = s["personagem"]["nivel"]
        t_antes = s["tempo_jogado"]
        motor, linhas = retomar(s, semente=5)
        self.assertTrue(linhas)
        self.assertIn("ausente", linhas[0])
        self.assertGreater(motor.p["nivel"], antes)
        self.assertAlmostEqual(motor.s["tempo_jogado"] - t_antes, 3 * 3600, delta=2)
        self.assertEqual(motor.s["cronica"][-1]["c"], "relato")

    def test_limite_de_24h(self):
        s = self._estado_antigo(5 * 24 * 3600)
        t_antes = s["tempo_jogado"]
        motor, linhas = retomar(s, semente=5)
        self.assertAlmostEqual(motor.s["tempo_jogado"] - t_antes, OFFLINE_MAX_S, delta=2)
        self.assertTrue(any("primeiras" in l for l in linhas))

    def test_offline_nao_enche_a_cronica(self):
        s = self._estado_antigo(6 * 3600)
        motor, _ = retomar(s, semente=5)
        permitidas = {"marco", "alerta", "relato"}
        novas = [e for e in motor.s["cronica"] if e["n"] > s["cron_n"]]
        self.assertTrue(all(e["c"] in permitidas for e in novas))


if __name__ == "__main__":
    unittest.main()
