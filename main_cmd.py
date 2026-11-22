# -*- coding: utf-8 -*-
"""Entrada do executável de terminal (CronicasDeCinzas-CMD.exe, com console)."""
import sys

from main import principal

if __name__ == "__main__":
    sys.exit(principal(modo_padrao="cmd"))
