# -*- coding: utf-8 -*-
"""Afixos de inimigos e fases dos guardiões."""

# Multiplicadores opcionais: hp, dano, vel (intervalo de ataque: menor = mais rápido).
AFIXOS = {
    "venenoso": {
        "nome": "Venenoso", "desc": "Seus golpes envenenam.",
        "ativa": "O golpe de {inimigo} deixa um veneno ardente em suas veias.",
    },
    "regenerador": {
        "nome": "Regenerador", "desc": "Recupera vitalidade durante o combate.",
        "ativa": "As feridas de {inimigo} se fecham diante dos seus olhos.",
    },
    "espinhoso": {
        "nome": "Espinhoso", "desc": "Devolve parte do dano que recebe.",
        "ativa": "Espinhos rasgam sua mão ao golpear {inimigo} ({dano} de dano devolvido).",
    },
    "impiedoso": {
        "nome": "Impiedoso", "desc": "Golpes mais fortes, que atravessam parte da defesa.",
        "ativa": "{inimigo} golpeia sem piedade, atravessando sua guarda.",
        "dano": 1.0,
    },
    "blindado": {
        "nome": "Blindado", "desc": "Reduz muito o dano recebido.",
        "ativa": "Seu golpe ressoa em vão contra a carapaça de {inimigo}.",
        "hp": 1.1,
    },
    "veloz": {
        "nome": "Veloz", "desc": "Ataca em intervalos muito menores.",
        "ativa": "{inimigo} se move depressa demais para os olhos.",
        "vel": 0.72, "dano": 0.85,
    },
    "sanguinario": {
        "nome": "Sanguinário", "desc": "Recupera vitalidade com os golpes que acerta.",
        "ativa": "{inimigo} se recompõe com o sangue que arranca de você.",
    },
    "aterrador": {
        "nome": "Aterrador", "desc": "Cada golpe esgota o fôlego.",
        "ativa": "O olhar de {inimigo} lhe tira o fôlego.",
    },
    "insepulto": {
        "nome": "Insepulto", "desc": "Levanta-se uma vez depois de abatido.",
        "ativa": "{inimigo} cai, mas algo o arrasta de volta à vida!",
    },
}

# Chaves de efeito de fase: dano (mult cumulativo), vel (mult cumulativo), escudo (fração do hp máx.),
# cura (fração do hp máx.), afixo (id adicionado). 'limiar' = fração de vitalidade restante.
FASES_GUARDIAO = [
    # 0 - Capitão Sem Nome
    [
        {"limiar": 0.60, "texto": "O Capitão rasga o próprio estandarte e investe sem guarda alguma.", "dano": 1.25},
        {"limiar": 0.25, "texto": "Ferido, o Capitão ergue a espada com as duas mãos. Cada golpe agora vale por dois.",
         "dano": 1.25, "vel": 0.85},
    ],
    # 1 - Anciã das Raízes
    [
        {"limiar": 0.66, "texto": "Raízes brotam do solo e envolvem a Anciã como uma casca viva.", "escudo": 0.15},
        {"limiar": 0.33, "texto": "A seiva da Anciã se torna veneno e escorre de seus dedos.", "afixo": "venenoso"},
    ],
    # 2 - Magistrado Sepulto
    [
        {"limiar": 0.70, "texto": "O Magistrado lê em voz alta a sua condenação. Sua voz pesa como chumbo.", "dano": 1.2},
        {"limiar": 0.40, "texto": "Sinos mudos ressoam sob as ruínas: os guardas sepultos respondem ao chamado.", "escudo": 0.20},
        {"limiar": 0.15, "texto": "A sentença final é proferida. O Magistrado já não faz questão de ser justo.",
         "dano": 1.25, "vel": 0.85},
    ],
    # 3 - Leviatã de Breu
    [
        {"limiar": 0.66, "texto": "O breu se agita e cobre as feridas do Leviatã, fechando-as.", "cura": 0.10,
         "afixo": "regenerador"},
        {"limiar": 0.33, "texto": "O Leviatã mergulha e emerge furioso, sacudindo o pântano inteiro.", "dano": 1.3},
    ],
    # 4 - Jarl Congelado
    [
        {"limiar": 0.60, "texto": "A nevasca obedece ao Jarl. O frio rói as juntas e rouba o fôlego.", "afixo": "aterrador"},
        {"limiar": 0.30, "texto": "O gelo que o cobre racha. Por baixo, o Jarl é pura fúria.", "dano": 1.3, "vel": 0.85},
    ],
    # 5 - Rainha Sem Coroa
    [
        {"limiar": 0.66, "texto": "A Rainha chama os cortesãos emparedados, e as paredes respondem.", "escudo": 0.20},
        {"limiar": 0.40, "texto": "Sangue frio escorre pela testa nua da Rainha, que passa a beber do seu.",
         "afixo": "sanguinario"},
        {"limiar": 0.20, "texto": "Sem coroa, sem corte, sem piedade.", "afixo": "impiedoso", "dano": 1.15},
    ],
    # 6 - Fornalheiro Primordial
    [
        {"limiar": 0.70, "texto": "As brasas engolem a forja. O corpo do Fornalheiro agora cospe faíscas.", "afixo": "espinhoso"},
        {"limiar": 0.40, "texto": "A fornalha sopra uma vez mais e reacende o que parecia extinto.", "cura": 0.08, "dano": 1.25},
        {"limiar": 0.15, "texto": "O Fornalheiro se consome na própria chama. Já não se importa com o que queima.",
         "dano": 1.4, "vel": 0.8},
    ],
    # 7 - O Rei que Jamais Foi
    [
        {"limiar": 0.75, "texto": "Uma coroa de ausência se forma sobre a cabeça do Rei, tornando-o mais real.", "escudo": 0.15},
        {"limiar": 0.50, "texto": "O Rei lembra de tudo o que nunca foi, e isso o torna impiedoso.",
         "afixo": "impiedoso", "dano": 1.2},
        {"limiar": 0.25, "texto": "O Vazio responde ao Rei. O salão inteiro se inclina para protegê-lo.",
         "cura": 0.10, "dano": 1.25, "vel": 0.85},
    ],
]
