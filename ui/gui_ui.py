# -*- coding: utf-8 -*-
"""Interface gráfica (janela desktop) em tkinter, usada pelo CronicasDeCinzas.exe.

Usa exatamente o mesmo núcleo (core.motor) da versão de terminal.
"""
import random
import sys
import time

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core import criacao, dados as D, itens as I, persistencia as P
from core.motor import Motor, retomar, xp_proximo_nivel, xp_proxima_maestria
from core.util import fmt_dec, fmt_duracao, fmt_num, fmt_relogio, limitar

VELOCIDADES = [1, 2, 5, 10, 30, 100]
AUTOSAVE_S = 30.0

BG = "#14110f"
BG2 = "#1d1815"
FG = "#d8cfc0"
DIM = "#7d7468"
OURO = "#b08d57"
COR_CATEGORIA = {
    "info": DIM, "detalhe": "#5f574d", "combate": FG, "perigo": "#d9a441", "alerta": "#c75a4a",
    "marco": OURO, "item": "#6fb7c9", "forja": "#b57fcf", "nivel": "#7fbf7f", "relato": OURO,
}
COR_RARIDADE = [FG, "#7fbf7f", "#6f9fe0", "#b57fcf", "#e0a43c"]


def _ativar_dpi():
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


def _estilizar(root):
    st = ttk.Style(root)
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass
    st.configure(".", background=BG, foreground=FG, fieldbackground=BG2)
    st.configure("TFrame", background=BG)
    st.configure("TLabel", background=BG, foreground=FG)
    st.configure("Dim.TLabel", background=BG, foreground=DIM)
    st.configure("Ouro.TLabel", background=BG, foreground=OURO, font=("Segoe UI", 11, "bold"))
    st.configure("TButton", background=BG2, foreground=FG, padding=6)
    st.map("TButton", background=[("active", "#2a231e")])
    st.configure("TNotebook", background=BG, borderwidth=0)
    st.configure("TNotebook.Tab", background=BG2, foreground=FG, padding=(12, 6))
    st.map("TNotebook.Tab", background=[("selected", "#2f2720")], foreground=[("selected", OURO)])
    st.configure("TCheckbutton", background=BG, foreground=FG)
    st.configure("TRadiobutton", background=BG, foreground=FG)
    st.configure("TCombobox", fieldbackground=BG2, background=BG2, foreground=FG)
    for nome, cor in (("Vida", "#a63a32"), ("Fadiga", "#c9a23a"), ("Xp", "#4a78b8"), ("Fase", "#3d9aa8")):
        st.configure("%s.Horizontal.TProgressbar" % nome, troughcolor=BG2, background=cor,
                     bordercolor=BG2, lightcolor=cor, darkcolor=cor)


def _texto(parent, **kw):
    t = tk.Text(parent, bg=BG2, fg=FG, insertbackground=FG, relief="flat", wrap="word",
                font=("Consolas", 10), padx=10, pady=8, borderwidth=0, highlightthickness=0, **kw)
    return t


