# -*- coding: utf-8 -*-
"""Interface de terminal (cmd.exe / Windows Terminal) com ANSI, sem flicker.

A tela é redesenhada de uma só vez (cursor para o canto + limpeza de fim de linha), a
~4 quadros por segundo, e as teclas são lidas sem bloquear a simulação.
"""
import os
import re
import shutil
import sys
import textwrap
import time

from core import criacao, dados as D, itens as I, persistencia as P
from core.motor import Motor, retomar, FASES, xp_proximo_nivel, xp_proxima_maestria, OFFLINE_MAX_S
from core.util import fmt_dec, fmt_duracao, fmt_num, fmt_relogio, limitar, romano

import random

VELOCIDADES = [1, 2, 5, 10, 30, 100]
AUTOSAVE_S = 30.0

# ----------------------------------------------------------------- ANSI
RESET = "\x1b[0m"
CORES = {
    "dim": "\x1b[90m", "red": "\x1b[91m", "green": "\x1b[92m", "yellow": "\x1b[93m",
    "blue": "\x1b[94m", "mag": "\x1b[95m", "cyan": "\x1b[96m", "white": "\x1b[97m",
    "gold": "\x1b[38;5;178m", "bold": "\x1b[1m",
}
COR_CATEGORIA = {
    "info": "dim", "detalhe": "dim", "combate": "white", "perigo": "yellow", "alerta": "red",
    "marco": "gold", "item": "cyan", "forja": "mag", "nivel": "green", "relato": "gold",
}
COR_RARIDADE = ["white", "green", "blue", "mag", "gold"]
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def c(texto, cor):
    return CORES[cor] + str(texto) + RESET


def vis_len(s):
    return len(_ANSI_RE.sub("", s))


def pad(s, largura):
    return s + " " * max(0, largura - vis_len(s))


class Estilo:
    def __init__(self, ascii_only):
        if ascii_only:
            self.tl, self.tr, self.bl, self.br, self.h, self.v = "+", "+", "+", "+", "-", "|"
            self.cheio, self.vazio = "#", "."
        else:
            self.tl, self.tr, self.bl, self.br, self.h, self.v = "╔", "╗", "╚", "╝", "═", "║"
            self.cheio, self.vazio = "█", "░"

    def barra(self, frac, largura, cor):
        n = int(round(limitar(frac, 0, 1) * largura))
        return c(self.cheio * n, cor) + c(self.vazio * (largura - n), "dim")

    def caixa(self, titulo, linhas, largura):
        interno = largura - 2
        t = " %s " % titulo if titulo else ""
        topo = self.tl + c(t, "gold") + self.h * (interno - len(t)) + self.tr
        out = [topo]
        for ln in linhas:
            if vis_len(ln) + 1 > interno:
                ln = _cortar(ln, interno - 1)
            out.append(self.v + pad(" " + ln, interno) + self.v)
        out.append(self.bl + self.h * interno + self.br)
        return out


def _cortar(s, n):
    """Corta uma string com ANSI preservando códigos até n caracteres visíveis."""
    out, vis, i = "", 0, 0
    while i < len(s) and vis < n:
        m = _ANSI_RE.match(s, i)
        if m:
            out += m.group(0)
            i = m.end()
        else:
            out += s[i]
            vis += 1
            i += 1
    return out + RESET


