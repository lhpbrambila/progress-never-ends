# -*- coding: utf-8 -*-
"""Dados de equipamentos: poder por slot, afixos nomeados, conjuntos, itens únicos e narrativa.

Todos os efeitos percentuais usam as mesmas chaves (ver NOMES_EFEITO) e são somados em
``Motor.efeitos_totais()``. Valores são frações: 0.04 = +4%.
"""

# (base, por nível de item): poder = (base + por_nivel * ilvl) * multiplicador de raridade
PODER_SLOT = {
    "arma": (3.0, 1.6), "armadura": (2.0, 1.5), "elmo": (1.5, 1.0),
    "botas": (1.0, 0.8), "anel": (2.0, 1.0), "reliquia": (2.0, 1.0),
}
PESO_SLOT = {"arma": 0.22, "armadura": 0.18, "elmo": 0.15, "botas": 0.15, "anel": 0.15, "reliquia": 0.15}
ROTULO_PODER = {"arma": "Dano", "armadura": "Defesa", "elmo": "Defesa", "botas": "Agilidade",
                "anel": "Acuidade", "reliquia": "Vigor"}
DESC_SLOT = {
    "arma": "aumenta o dano de cada golpe",
    "armadura": "reduz o dano recebido",
    "elmo": "reforça a defesa",
    "botas": "aumenta a esquiva",
    "anel": "aumenta a chance de crítico",
    "reliquia": "aumenta a vitalidade máxima",
}

INICIAIS = {
    "armadura": "Gibão Remendado", "elmo": "Capuz Puído", "botas": "Bota Remendada",
    "anel": "Anel de Latão Fosco", "reliquia": "Medalhão Sem Brilho",
}

# chave -> sufixo exibido depois do valor em %
NOMES_EFEITO = {
    "dano_pct": "de dano",
    "defesa_pct": "de defesa",
    "crit": "de chance de crítico",
    "crit_dano": "de dano crítico",
    "pv_pct": "de vitalidade máxima",
    "regen_pct": "de recuperação",
    "esquiva": "de esquiva",
    "xp_pct": "de experiência",
    "fragmentos_pct": "de fragmentos",
    "dano_chefe_pct": "de dano contra guardiões",
    "roubo_vida": "do dano causado vira vitalidade",
    "resist_veneno": "de resistência a veneno",
    "reducao_dano": "a menos de dano sofrido",
    "vel_marcha_pct": "de velocidade de marcha",
    "fadiga_red": "de resistência à fadiga",
    "tecnica_pct": "de dano da técnica",
    "precisao": "de precisão",
    "forja": "de êxito no refino",
}

