# -*- coding: utf-8 -*-
"""Funções utilitárias de formatação, independentes de interface."""


def fmt_duracao(segundos):
    segundos = int(max(0, segundos))
    d, resto = divmod(segundos, 86400)
    h, resto = divmod(resto, 3600)
    m, s = divmod(resto, 60)
    if d:
        return "%dd %02dh %02dm" % (d, h, m)
    if h:
        return "%dh %02dm %02ds" % (h, m, s)
    return "%02dm %02ds" % (m, s)


def fmt_relogio(segundos):
    segundos = int(max(0, segundos))
    h, resto = divmod(segundos, 3600)
    m, s = divmod(resto, 60)
    return "%02d:%02d:%02d" % (h, m, s)


def romano(n):
    valores = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for v, s in valores:
        while n >= v:
            out += s
            n -= v
    return out or "I"


def fmt_num(x):
    """Número compacto: 1234 -> 1.234; 1.5 -> 1,5."""
    if abs(x) >= 100:
        return "{:,}".format(int(round(x))).replace(",", ".")
    return ("%.1f" % x).replace(".", ",")


def limitar(x, minimo, maximo):
    return max(minimo, min(maximo, x))


def fmt_dec(x, casas=1):
    """Decimal com vírgula: fmt_dec(7.34) -> '7,3'."""
    return ("%.*f" % (casas, x)).replace(".", ",")