# ------------------------------------------------------------ terminal / teclado
def preparar_terminal():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if sys.platform.startswith("win"):
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            k32.SetConsoleOutputCP(65001)
            h = k32.GetStdHandle(-11)
            modo = ctypes.c_uint32()
            if k32.GetConsoleMode(h, ctypes.byref(modo)):
                k32.SetConsoleMode(h, modo.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        except Exception:
            os.system("")  # fallback clássico que ativa ANSI em versões recentes
        try:
            os.system("title Crônicas de Cinzas")
        except Exception:
            pass


class Teclado:
    """Leitura de teclas sem bloqueio, em Windows (msvcrt) e POSIX (termios)."""

    def __enter__(self):
        self.win = sys.platform.startswith("win")
        if not self.win and sys.stdin.isatty():
            import termios
            import tty
            self._termios = termios
            self._fd = sys.stdin.fileno()
            self._antigo = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        else:
            self._antigo = None
        return self

    def __exit__(self, *a):
        if self._antigo is not None:
            self._termios.tcsetattr(self._fd, self._termios.TCSADRAIN, self._antigo)

    def ler(self):
        if self.win:
            import msvcrt
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\x00", "\xe0"):
                    msvcrt.getwch()
                    return ""
                return ch
            return None
        if self._antigo is None:
            return None
        import select
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None


# --------------------------------------------------------------- criação
def perguntar(msg, padrao=None):
    try:
        r = input(msg).strip()
    except EOFError:
        r = ""
    return r or (padrao if padrao is not None else "")


def escolher(titulo, opcoes):
    """opcoes: lista de (chave, rótulo, descrição). Retorna a chave escolhida."""
    print("\n" + c(titulo, "gold"))
    for i, (_, rot, desc) in enumerate(opcoes, 1):
        print("  %d) %s - %s" % (i, c(rot, "white"), desc))
    while True:
        r = perguntar("Escolha [1-%d]: " % len(opcoes))
        if r.isdigit() and 1 <= int(r) <= len(opcoes):
            return opcoes[int(r) - 1][0]
        print(c("Opção inválida.", "red"))


def mostrar_atributos(attrs, titulo="Atributos"):
    print(c("\n" + titulo, "gold"))
    for a in D.ATRIBUTOS:
        print("  %-11s %3d   %s" % (D.NOMES_ATRIBUTOS[a], attrs[a], c(D.DESC_ATRIBUTOS[a], "dim")))


def distribuir_manual():
    attrs = criacao.distribuicao_inicial()
    print("\nDistribua %d pontos entre os atributos (cada um entre %d e %d)." % (
        criacao.PONTOS_DISTRIBUIVEIS, criacao.BASE_ATRIBUTO, criacao.MAX_ATRIBUTO_INICIAL))
    restante = criacao.PONTOS_DISTRIBUIVEIS
    for a in D.ATRIBUTOS:
        while True:
            r = perguntar("%s (atual %d, restam %d pontos) - pontos a somar: " % (
                D.NOMES_ATRIBUTOS[a], attrs[a], restante), "0")
            if r.isdigit() and int(r) <= restante and attrs[a] + int(r) <= criacao.MAX_ATRIBUTO_INICIAL:
                attrs[a] += int(r)
                restante -= int(r)
                break
            print(c("Valor inválido.", "red"))
    if restante:
        # sobra: coloca onde couber, em ordem, para fechar exatamente 20 pontos
        for a in D.ATRIBUTOS:
            while restante and attrs[a] < criacao.MAX_ATRIBUTO_INICIAL:
                attrs[a] += 1
                restante -= 1
    return attrs


def criar_personagem():
    rng = random.Random()
    print(c("\n=== Criação de Personagem ===", "gold"))
    modo = escolher("Como deseja começar?", [
        ("rapida", "Criação rápida", "tudo sorteado, a jornada começa em segundos"),
        ("manual", "Criação completa", "você escolhe nome, origem, vocação e atributos"),
    ])
    if modo == "rapida":
        nome, origem, classe, attrs = criacao.criacao_rapida(rng)
    else:
        nome = perguntar("\nNome do personagem: ", rng.choice(D.NOMES_SUGERIDOS))[:24]
        origem = escolher("Origem", [(k, v["nome"], v["desc"]) for k, v in D.ORIGENS.items()])
        classe = escolher("Vocação", [(k, v["nome"], v["desc"]) for k, v in D.CLASSES.items()])
        metodo = escolher("Atributos", [
            ("rolar", "Rolagem", "5 rolagens de 4d6 (descarta o menor), atribuídas conforme a vocação"),
            ("dist", "Distribuição", "você reparte %d pontos livremente" % criacao.PONTOS_DISTRIBUIVEIS),
        ])
        if metodo == "rolar":
            attrs = criacao.rolar_atributos(rng, classe)
            while True:
                mostrar_atributos(attrs, "Resultado da rolagem")
                if perguntar("Aceitar? [S/n]: ", "s").lower().startswith("s"):
                    break
                attrs = criacao.rolar_atributos(rng, classe)
        else:
            attrs = distribuir_manual()
    final = criacao.aplicar_origem(attrs, origem)
    mostrar_atributos(final, "Atributos finais (com bônus de origem)")
    print("\n%s - %s, %s" % (c(nome, "white"), D.ORIGENS[origem]["nome"], D.CLASSES[classe]["nome"]))
    perguntar("\nPressione Enter para iniciar a jornada...")
    return Motor.novo(nome, origem, classe, final)


# ----------------------------------------------------------- telas do jogo
class Tela:
    def __init__(self, motor, ascii_only=False):
        self.m = motor
        self.e = Estilo(ascii_only)
        self.vista = "painel"
        self.vel_i = 0
        self.pausado = False
        self.detalhes = False
        self.msg = ""
        self.msg_ate = 0.0
        self.confirmando = None   # "reset" ou "sair"

    # ---------- utilidades
    @property
    def largura(self):
        cols = shutil.get_terminal_size((100, 30)).columns
        return max(64, min(cols - 1, 110))

    @property
    def altura(self):
        return shutil.get_terminal_size((100, 30)).lines

    def aviso(self, texto, seg=4.0):
        self.msg = texto
        self.msg_ate = time.monotonic() + seg

    def _linha_barra(self, rot, frac, texto, cor, larg):
        bw = max(10, larg - 34)
        return "%-12s %s %s" % (rot, self.e.barra(frac, bw, cor), texto)

    # ---------- cabeçalho
    def cabecalho(self, W):
        m, p = self.m, self.m.p
        d = m.derivados()
        cl = D.CLASSES[p["classe"]]
        vel = VELOCIDADES[self.vel_i]
        estado = c("|| PAUSADO", "yellow") if self.pausado else c("> x%d" % vel, "green")
        t1 = "%s  %s, %s  Nível %d" % (c(p["nome"], "white"), D.ORIGENS[p["origem"]]["nome"], cl["nome"], p["nivel"])
        t2 = "%s   Tempo de jornada: %s   %s" % (c(m.nome_regiao(), "gold"), fmt_duracao(m.s["tempo_jogado"]), estado)
        rot, frac, det = m.info_fase()
        xpn = xp_proximo_nivel(p["nivel"])
        linhas = [
            t1, t2,
            self._linha_barra("Vitalidade", p["pv"] / d["pv_max"],
                              "%d/%d" % (p["pv"], d["pv_max"]), "red", W),
            self._linha_barra("Fadiga", p["fadiga"] / 100.0, "%d%%" % p["fadiga"], "yellow", W),
            self._linha_barra("Experiência", p["xp"] / xpn, "%d/%d" % (p["xp"], xpn), "blue", W),
            self._linha_barra("Atividade", frac, c(rot, "cyan"), "cyan", W),
            c(det, "dim"),
        ]
        return self.e.caixa("CRÔNICAS DE CINZAS", linhas, W)

    def rodape(self, W):
        itens = ("[P]ausa [V]elocidade [1]Painel [2]Atributos [3]Equip. [4]Maestrias [5]Jornada "
                 "[6]Crônica [D]etalhes [X]Exportar [Z]Reiniciar [Q]Sair")
        if self.confirmando == "reset":
            return [c("Reiniciar apaga esta jornada (uma cópia fica em 'exportacoes'). Digite S para confirmar:", "red")]
        if self.confirmando == "sair":
            return [c("Salvar e sair? [S/N]", "yellow")]
        linhas = textwrap.wrap(itens, W)
        if self.msg and time.monotonic() < self.msg_ate:
            linhas.append(c(self.msg, "gold"))
        return linhas

    # ---------- painéis
    def _cronica_linhas(self, W, n):
        filtro = None if self.detalhes else ("detalhe",)
        saida = []
        for ent in self.m.s["cronica"]:
            if filtro and ent["c"] in filtro:
                continue
            cor = COR_CATEGORIA.get(ent["c"], "white")
            prefixo = "[%s] " % fmt_relogio(ent["t"])
            partes = textwrap.wrap(ent["m"], W - 4 - len(prefixo)) or [""]
            saida.append(c(prefixo, "dim") + c(partes[0], cor))
            for extra in partes[1:]:
                saida.append(" " * len(prefixo) + c(extra, cor))
        return saida[-n:] if n > 0 else []

    def painel_cronica(self, W, altura_livre):
        n = max(4, altura_livre - 2)
        linhas = self._cronica_linhas(W, n)
        while len(linhas) < n:
            linhas.insert(0, "")
        return self.e.caixa("CRÔNICA", linhas, W)

    def painel_atributos(self, W):
        m, p = self.m, self.m.p
        d = m.derivados()
        base = p["atributos"]
        L = []
        for a in D.ATRIBUTOS:
            extra = d["atributos"][a] - base[a]
            L.append("%-11s %3d %s   %s" % (D.NOMES_ATRIBUTOS[a], base[a],
                                             c("(+%s equip.)" % fmt_num(extra), "cyan") if extra > 0 else "           ",
                                             c(D.DESC_ATRIBUTOS[a], "dim")))
        L.append("")
        L += [
            "Vitalidade máxima   %s" % fmt_num(d["pv_max"]),
            "Dano por golpe      %s   (técnica: %s)" % (fmt_num(d["dano"]), D.CLASSES[p["classe"]]["tecnica"]["nome"]),
            "Defesa              %s" % fmt_num(d["defesa"]),
            "Precisão base       %d%%" % round(d["acerto"] * 100),
            "Chance de crítico   %s%%" % fmt_dec(d["crit"] * 100),
            "Intervalo do ciclo  %ss" % fmt_dec(d["ciclo"], 2),
            "Recuperação         %s%% da vitalidade/s" % fmt_dec(d["regen"] * 100),
            "Resistência fadiga  x%s" % fmt_dec(d["resist"], 2),
            "Fragmentos          %d" % p["fragmentos"],
        ]
        return self.e.caixa("ATRIBUTOS E DERIVADOS", L, W)

    def painel_equip(self, W):
        p = self.m.p
        L = []
        for slot in D.SLOTS:
            it = p["equip"].get(slot)
            if not it:
                L.append("%-9s (vazio)" % D.NOMES_SLOTS[slot])
                continue
            cor = COR_RARIDADE[it["raridade"]]
            L.append("%-9s %s  %s" % (D.NOMES_SLOTS[slot], c(I.rotulo(it), cor),
                                     c("[%s, nível %d]" % (D.RARIDADES[it["raridade"]], it["ilvl"]), "dim")))
            rot_poder = {"arma": "Dano", "armadura": "Defesa", "reliquia": "Vigor"}[slot]
            partes = ["%s +%s" % (rot_poder, fmt_num(I.poder(it) * (2.5 if slot == "reliquia" else 1)))]
            partes += ["%s +%s" % (D.NOMES_ATRIBUTOS[a], fmt_num(v)) for a, v in I.afixos(it).items()]
            L.append("          " + c(" | ".join(partes), "dim"))
            if it["refino"] < D.REFINO_MAX:
                L.append("          Refino +%d  (próximo: %d fragmentos, %d%% de êxito)" % (
                    it["refino"], I.custo_refino(it),
                    round(I.chance_refino(it, self.m.derivados()["forja"]) * 100)))
            else:
                L.append("          Refino no máximo (+%d)" % D.REFINO_MAX)
        L += ["", "Fragmentos disponíveis: %d" % p["fragmentos"]]
        return self.e.caixa("EQUIPAMENTOS", L, W)

    def painel_maestrias(self, W):
        p = self.m.p
        tec = D.CLASSES[p["classe"]]["tecnica"]
        L = [c("Técnica: %s" % tec["nome"], "gold") +
             c("  (x%s de dano a cada %d golpes)" % (fmt_dec(tec["mult"]), tec["cd"]), "dim"), ""]
        for k, defn in D.MAESTRIAS.items():
            mm = p["maestrias"][k]
            frac = mm["xp"] / xp_proxima_maestria(mm["nivel"]) if mm["nivel"] < D.NIVEL_MAX_MAESTRIA else 1
            L.append("%-26s Nv %2d %s" % (defn["nome"], mm["nivel"], self.e.barra(frac, 14, "green")))
            L.append("   " + c(defn["desc"], "dim"))
        return self.e.caixa("MAESTRIAS", L, W)

    def painel_jornada(self, W):
        m, s = self.m, self.m.s
        L = []
        for i, reg in enumerate(D.REGIOES):
            if s["ciclo"] > 0 or i < s["regiao"]:
                marca = c("[x]", "green")
            elif i == s["regiao"]:
                marca = c("[>]", "gold")
            else:
                marca = c("[ ]", "dim")
            L.append("%s %-32s níveis %d-%d" % (marca, reg["nome"], reg["nivel_base"], reg["nivel_chefe"]))
        L += ["", c("Estatísticas", "gold")]
        st = s["stats"]
        L += [
            "Abates %d (guardiões %d) | Léguas %d | Recuos %d" % (st["abates"], st["chefes"], int(st["leguas"]), st["recuos"]),
            "Itens %d | Desmontados %d | Refinos %d ok / %d falhos" % (
                st["itens"], st["desmontados"], st["refinos_ok"], st["refinos_falha"]),
            "Dano causado %s | Dano sofrido %s | Maior golpe %s | Críticos %d" % (
                fmt_num(st["dano_causado"]), fmt_num(st["dano_sofrido"]), fmt_num(st["maior_golpe"]), st["criticos"]),
            "", c("Marcos alcançados (%d)" % len(s["marcos"]), "gold"),
        ]
        for mc in s["marcos"][-8:]:
            for parte in textwrap.wrap(mc["texto"], W - 8):
                L.append(c("* " + parte, "gold"))
        return self.e.caixa("JORNADA", L, W)

    # ---------- composição
    def desenhar(self):
        W = self.largura
        linhas = self.cabecalho(W)
        rod = self.rodape(W)
        livre = self.altura - len(linhas) - len(rod) - 1
        v = self.vista
        if v == "painel":
            corpo = self.painel_cronica(W, livre)
        elif v == "atributos":
            corpo = self.painel_atributos(W)
        elif v == "equip":
            corpo = self.painel_equip(W)
        elif v == "maestrias":
            corpo = self.painel_maestrias(W)
        elif v == "jornada":
            corpo = self.painel_jornada(W)
        else:
            corpo = self.painel_cronica(W, self.altura - 4)
            linhas = []
            livre = 0
        saida = linhas + corpo + rod
        saida = saida[: max(5, self.altura - 1)]
        return "\x1b[H" + "".join(l + "\x1b[K\n" for l in saida) + "\x1b[J"


def tratar_tecla(tela, k, motor):
    """Retorna 'sair' quando o jogador confirma a saída."""
    if tela.confirmando == "reset":
        if k.lower() == "s":
            return "reset"
        tela.confirmando = None
        tela.aviso("Reinício cancelado.")
        return None
    if tela.confirmando == "sair":
        if k.lower() == "s":
            return "sair"
        tela.confirmando = None
        return None
    k = k.lower()
    mapa = {"1": "painel", "2": "atributos", "3": "equip", "4": "maestrias", "5": "jornada", "6": "cronica"}
    if k in mapa:
        tela.vista = mapa[k]
    elif k == "p":
        tela.pausado = not tela.pausado
    elif k == "v":
        tela.vel_i = (tela.vel_i + 1) % len(VELOCIDADES)
        tela.aviso("Velocidade x%d" % VELOCIDADES[tela.vel_i])
    elif k == "d":
        tela.detalhes = not tela.detalhes
        tela.aviso("Detalhes de combate: %s" % ("ligados" if tela.detalhes else "desligados"))
    elif k == "x":
        P.salvar(motor.s)
        caminho = P.exportar(motor.s)
        tela.aviso("Save exportado: %s" % caminho, 8)
    elif k == "z":
        tela.confirmando = "reset"
    elif k == "q":
        tela.confirmando = "sair"
    return None


def laco_jogo(motor, ascii_only=False):
    tela = Tela(motor, ascii_only)
    sys.stdout.write("\x1b[?25l\x1b[2J")   # esconde cursor, limpa tela
    sys.stdout.flush()
    ult = time.monotonic()
    ult_save = ult
    ult_draw = 0.0
    resultado = "sair"
    try:
        with Teclado() as kb:
            while True:
                k = kb.ler()
                if k:
                    acao = tratar_tecla(tela, k, motor)
                    if acao:
                        resultado = acao
                        break
                    ult_draw = 0.0
                agora = time.monotonic()
                dt = min(agora - ult, 120.0)
                ult = agora
                if not tela.pausado and tela.confirmando != "reset":
                    motor.avancar(dt * VELOCIDADES[tela.vel_i])
                if agora - ult_save >= AUTOSAVE_S:
                    P.salvar(motor.s)
                    ult_save = agora
                if agora - ult_draw >= 0.25:
                    sys.stdout.write(tela.desenhar())
                    sys.stdout.flush()
                    ult_draw = agora
                time.sleep(0.05)
    except KeyboardInterrupt:
        resultado = "sair"
    finally:
        sys.stdout.write("\x1b[?25h" + RESET + "\x1b[2J\x1b[H")
        sys.stdout.flush()
    return resultado


def mostrar_relatorio(linhas):
    if not linhas:
        return
    print(c("\n=== Relato do intervalo ===", "gold"))
    for ln in linhas:
        print("  " + ln)
    perguntar("\nPressione Enter para continuar...")


def menu_inicial():
    """Retorna o Motor a ser jogado, ou None para sair."""
    print(c("\n  CRÔNICAS DE CINZAS", "gold") + c("   v%s" % D.VERSAO, "dim"))
    print(c("  Uma jornada que continua mesmo quando você não está olhando.\n", "dim"))
    while True:
        tem = P.existe_save()
        opcoes = []
        if tem:
            opcoes.append(("continuar", "Continuar jornada", "retoma o save e aplica o progresso offline"))
        opcoes += [("nova", "Nova jornada", "cria um personagem" + (" (o save atual vira cópia em 'exportacoes')" if tem else "")),
                   ("importar", "Importar save", "carrega um arquivo exportado anteriormente"),
                   ("sair", "Sair", "")]
        acao = escolher("Menu", opcoes)
        if acao == "sair":
            return None
        if acao == "continuar":
            try:
                estado = P.carregar()
            except P.ErroSave as e:
                print(c(str(e), "red"))
                continue
            motor, linhas = retomar(estado)
            mostrar_relatorio(linhas)
            return motor
        if acao == "nova":
            if tem and perguntar("Isso substituirá o save atual. Confirma? [s/N]: ", "n").lower() != "s":
                continue
            if tem:
                P.apagar()
            motor = criar_personagem()
            P.salvar(motor.s)
            return motor
        if acao == "importar":
            caminho = perguntar("Caminho do arquivo .json: ").strip('"')
            try:
                estado = P.importar(caminho)
            except P.ErroSave as e:
                print(c(str(e), "red"))
                continue
            if tem:
                if perguntar("Substituir o save atual? [s/N]: ", "n").lower() != "s":
                    continue
                P.apagar()
            P.salvar(estado)
            motor, linhas = retomar(estado)
            mostrar_relatorio(linhas)
            return motor


def executar(ascii_only=False):
    preparar_terminal()
    while True:
        motor = menu_inicial()
        if motor is None:
            return 0
        res = laco_jogo(motor, ascii_only)
        P.salvar(motor.s)
        if res == "reset":
            P.apagar()
            print(c("Jornada encerrada. Uma cópia foi guardada na pasta 'exportacoes'.", "gold"))
            continue
        print(c("Jornada salva. Que as cinzas lhe sejam leves.", "gold"))
        return 0
