# -*- coding: utf-8 -*-
"""Ponto de entrada único de Crônicas de Cinzas.

    python main.py            -> janela gráfica (ou terminal, se tkinter não existir)
    python main.py --cmd      -> interface de terminal
    python main.py --gui      -> janela gráfica
    python main.py --ascii    -> terminal sem caracteres de moldura Unicode
    python main.py --dir PATH -> usa outra pasta para os saves
"""
import argparse
import os
import sys

from core import dados as D


def _analisar(argv):
    ap = argparse.ArgumentParser(prog="CronicasDeCinzas", description=D.NOME_JOGO + " - RPG idle sombrio")
    modo = ap.add_mutually_exclusive_group()
    modo.add_argument("--cmd", action="store_true", help="abre a interface de terminal")
    modo.add_argument("--gui", action="store_true", help="abre a interface gráfica")
    ap.add_argument("--ascii", action="store_true", help="usa apenas caracteres ASCII nas molduras")
    ap.add_argument("--dir", help="pasta para saves e exportações")
    ap.add_argument("--versao", action="store_true", help="mostra a versão e sai")
    return ap.parse_args(argv)


def principal(argv=None, modo_padrao="gui"):
    if sys.stdout is None:   # executável com janela (sem console)
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    args = _analisar(argv)
    if args.versao:
        print("%s %s" % (D.NOME_JOGO, D.VERSAO))
        return 0
    if args.dir:
        os.environ["CRONICAS_DIR"] = args.dir
    modo = "cmd" if args.cmd else "gui" if args.gui else modo_padrao
    if modo == "gui":
        try:
            from ui import gui_ui
        except ImportError:
            print("tkinter não está disponível; abrindo a versão de terminal.")
            modo = "cmd"
        else:
            return gui_ui.executar()
    from ui import cmd_ui
    return cmd_ui.executar(ascii_only=args.ascii)


if __name__ == "__main__":
    sys.exit(principal())
