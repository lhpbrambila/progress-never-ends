# -*- coding: utf-8 -*-
"""Testes do salvamento ao encerrar (fechar a janela do console, SIGTERM, etc.)."""
import os
import random
import signal
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import criacao, persistencia as P
from core.motor import Motor
from ui import saida_segura
from ui.saida_segura import ProtecaoDeSaida


def novo_motor():
    attrs = criacao.aplicar_origem(criacao.rolar_atributos(random.Random(1), "penitente"), "marcas")
    return Motor.novo("Teste", "marcas", "penitente", attrs, semente=1)


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


class TestProtecaoDeSaida(BaseComPasta):
    def test_laco_responde_e_salva(self):
        """Aviso externo -> o laço principal grava e a rotina só devolve depois disso."""
        m = novo_motor()
        m.avancar(90)
        prot = ProtecaoDeSaida(m)

        def laco():
            prot.encerrar.wait(5)
            prot.finalizar()

        t = threading.Thread(target=laco)
        t.start()
        t0 = time.monotonic()
        prot._ao_fechar()
        t.join()
        self.assertLess(time.monotonic() - t0, 2.0)
        self.assertTrue(prot.salvo.is_set())
        self.assertAlmostEqual(P.carregar()["tempo_jogado"], 90.0, places=3)

    def test_sem_resposta_do_laco_grava_como_ultimo_recurso(self):
        m = novo_motor()
        m.avancar(45)
        prot = ProtecaoDeSaida(m)
        antigo = saida_segura.LIMITE_ESPERA_S
        saida_segura.LIMITE_ESPERA_S = 0.2
        try:
            prot._ao_fechar()       # ninguém chama finalizar()
        finally:
            saida_segura.LIMITE_ESPERA_S = antigo
        self.assertAlmostEqual(P.carregar()["tempo_jogado"], 45.0, places=3)

    def test_finalizar_sem_pedido_nao_grava(self):
        prot = ProtecaoDeSaida(novo_motor())
        prot.finalizar()
        self.assertFalse(P.existe_save())

    @unittest.skipIf(sys.platform.startswith("win"), "sinais POSIX")
    def test_sigterm_e_sighup_pedem_encerramento(self):
        for sinal in (signal.SIGTERM, signal.SIGHUP):
            prot = ProtecaoDeSaida(novo_motor())
            antigo = signal.getsignal(sinal)
            with prot:
                os.kill(os.getpid(), sinal)
                for _ in range(50):
                    if prot.encerrar.is_set():
                        break
                    time.sleep(0.01)
                self.assertTrue(prot.encerrar.is_set(), sinal)
            self.assertEqual(signal.getsignal(sinal), antigo)   # tratador original restaurado


if __name__ == "__main__":
    unittest.main()
