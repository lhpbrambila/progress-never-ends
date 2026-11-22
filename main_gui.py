# -*- coding: utf-8 -*-
"""Entrada do executável gráfico (UltimaVigilia.exe, sem janela de console)."""
import sys

from main import principal

if __name__ == "__main__":
    sys.exit(principal(modo_padrao="gui"))