class DialogoCriacao(tk.Toplevel):
    """Criação de personagem: nome, origem, vocação, rolagem ou distribuição de atributos."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Nova jornada")
        self.configure(bg=BG, padx=16, pady=14)
        self.resizable(False, False)
        self.resultado = None
        self.rng = random.Random()
        self._origens = list(D.ORIGENS)
        self._classes = list(D.CLASSES)

        ttk.Label(self, text="Criação de Personagem", style="Ouro.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(self, text="Nome").grid(row=1, column=0, sticky="w", pady=(10, 2))
        self.nome = tk.StringVar(value=self.rng.choice(D.NOMES_SUGERIDOS))
        ttk.Entry(self, textvariable=self.nome, width=26).grid(row=1, column=1, columnspan=2, sticky="we", pady=(10, 2))

        ttk.Label(self, text="Origem").grid(row=2, column=0, sticky="w", pady=2)
        self.cb_origem = ttk.Combobox(self, state="readonly", width=30,
                                      values=[D.ORIGENS[k]["nome"] for k in self._origens])
        self.cb_origem.current(0)
        self.cb_origem.grid(row=2, column=1, columnspan=2, sticky="we", pady=2)
        ttk.Label(self, text="Vocação").grid(row=3, column=0, sticky="w", pady=2)
        self.cb_classe = ttk.Combobox(self, state="readonly", width=30,
                                      values=[D.CLASSES[k]["nome"] for k in self._classes])
        self.cb_classe.current(0)
        self.cb_classe.grid(row=3, column=1, columnspan=2, sticky="we", pady=2)
        self.lbl_desc = ttk.Label(self, style="Dim.TLabel", wraplength=420, justify="left")
        self.lbl_desc.grid(row=4, column=0, columnspan=3, sticky="w", pady=(4, 8))
        self.cb_origem.bind("<<ComboboxSelected>>", lambda e: self._atualizar_desc())
        self.cb_classe.bind("<<ComboboxSelected>>", lambda e: self._rolar_se_preciso())

        self.modo = tk.StringVar(value="rolar")
        ttk.Radiobutton(self, text="Rolagem (4d6, descarta o menor)", variable=self.modo, value="rolar",
                        command=self._mudou_modo).grid(row=5, column=0, columnspan=2, sticky="w")
        ttk.Radiobutton(self, text="Distribuir %d pontos" % criacao.PONTOS_DISTRIBUIVEIS, variable=self.modo,
                        value="dist", command=self._mudou_modo).grid(row=5, column=2, sticky="w")

        self.vars = {}
        self.spins = {}
        for i, a in enumerate(D.ATRIBUTOS):
            ttk.Label(self, text=D.NOMES_ATRIBUTOS[a]).grid(row=6 + i, column=0, sticky="w", pady=1)
            v = tk.IntVar(value=criacao.BASE_ATRIBUTO)
            sp = tk.Spinbox(self, from_=criacao.BASE_ATRIBUTO, to=criacao.MAX_ATRIBUTO_INICIAL, width=5,
                            textvariable=v, command=self._atualizar_restante, bg=BG2, fg=FG,
                            buttonbackground=BG2, relief="flat")
            sp.grid(row=6 + i, column=1, sticky="w", pady=1)
            sp.bind("<KeyRelease>", lambda e: self._atualizar_restante())
            self.vars[a] = v
            self.spins[a] = sp
            ttk.Label(self, text=D.DESC_ATRIBUTOS[a], style="Dim.TLabel", wraplength=300,
                      justify="left").grid(row=6 + i, column=2, sticky="w", padx=(8, 0))
        self.lbl_info = ttk.Label(self, text="", style="Dim.TLabel")
        self.lbl_info.grid(row=11, column=0, columnspan=3, sticky="w", pady=(6, 0))

        barra = ttk.Frame(self)
        barra.grid(row=12, column=0, columnspan=3, sticky="we", pady=(12, 0))
        ttk.Button(barra, text="Rolar novamente", command=self._rolar).pack(side="left")
        ttk.Button(barra, text="Criação rápida", command=self._rapida).pack(side="left", padx=6)
        ttk.Button(barra, text="Iniciar jornada", command=self._confirmar).pack(side="right")

        self._atualizar_desc()
        self._rolar()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_visibility()
        self.grab_set()
        self.focus_force()

    def _origem(self):
        return self._origens[self.cb_origem.current()]

    def _classe(self):
        return self._classes[self.cb_classe.current()]

    def _atualizar_desc(self):
        o, cl = D.ORIGENS[self._origem()], D.CLASSES[self._classe()]
        bonus = ", ".join("+%d %s" % (v, D.NOMES_ATRIBUTOS[k]) for k, v in o["bonus"].items())
        self.lbl_desc.config(text="%s (%s)\n%s\nTécnica: %s" % (o["desc"], bonus, cl["desc"], cl["tecnica"]["nome"]))

    def _mudou_modo(self):
        if self.modo.get() == "rolar":
            self._rolar()
        else:
            for a in D.ATRIBUTOS:
                self.vars[a].set(criacao.BASE_ATRIBUTO)
                self.spins[a].config(state="normal")
            self._atualizar_restante()

    def _rolar_se_preciso(self):
        self._atualizar_desc()
        if self.modo.get() == "rolar":
            self._rolar()

    def _rolar(self):
        if self.modo.get() != "rolar":
            return
        attrs = criacao.rolar_atributos(self.rng, self._classe())
        for a in D.ATRIBUTOS:
            self.spins[a].config(state="normal")
            self.vars[a].set(attrs[a])
            self.spins[a].config(state="disabled")
        self.lbl_info.config(text="Valores rolados e atribuídos conforme a vocação. O bônus de origem é somado ao iniciar.")

    def _valores(self):
        try:
            return {a: int(self.vars[a].get()) for a in D.ATRIBUTOS}
        except (tk.TclError, ValueError):
            return None

    def _atualizar_restante(self):
        attrs = self._valores()
        if attrs is None or self.modo.get() != "dist":
            return
        restante = criacao.BASE_ATRIBUTO * 5 + criacao.PONTOS_DISTRIBUIVEIS - sum(attrs.values())
        self.lbl_info.config(text="Pontos restantes: %d" % restante)

    def _rapida(self):
        nome, origem, classe, attrs = criacao.criacao_rapida(self.rng)
        self._finalizar(nome, origem, classe, attrs)

    def _confirmar(self):
        nome = self.nome.get().strip()[:24]
        if not nome:
            messagebox.showwarning("Nome", "Dê um nome ao seu personagem.", parent=self)
            return
        attrs = self._valores()
        if attrs is None:
            messagebox.showwarning("Atributos", "Valores de atributo inválidos.", parent=self)
            return
        if self.modo.get() == "dist":
            ok, msg = criacao.validar_distribuicao(attrs)
            if not ok:
                messagebox.showwarning("Atributos", msg, parent=self)
                return
        self._finalizar(nome, self._origem(), self._classe(), attrs)

    def _finalizar(self, nome, origem, classe, attrs):
        final = criacao.aplicar_origem(attrs, origem)
        self.resultado = Motor.novo(nome, origem, classe, final)
        self.destroy()


class Aplicacao:
    def __init__(self):
        _ativar_dpi()
        self.root = tk.Tk()
        self.root.title("Crônicas de Cinzas")
        self.root.configure(bg=BG)
        self.root.geometry("980x700")
        self.root.minsize(820, 560)
        _estilizar(self.root)
        self.motor = None
        self.pausado = False
        self.vel_i = 0
        self._ult = time.monotonic()
        self._ult_save = self._ult
        self._ult_cron = 0
        self._ult_aba = None
        self._ult_ui = 0.0
        self.mostrar_detalhes = tk.BooleanVar(value=False)
        self.root.protocol("WM_DELETE_WINDOW", self.sair)

    # --------------------------------------------------------------- início
    def iniciar(self):
        self.root.withdraw()
        motor = self._abrir_jornada()
        if motor is None:
            self.root.destroy()
            return
        self.motor = motor
        self._montar()
        self.root.deiconify()
        self._ult = time.monotonic()
        self.root.after(200, self._tick)
        self.root.mainloop()

    def _abrir_jornada(self):
        if P.existe_save():
            try:
                estado = P.carregar()
            except P.ErroSave as e:
                if not messagebox.askyesno("Save ilegível", "%s\n\nDeseja iniciar uma nova jornada?" % e):
                    return None
                estado = None
            if estado is not None:
                motor, linhas = retomar(estado)
                if linhas:
                    messagebox.showinfo("Relato do intervalo", "\n".join(linhas))
                P.salvar(motor.s)
                return motor
        return self._criar_nova()

    def _criar_nova(self):
        dlg = DialogoCriacao(self.root)
        self.root.wait_window(dlg)
        if dlg.resultado is None:
            return None
        P.salvar(dlg.resultado.s)
        return dlg.resultado

    # ---------------------------------------------------------------- layout
    def _montar(self):
        r = self.root
        topo = ttk.Frame(r)
        topo.pack(fill="x", padx=14, pady=(12, 4))
        self.lbl_nome = ttk.Label(topo, style="Ouro.TLabel")
        self.lbl_nome.pack(anchor="w")
        self.lbl_regiao = ttk.Label(topo, style="Dim.TLabel")
        self.lbl_regiao.pack(anchor="w")

        barras = ttk.Frame(r)
        barras.pack(fill="x", padx=14, pady=4)
        barras.columnconfigure(1, weight=1)
        self.pb = {}
        self.lb = {}
        for i, (chave, rot, estilo) in enumerate((("pv", "Vitalidade", "Vida"), ("fad", "Fadiga", "Fadiga"),
                                                  ("xp", "Experiência", "Xp"), ("fase", "Atividade", "Fase"))):
            ttk.Label(barras, text=rot, width=12).grid(row=i, column=0, sticky="w", pady=2)
            pb = ttk.Progressbar(barras, maximum=1000, style="%s.Horizontal.TProgressbar" % estilo)
            pb.grid(row=i, column=1, sticky="we", padx=6, pady=2)
            lb = ttk.Label(barras, width=30, anchor="w")
            lb.grid(row=i, column=2, sticky="w")
            self.pb[chave], self.lb[chave] = pb, lb
        self.lbl_det = ttk.Label(r, style="Dim.TLabel")
        self.lbl_det.pack(anchor="w", padx=14)

        self.nb = ttk.Notebook(r)
        self.nb.pack(fill="both", expand=True, padx=14, pady=8)
        self.abas = {}
        for chave, titulo in (("cronica", "Crônica"), ("atributos", "Atributos"), ("equip", "Equipamentos"),
                              ("maestrias", "Maestrias"), ("jornada", "Jornada")):
            fr = ttk.Frame(self.nb)
            t = _texto(fr)
            sb = ttk.Scrollbar(fr, command=t.yview)
            t.configure(yscrollcommand=sb.set)
            sb.pack(side="right", fill="y")
            t.pack(side="left", fill="both", expand=True)
            self.nb.add(fr, text=titulo)
            self.abas[chave] = t
        self._chaves_abas = ["cronica", "atributos", "equip", "maestrias", "jornada"]
        for cat, cor in COR_CATEGORIA.items():
            self.abas["cronica"].tag_configure(cat, foreground=cor)
        self.abas["cronica"].tag_configure("hora", foreground="#5f574d")
        for chave in ("atributos", "equip", "maestrias", "jornada"):
            t = self.abas[chave]
            t.tag_configure("ouro", foreground=OURO)
            t.tag_configure("dim", foreground=DIM)
            for i, cor in enumerate(COR_RARIDADE):
                t.tag_configure("rar%d" % i, foreground=cor)
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self._forcar_aba())

        base = ttk.Frame(r)
        base.pack(fill="x", padx=14, pady=(0, 12))
        self.btn_pausa = ttk.Button(base, text="Pausar", command=self.alternar_pausa)
        self.btn_pausa.pack(side="left")
        self.btn_vel = ttk.Button(base, text="Velocidade x1", command=self.ciclar_vel)
        self.btn_vel.pack(side="left", padx=6)
        ttk.Checkbutton(base, text="Detalhes de combate", variable=self.mostrar_detalhes,
                        command=self._recarregar_cronica).pack(side="left", padx=10)
        ttk.Button(base, text="Sair", command=self.sair).pack(side="right")
        ttk.Button(base, text="Reiniciar jornada", command=self.reiniciar).pack(side="right", padx=6)
        ttk.Button(base, text="Importar", command=self.importar).pack(side="right")
        ttk.Button(base, text="Exportar save", command=self.exportar).pack(side="right", padx=6)
        r.bind("<space>", lambda e: self.alternar_pausa())

    # ----------------------------------------------------------------- ações
    def alternar_pausa(self):
        self.pausado = not self.pausado
        self.btn_pausa.config(text="Retomar" if self.pausado else "Pausar")

    def ciclar_vel(self):
        self.vel_i = (self.vel_i + 1) % len(VELOCIDADES)
        self.btn_vel.config(text="Velocidade x%d" % VELOCIDADES[self.vel_i])

    def exportar(self):
        P.salvar(self.motor.s)
        caminho = P.exportar(self.motor.s)
        messagebox.showinfo("Save exportado", "Cópia criada em:\n%s" % caminho)

    def importar(self):
        caminho = filedialog.askopenfilename(title="Importar save", filetypes=[("Save JSON", "*.json")],
                                             initialdir=P.diretorio_dados())
        if not caminho:
            return
        try:
            estado = P.importar(caminho)
        except P.ErroSave as e:
            messagebox.showerror("Importar", str(e))
            return
        if not messagebox.askyesno("Importar", "Isto substituirá a jornada atual (uma cópia será guardada). Continuar?"):
            return
        P.salvar(self.motor.s)
        P.apagar()
        P.salvar(estado)
        self.motor, linhas = retomar(estado)
        if linhas:
            messagebox.showinfo("Relato do intervalo", "\n".join(linhas))
        self._ult_cron = 0
        self._recarregar_cronica()

    def reiniciar(self):
        if not messagebox.askyesno("Reiniciar jornada",
                                   "Isto encerra a jornada atual. Uma cópia será guardada na pasta de exportações.\n\nConfirma?",
                                   icon="warning"):
            return
        if not messagebox.askyesno("Confirmação final", "Tem certeza? Esta é a última confirmação."):
            return
        self.pausado = True
        P.salvar(self.motor.s)
        P.apagar()
        novo = self._criar_nova()
        if novo is None:
            self.root.destroy()
            return
        self.motor = novo
        self.pausado = False
        self.btn_pausa.config(text="Pausar")
        self._ult = time.monotonic()
        self._ult_cron = 0
        self._recarregar_cronica()

    def sair(self):
        try:
            if self.motor:
                P.salvar(self.motor.s)
        finally:
            self.root.destroy()

    # ------------------------------------------------------------- laço
    def _tick(self):
        agora = time.monotonic()
        dt = min(agora - self._ult, 120.0)
        self._ult = agora
        if self.motor and not self.pausado:
            self.motor.avancar(dt * VELOCIDADES[self.vel_i])
        if agora - self._ult_save >= AUTOSAVE_S:
            P.salvar(self.motor.s)
            self._ult_save = agora
        self._atualizar()
        self.root.after(200, self._tick)

    def _forcar_aba(self):
        self._ult_ui = 0.0
        self._atualizar()

    # ------------------------------------------------------------ atualização
    def _atualizar(self):
        m, p = self.motor, self.motor.p
        d = m.derivados()
        cl = D.CLASSES[p["classe"]]
        self.lbl_nome.config(text="%s - %s, %s - Nível %d" % (p["nome"], D.ORIGENS[p["origem"]]["nome"], cl["nome"], p["nivel"]))
        self.lbl_regiao.config(text="%s   |   Tempo de jornada: %s%s" % (
            m.nome_regiao(), fmt_duracao(m.s["tempo_jogado"]), "   |   PAUSADO" if self.pausado else ""))
        rot, frac, det = m.info_fase()
        xpn = xp_proximo_nivel(p["nivel"])
        self._barra("pv", p["pv"] / d["pv_max"], "%d / %d" % (p["pv"], d["pv_max"]))
        self._barra("fad", p["fadiga"] / 100.0, "%d%%" % p["fadiga"])
        self._barra("xp", p["xp"] / xpn, "%d / %d" % (p["xp"], xpn))
        self._barra("fase", frac, rot)
        self.lbl_det.config(text=det)
        aba = self._chaves_abas[self.nb.index(self.nb.select())]
        self._atualizar_cronica()
        agora = time.monotonic()
        if aba != "cronica" and agora - self._ult_ui >= 1.0:
            self._ult_ui = agora
            getattr(self, "_aba_" + aba)()

    def _barra(self, chave, frac, texto):
        self.pb[chave]["value"] = limitar(frac, 0, 1) * 1000
        self.lb[chave].config(text=texto)

    # ----------------------------------------------------------------- crônica
    def _recarregar_cronica(self):
        t = self.abas["cronica"]
        t.config(state="normal")
        t.delete("1.0", "end")
        t.config(state="disabled")
        self._ult_cron = 0
        self._atualizar_cronica()

    def _atualizar_cronica(self):
        s = self.motor.s
        novos = [e for e in s["cronica"] if e["n"] > self._ult_cron]
        if not novos:
            return
        self._ult_cron = novos[-1]["n"]
        t = self.abas["cronica"]
        no_fim = t.yview()[1] >= 0.98
        t.config(state="normal")
        for e in novos:
            if e["c"] == "detalhe" and not self.mostrar_detalhes.get():
                continue
            t.insert("end", "[%s] " % fmt_relogio(e["t"]), "hora")
            t.insert("end", e["m"] + "\n", e["c"])
        # mantém o widget leve: no máximo 600 linhas
        linhas = int(t.index("end-1c").split(".")[0])
        if linhas > 600:
            t.delete("1.0", "%d.0" % (linhas - 600))
        t.config(state="disabled")
        if no_fim:
            t.see("end")

    # ------------------------------------------------------------------ abas
    def _preencher(self, chave, partes):
        """partes: lista de (texto, tag|None)."""
        t = self.abas[chave]
        topo = t.yview()[0]
        t.config(state="normal")
        t.delete("1.0", "end")
        for txt, tag in partes:
            t.insert("end", txt, tag) if tag else t.insert("end", txt)
        t.config(state="disabled")
        t.yview_moveto(topo)

    def _aba_atributos(self):
        m, p = self.motor, self.motor.p
        d = m.derivados()
        partes = [("Atributos\n", "ouro")]
        for a in D.ATRIBUTOS:
            extra = d["atributos"][a] - p["atributos"][a]
            partes.append(("%-11s %3d" % (D.NOMES_ATRIBUTOS[a], p["atributos"][a]), None))
            partes.append(("  (+%s equip.)" % fmt_num(extra) if extra > 0 else "", "rar2"))
            partes.append(("   %s\n" % D.DESC_ATRIBUTOS[a], "dim"))
        partes.append(("\nDerivados\n", "ouro"))
        tec = D.CLASSES[p["classe"]]["tecnica"]
        linhas = [
            "Vitalidade máxima    %s" % fmt_num(d["pv_max"]),
            "Dano por golpe       %s" % fmt_num(d["dano"]),
            "Defesa               %s" % fmt_num(d["defesa"]),
            "Precisão base        %d%%" % round(d["acerto"] * 100),
            "Chance de crítico    %s%%" % fmt_dec(d["crit"] * 100),
            "Intervalo do ciclo   %ss" % fmt_dec(d["ciclo"], 2),
            "Recuperação          %s%% da vitalidade por segundo" % fmt_dec(d["regen"] * 100),
            "Resistência à fadiga x%s" % fmt_dec(d["resist"], 2),
            "Fragmentos           %d" % p["fragmentos"],
            "",
            "Técnica: %s (x%s de dano a cada %d golpes)" % (tec["nome"], fmt_dec(tec["mult"]), tec["cd"]),
        ]
        partes.append(("\n".join(linhas) + "\n", None))
        self._preencher("atributos", partes)

    def _aba_equip(self):
        p = self.motor.p
        partes = [("Equipamentos\n\n", "ouro")]
        for slot in D.SLOTS:
            it = p["equip"].get(slot)
            partes.append(("%-9s " % D.NOMES_SLOTS[slot], None))
            if not it:
                partes.append(("(vazio)\n", "dim"))
                continue
            partes.append((I.rotulo(it), "rar%d" % it["raridade"]))
            partes.append(("  [%s, nível %d]\n" % (D.RARIDADES[it["raridade"]], it["ilvl"]), "dim"))
            rot = {"arma": "Dano", "armadura": "Defesa", "reliquia": "Vigor"}[slot]
            efeitos = ["%s +%s" % (rot, fmt_num(I.poder(it) * (2.5 if slot == "reliquia" else 1)))]
            efeitos += ["%s +%s" % (D.NOMES_ATRIBUTOS[a], fmt_num(v)) for a, v in I.afixos(it).items()]
            partes.append(("          " + " | ".join(efeitos) + "\n", None))
            if it["refino"] < D.REFINO_MAX:
                partes.append(("          Refino +%d: próximo custa %d fragmentos (%d%% de êxito)\n\n" % (
                    it["refino"], I.custo_refino(it),
                    round(I.chance_refino(it, self.motor.derivados()["forja"]) * 100)), "dim"))
            else:
                partes.append(("          Refino no máximo (+%d)\n\n" % D.REFINO_MAX, "dim"))
        partes.append(("Fragmentos disponíveis: %d\n" % p["fragmentos"], "ouro"))
        self._preencher("equip", partes)

    def _aba_maestrias(self):
        p = self.motor.p
        partes = [("Maestrias (evoluem sozinhas com o uso)\n\n", "ouro")]
        for k, defn in D.MAESTRIAS.items():
            mm = p["maestrias"][k]
            if mm["nivel"] < D.NIVEL_MAX_MAESTRIA:
                pct = int(100 * mm["xp"] / xp_proxima_maestria(mm["nivel"]))
            else:
                pct = 100
            partes.append(("%-26s Nv %2d  (%d%%)\n" % (defn["nome"], mm["nivel"], pct), None))
            partes.append(("   %s\n" % defn["desc"], "dim"))
        self._preencher("maestrias", partes)

    def _aba_jornada(self):
        m, s = self.motor, self.motor.s
        partes = [("Regiões\n", "ouro")]
        for i, reg in enumerate(D.REGIOES):
            if s["ciclo"] > 0 or i < s["regiao"]:
                marca, tag = "[x]", "rar1"
            elif i == s["regiao"]:
                marca, tag = "[>]", "ouro"
            else:
                marca, tag = "[ ]", "dim"
            partes.append(("%s %-32s níveis %d-%d\n" % (marca, reg["nome"], reg["nivel_base"], reg["nivel_chefe"]), tag))
        st = s["stats"]
        partes.append(("\nEstatísticas\n", "ouro"))
        partes.append(("Abates: %d (guardiões: %d)\nLéguas percorridas: %d\nRecuos: %d\n"
                       "Itens obtidos: %d | desmontados: %d\nRefinos: %d bem-sucedidos, %d falhos\n"
                       "Dano causado: %s | sofrido: %s | maior golpe: %s | críticos: %d\n" % (
                           st["abates"], st["chefes"], int(st["leguas"]), st["recuos"], st["itens"], st["desmontados"],
                           st["refinos_ok"], st["refinos_falha"], fmt_num(st["dano_causado"]),
                           fmt_num(st["dano_sofrido"]), fmt_num(st["maior_golpe"]), st["criticos"]), None))
        partes.append(("\nMarcos alcançados (%d)\n" % len(s["marcos"]), "ouro"))
        for mc in s["marcos"]:
            partes.append(("[%s] %s\n" % (fmt_relogio(mc["t"]), mc["texto"]), "dim"))
        self._preencher("jornada", partes)


def executar():
    app = Aplicacao()
    app.iniciar()
    return 0