# ---------------------------------------------------------------- afixos nomeados
MODS = {
    "crueldade": {"nome": "Crueldade", "efeito": "dano_pct", "base": 0.04,
                  "slots": ["arma", "anel", "reliquia"], "lore": "Feito para quem nunca aprendeu a perdoar."},
    "sede_sangue": {"nome": "Sede de Sangue", "efeito": "roubo_vida", "base": 0.012,
                    "slots": ["arma", "anel"], "lore": "O metal parece beber o que toca."},
    "golpe_certeiro": {"nome": "Golpe Certeiro", "efeito": "crit", "base": 0.02,
                       "slots": ["arma", "anel", "elmo"], "lore": "Procura o ponto onde a guarda cede."},
    "fio_impiedoso": {"nome": "Fio Impiedoso", "efeito": "crit_dano", "base": 0.06,
                      "slots": ["arma", "anel"], "lore": "Quando acerta, não deixa dúvidas."},
    "carrasco_reis": {"nome": "Carrasco de Reis", "efeito": "dano_chefe_pct", "base": 0.06,
                      "slots": ["arma", "elmo", "anel"], "lore": "Gravado com os nomes de tronos que tombaram."},
    "pele_ferro": {"nome": "Pele de Ferro", "efeito": "defesa_pct", "base": 0.04,
                   "slots": ["armadura", "elmo", "botas"], "lore": "Temperado até esquecer o que é ferida."},
    "coracao_obstinado": {"nome": "Coração Obstinado", "efeito": "pv_pct", "base": 0.035,
                          "slots": ["armadura", "reliquia", "elmo"], "lore": "Bate mesmo quando já não deveria."},
    "manto_sombras": {"nome": "Manto de Sombras", "efeito": "reducao_dano", "base": 0.015,
                      "slots": ["armadura", "botas", "reliquia"], "lore": "Os golpes parecem errar de endereço."},
    "sangue_frio": {"nome": "Sangue Frio", "efeito": "resist_veneno", "base": 0.15,
                    "slots": ["armadura", "elmo", "botas", "reliquia"], "lore": "O veneno encontra pouco o que corroer."},
    "passo_leve": {"nome": "Passo Leve", "efeito": "esquiva", "base": 0.02,
                   "slots": ["botas", "armadura"], "lore": "Quem o veste raramente deixa pegadas."},
    "marcha_peregrino": {"nome": "Marcha do Peregrino", "efeito": "vel_marcha_pct", "base": 0.04,
                         "slots": ["botas"], "lore": "As léguas passam como se fossem passos."},
    "folego_antigo": {"nome": "Fôlego Antigo", "efeito": "regen_pct", "base": 0.06,
                      "slots": ["reliquia", "armadura", "botas"], "lore": "Ensina o corpo a descansar depressa."},
    "mente_vigilante": {"nome": "Mente Vigilante", "efeito": "fadiga_red", "base": 0.05,
                        "slots": ["elmo", "reliquia", "botas"], "lore": "O cansaço chega tarde a quem vigia."},
    "saber_esquecidos": {"nome": "Saber dos Esquecidos", "efeito": "xp_pct", "base": 0.02,
                         "slots": ["elmo", "anel", "reliquia"], "lore": "Cada derrota alheia vira lição sua."},
    "olho_garimpeiro": {"nome": "Olho de Garimpeiro", "efeito": "fragmentos_pct", "base": 0.08,
                        "slots": ["anel", "elmo", "reliquia"], "lore": "Encontra valor onde outros veem escombros."},
    "mao_ferreiro": {"nome": "Mão de Ferreiro", "efeito": "forja", "base": 0.015,
                     "slots": ["anel", "arma", "reliquia"], "lore": "Lembra a paciência de quem o forjou."},
}

# ------------------------------------------------------------ narrativa genérica
LORE_ITEM = {
    "arma": [
        "O cabo guarda a marca de mãos que já não existem.",
        "Dizem que foi empunhada em uma guerra cujo nome ninguém mais lembra.",
        "A lâmina tem um brilho cansado, como quem viu demais.",
        "Há um nome riscado perto do guarda-mão, e ninguém o decifra.",
        "Pesa mais do que deveria, e você aprendeu a não perguntar por quê.",
    ],
    "armadura": [
        "Cada amassado conta uma luta que alguém sobreviveu.",
        "Cheira a fumaça antiga e a juramentos mal cumpridos.",
        "As correias foram remendadas por mãos que sabiam o que faziam.",
        "Veste-se como se fosse uma segunda pele, e igualmente difícil de largar.",
        "Quem a usou antes não a perdeu em combate.",
    ],
    "elmo": [
        "Por dentro, alguém gravou uma prece curta e desesperada.",
        "O metal ainda guarda o eco de gritos que ninguém ouviu.",
        "Limita a visão, mas poupa de ver o que vem depois.",
        "Tem uma fenda antiga, de um golpe que não chegou a matar.",
        "Foi feito para um rosto que o tempo apagou.",
    ],
    "botas": [
        "A sola gasta lembra estradas que já não levam a lugar nenhum.",
        "Caminharam léguas demais para terem sido feitas para um só dono.",
        "Fazem pouco ruído, o que nestas terras vale ouro.",
        "O couro tem a cor da cinza e a paciência de quem espera.",
        "Há lama de cinco regiões nas costuras.",
    ],
    "anel": [
        "Uma aliança que sobreviveu à pessoa a quem foi prometida.",
        "Gelado ao toque, mesmo ao lado da fogueira.",
        "O sinete está tão gasto que já não se lê o brasão.",
        "Aperta o dedo como uma lembrança que se recusa a soltar.",
        "Foi retirado de uma mão que não o queria entregar.",
    ],
    "reliquia": [
        "Para alguns, um objeto de fé; para outros, apenas um peso no peito.",
        "Pulsa de leve nas noites sem vento.",
        "Guarda algo que foi sagrado antes de o mundo esquecer o motivo.",
        "Ninguém sabe a quem reza quem o carrega, mas ele escuta.",
        "Foi enterrado com alguém importante e desenterrado por alguém desesperado.",
    ],
}

