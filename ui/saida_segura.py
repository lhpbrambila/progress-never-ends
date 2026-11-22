# -*- coding: utf-8 -*-
"""Salvamento automático quando o jogo é encerrado "de fora".

Cobre o caso de fechar a janela do console no X (o .bat ou o .exe de terminal), logoff e
desligamento do Windows e, em sistemas POSIX, SIGHUP/SIGTERM.

Como funciona: o aviso chega por uma rotina do sistema (no Windows, numa thread à parte).
Ela NÃO mexe no estado do jogo: só pede ao laço principal que encerre (``encerrar``) e espera
o laço terminar de salvar (``salvo``). Assim só uma thread grava no save, sem travas.
O Windows dá cerca de 5 segundos entre o aviso e o encerramento forçado; se o laço não
responder a tempo, a própria rotina grava como último recurso.
"""
import signal
import sys
import threading

from core import persistencia as P

CTRL_CLOSE_EVENT = 2
CTRL_LOGOFF_EVENT = 5
CTRL_SHUTDOWN_EVENT = 6
LIMITE_ESPERA_S = 3.0


class ProtecaoDeSaida:
    def __init__(self, motor):
        self.motor = motor
        self.encerrar = threading.Event()   # pedido de encerramento (vindo do sistema)
        self.salvo = threading.Event()      # o laço já gravou o save final
        self._rotina_win = None
        self._sinais_antigos = {}

    # ------------------------------------------------------------ ciclo de vida
    def __enter__(self):
        if sys.platform.startswith("win"):
            self._instalar_windows()
        else:
            self._instalar_posix()
        return self

    def __exit__(self, *args):
        if self._rotina_win is not None:
            try:
                import ctypes
                ctypes.windll.kernel32.SetConsoleCtrlHandler(self._rotina_win, False)
            except Exception:
                pass
            self._rotina_win = None
        for sig, antigo in self._sinais_antigos.items():
            try:
                signal.signal(sig, antigo)
            except Exception:
                pass
        self._sinais_antigos = {}

    # ------------------------------------------------------------ laço principal
    def finalizar(self):
        """Chamado pelo laço ao sair: se o encerramento veio de fora, grava e avisa a rotina."""
        if not self.encerrar.is_set():
            return
        try:
            P.salvar(self.motor.s)
        except Exception:
            pass
        finally:
            self.salvo.set()

    # --------------------------------------------------------------- aviso externo
    def _ao_fechar(self):
        """Roda na thread da rotina do sistema (Windows) ou é chamada por testes."""
        self.encerrar.set()
        if not self.salvo.wait(LIMITE_ESPERA_S):
            try:   # o laço não respondeu a tempo: grava aqui, como último recurso
                P.salvar(self.motor.s)
            except Exception:
                pass

    def _instalar_windows(self):
        import ctypes
        from ctypes import wintypes
        tipo = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)

        def rotina(evento):
            if evento in (CTRL_CLOSE_EVENT, CTRL_LOGOFF_EVENT, CTRL_SHUTDOWN_EVENT):
                self._ao_fechar()
                return True
            return False    # Ctrl+C / Ctrl+Break seguem o caminho normal (KeyboardInterrupt)

        self._rotina_win = tipo(rotina)   # guardar a referência evita que o coletor a destrua
        k32 = ctypes.windll.kernel32
        k32.SetConsoleCtrlHandler.argtypes = [tipo, wintypes.BOOL]
        k32.SetConsoleCtrlHandler.restype = wintypes.BOOL
        k32.SetConsoleCtrlHandler(self._rotina_win, True)

    def _instalar_posix(self):
        def tratador(numero, quadro):
            self.encerrar.set()   # o laço percebe em até 50 ms e salva

        for nome in ("SIGHUP", "SIGTERM"):
            sig = getattr(signal, nome, None)
            if sig is None:
                continue
            try:
                self._sinais_antigos[sig] = signal.signal(sig, tratador)
            except (ValueError, OSError):   # fora da thread principal
                pass