# ------------------------------------------------------------------ conjuntos
# Um conjunto por região. 'bonus': peças -> efeitos. Peças: slot -> nome.
SETS = {
    "luto": {
        "nome": "Vestes do Luto", "regiao": 0,
        "lore": "Costuradas por viúvas das Charnecas, para que os vivos carregassem o peso dos mortos.",
        "pecas": {"armadura": "Gibão do Luto", "elmo": "Capuz do Luto", "botas": "Bota do Luto", "anel": "Anel do Luto"},
        "bonus": {2: {"pv_pct": 0.06}, 4: {"defesa_pct": 0.10, "reducao_dano": 0.03}},
    },
    "corvos": {
        "nome": "Mortalha dos Corvos", "regiao": 1,
        "lore": "Tecida com penas de aves que jamais cantaram, para quem anda sem ser ouvido.",
        "pecas": {"armadura": "Mortalha de Penas Negras", "elmo": "Máscara de Bico Longo",
                  "botas": "Bota de Garras", "reliquia": "Pena do Corvo Silencioso"},
        "bonus": {2: {"esquiva": 0.04}, 4: {"crit": 0.05, "crit_dano": 0.15}},
    },
    "magistrado": {
        "nome": "Regalia do Magistrado", "regiao": 2,
        "lore": "Insígnias de uma justiça que sobreviveu ao reino que a instituiu.",
        "pecas": {"armadura": "Toga Sepulta", "elmo": "Barrete de Juiz", "anel": "Sinete de Sentença",
                  "arma": "Cetro do Magistrado"},
        "bonus": {2: {"xp_pct": 0.05}, 4: {"dano_chefe_pct": 0.15, "fragmentos_pct": 0.15}},
    },
    "breu": {
        "nome": "Couraça de Breu", "regiao": 3,
        "lore": "Endurecida no lodo do pântano, e por isso difícil de ferir e de matar.",
        "pecas": {"armadura": "Couraça de Breu Seco", "elmo": "Elmo de Lodo Endurecido",
                  "botas": "Greva do Pântano", "reliquia": "Frasco de Breu Vivo"},
        "bonus": {2: {"resist_veneno": 0.30}, 4: {"regen_pct": 0.20, "pv_pct": 0.06}},
    },
    "gigantes": {
        "nome": "Armadura dos Gigantes", "regiao": 4,
        "lore": "Ossos de gigantes que o gelo conservou, lapidados por quem queria ser maior que o frio.",
        "pecas": {"armadura": "Peitoral de Osso de Gigante", "elmo": "Elmo de Mandíbula Gélida",
                  "botas": "Bota de Peles Gélidas", "arma": "Machado de Costela Gélida"},
        "bonus": {2: {"defesa_pct": 0.08}, 4: {"dano_pct": 0.10, "fadiga_red": 0.10}},
    },
    "rainha": {
        "nome": "Insígnias da Rainha", "regiao": 5,
        "lore": "Emblemas de uma dinastia emparedada viva, que ainda exige reverência.",
        "pecas": {"arma": "Adaga da Corte Emparedada", "anel": "Anel da Dinastia",
                  "elmo": "Diadema Partido", "reliquia": "Relicário Real"},
        "bonus": {2: {"crit": 0.04}, 4: {"roubo_vida": 0.03, "dano_pct": 0.08}},
    },
    "brasas": {
        "nome": "Brasas do Fornalheiro", "regiao": 6,
        "lore": "Forjadas no coração do Abismo, ainda guardam o calor de uma primeira chama.",
        "pecas": {"arma": "Martelo de Brasa", "armadura": "Avental de Forja Primordial",
                  "botas": "Bota de Cinza Quente", "anel": "Anel de Ferro Rubro"},
        "bonus": {2: {"dano_pct": 0.06}, 4: {"tecnica_pct": 0.20, "crit_dano": 0.20}},
    },
    "ausencia": {
        "nome": "Ausência do Rei", "regiao": 7,
        "lore": "Pertenceram a ninguém, e é essa ausência que lhes dá peso.",
        "pecas": {"armadura": "Manto Sem Dono", "elmo": "Véu do Vazio", "anel": "Anel de Ninguém",
                  "reliquia": "Relíquia da Ausência"},
        "bonus": {2: {"pv_pct": 0.06}, 4: {"dano_pct": 0.08, "defesa_pct": 0.08, "xp_pct": 0.06}},
    },
}
SET_POR_REGIAO = ["luto", "corvos", "magistrado", "breu", "gigantes", "rainha", "brasas", "ausencia"]

# --------------------------------------------------------------- itens únicos
UNICOS = {
    "espada_sem_nome": {
        "nome": "Espada Sem Nome", "slot": "arma", "regiao": 0, "guardiao": "Capitão Sem Nome",
        "lore": "O aço sem brasão lembra a todos que o caminho sempre pertenceu a quem o atravessou.",
        "efeito": {"dano_chefe_pct": 0.20},
    },
    "anel_raiz_viva": {
        "nome": "Anel de Raiz Viva", "slot": "anel", "regiao": 1, "guardiao": "Anciã das Raízes",
        "lore": "Uma raiz fina ainda cresce em torno do aro, indiferente a quem o veste.",
        "efeito": {"regen_pct": 0.25, "resist_veneno": 0.30},
    },
    "sinete_magistrado": {
        "nome": "Sinete do Magistrado Sepulto", "slot": "reliquia", "regiao": 2, "guardiao": "Magistrado Sepulto",
        "lore": "Cada sentença lavrada com ele ainda pesa em algum lugar do mundo.",
        "efeito": {"xp_pct": 0.10},
    },
    "bota_leviata": {
        "nome": "Bota de Pele de Leviatã", "slot": "botas", "regiao": 3, "guardiao": "Leviatã de Breu",
        "lore": "Nada que afunda a segura por muito tempo.",
        "efeito": {"resist_veneno": 0.50, "esquiva": 0.06},
    },
    "elmo_jarl": {
        "nome": "Elmo Coroado do Jarl", "slot": "elmo", "regiao": 4, "guardiao": "Jarl Congelado",
        "lore": "O gelo que o cobre jamais derrete, e protege de tudo, menos da solidão.",
        "efeito": {"reducao_dano": 0.06, "fadiga_red": 0.15},
    },
    "manto_rainha": {
        "nome": "Manto Funéreo da Rainha", "slot": "armadura", "regiao": 5, "guardiao": "Rainha Sem Coroa",
        "lore": "Bordado com fios de uma dinastia inteira, e pesado como ela.",
        "efeito": {"reducao_dano": 0.05, "pv_pct": 0.08},
    },
    "martelo_fornalheiro": {
        "nome": "Martelo do Fornalheiro", "slot": "arma", "regiao": 6, "guardiao": "Fornalheiro Primordial",
        "lore": "Cada golpe soa como o primeiro metal batido no primeiro fogo.",
        "efeito": {"roubo_vida": 0.04, "crit_dano": 0.25},
    },
    "coroa_nunca_usada": {
        "nome": "Coroa Que Nunca Foi Usada", "slot": "elmo", "regiao": 7, "guardiao": "O Rei que Jamais Foi",
        "lore": "Não repousou sobre cabeça alguma, e por isso serve a qualquer um que a mereça.",
        "efeito": {"dano_pct": 0.10, "xp_pct": 0.08, "fragmentos_pct": 0.15},
    },
}
UNICO_POR_REGIAO = ["espada_sem_nome", "anel_raiz_viva", "sinete_magistrado", "bota_leviata",
                    "elmo_jarl", "manto_rainha", "martelo_fornalheiro", "coroa_nunca_usada"]
