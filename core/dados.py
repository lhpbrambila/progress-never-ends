# -*- coding: utf-8 -*-
"""Dados estáticos do jogo: atributos, origens, classes, maestrias, regiões e textos.

Todo o conteúdo narrativo fica aqui, em português do Brasil, separado da lógica.
"""

VERSAO = "1.0.0"
NOME_JOGO = "A Última Vigília"

# ---------------------------------------------------------------- atributos
ATRIBUTOS = ["forca", "destreza", "vitalidade", "intelecto", "vontade"]
NOMES_ATRIBUTOS = {
    "forca": "Força",
    "destreza": "Destreza",
    "vitalidade": "Vitalidade",
    "intelecto": "Intelecto",
    "vontade": "Vontade",
}
DESC_ATRIBUTOS = {
    "forca": "Potência bruta dos golpes e peso que o corpo suporta.",
    "destreza": "Precisão, chance de golpe crítico e rapidez dos ciclos de combate.",
    "vitalidade": "Reserva de vida e resistência física às feridas.",
    "intelecto": "Poder arcano, auxilia o crítico e a leitura do inimigo.",
    "vontade": "Recuperação, resistência à fadiga e firmeza diante do terror.",
}

# ------------------------------------------------------------------ origens
ORIGENS = {
    "marcas": {
        "nome": "Filho das Marcas",
        "desc": "Gente das fronteiras desoladas, criada entre guerras que nunca terminam.",
        "bonus": {"vontade": 2, "vitalidade": 1},
    },
    "vale": {
        "nome": "Povo do Vale Subterrâneo",
        "desc": "Descendentes de mineiros que desceram fundo demais e voltaram diferentes.",
        "bonus": {"vitalidade": 2, "forca": 1},
    },
    "crepusculo": {
        "nome": "Crepuscular",
        "desc": "Povo esguio das florestas sombrias, de olhos acostumados à penumbra.",
        "bonus": {"destreza": 2, "intelecto": 1},
    },
    "cinzas": {
        "nome": "Nascido das Cinzas",
        "desc": "Sobreviventes de cidades queimadas, marcados por visões do que se perdeu.",
        "bonus": {"intelecto": 2, "vontade": 1},
    },
}

# ------------------------------------------------------------------ classes
CLASSES = {
    "penitente": {
        "nome": "Cavaleiro Penitente",
        "desc": "Guerreiro que expia culpas antigas a golpes de espada e silêncio.",
        "principal": "forca",
        "pesos": {"forca": 4, "vitalidade": 3, "vontade": 2, "destreza": 1, "intelecto": 0.5},
        "tecnica": {
            "nome": "Golpe de Contrição", "mult": 2.3, "cd": 5, "cura": 0.0,
            "texto": "Você descarrega {tecnica} sobre {inimigo}: o aço cai como uma sentença ({dano}).",
        },
        "arma": ("Espada de Ferro Gasta", "f"),
    },
    "cacador": {
        "nome": "Caçador de Sombras",
        "desc": "Rastreador solitário que persegue o que a luz abandonou.",
        "principal": "destreza",
        "pesos": {"destreza": 4, "vitalidade": 2, "forca": 1.5, "vontade": 1, "intelecto": 1},
        "tecnica": {
            "nome": "Lâmina na Penumbra", "mult": 2.1, "cd": 4, "cura": 0.0,
            "texto": "Das sombras surge {tecnica}: o aço encontra {inimigo} onde a guarda é mais fraca ({dano}).",
        },
        "arma": ("Adaga Serrilhada Gasta", "f"),
    },
    "sacerdote": {
        "nome": "Sacerdote das Cinzas",
        "desc": "Clérigo de um culto extinto, que ainda reza pelos mortos sem nome.",
        "principal": "intelecto",
        "pesos": {"intelecto": 4, "vontade": 3, "vitalidade": 2, "destreza": 1, "forca": 0.5},
        "tecnica": {
            "nome": "Chama Sepulcral", "mult": 2.5, "cd": 6, "cura": 0.0,
            "texto": "Você murmura a litania e {tecnica} consome {inimigo} ({dano}).",
        },
        "arma": ("Cajado de Freixo Chamuscado", "m"),
    },
    "guardiao": {
        "nome": "Guardião do Juramento",
        "desc": "Sentinela atada a um voto que sobreviveu ao reino que o fez.",
        "principal": "vontade",
        "pesos": {"vontade": 3.5, "vitalidade": 3.5, "forca": 2, "destreza": 1, "intelecto": 1},
        "tecnica": {
            "nome": "Juramento Inquebrável", "mult": 1.9, "cd": 5, "cura": 0.06,
            "texto": "Você ergue a voz em {tecnica}; o golpe abate {inimigo} ({dano}) e o voto restaura seu fôlego.",
        },
        "arma": ("Maça de Guarnição", "f"),
    },
}

NOMES_SUGERIDOS = [
    "Aldric", "Maren", "Sevrin", "Isolde", "Corvane", "Brenna", "Torvin", "Elysa",
    "Hadrian", "Nyra", "Osric", "Vesna", "Garrick", "Liora", "Dunmar", "Selene",
]

# ---------------------------------------------------------------- maestrias
# Evoluem sozinhas com o uso. 'por_nivel' é somado ao efeito a cada nível.
MAESTRIAS = {
    "armas": {"nome": "Maestria de Armas", "efeito": "dano_pct", "por_nivel": 0.012,
              "desc": "Cada golpe desferido aprimora o dano causado."},
    "precisao": {"nome": "Olhar Treinado", "efeito": "crit", "por_nivel": 0.004,
                 "desc": "Ler o inimigo aumenta a chance de golpe crítico."},
    "guarda": {"nome": "Postura de Guarda", "efeito": "defesa_pct", "por_nivel": 0.012,
               "desc": "Suportar golpes ensina a recebê-los melhor."},
    "resistencia": {"nome": "Fortitude", "efeito": "fadiga_red", "por_nivel": 0.015,
                    "desc": "A longa marcha torna o corpo menos suscetível à fadiga."},
    "sobrevivencia": {"nome": "Instinto de Sobrevivência", "efeito": "regen_pct", "por_nivel": 0.02,
                      "desc": "Descansar com sabedoria acelera a recuperação."},
    "forja": {"nome": "Ofício da Forja", "efeito": "forja", "por_nivel": 0.01,
              "desc": "Aumenta a chance de êxito ao refinar equipamentos."},
    "tecnica": {"nome": "Domínio da Técnica", "efeito": "tecnica_pct", "por_nivel": 0.03,
                "desc": "Fortalece a técnica característica da vocação."},
}
NIVEL_MAX_MAESTRIA = 60

# ---------------------------------------------------------------- equipamentos
SLOTS = ["arma", "armadura", "reliquia"]
NOMES_SLOTS = {"arma": "Arma", "armadura": "Armadura", "reliquia": "Relíquia"}
RARIDADES = ["Comum", "Incomum", "Raro", "Épico", "Lendário"]
REFINO_MAX = 12

BASES_ITEM = {
    "arma": [("Espada Larga", "f"), ("Machado de Guerra", "m"), ("Maça Cravejada", "f"),
             ("Lança de Caça", "f"), ("Adaga Serrilhada", "f"), ("Cajado de Ébano", "m"),
             ("Arco Longo", "m"), ("Foice de Ceifa", "f")],
    "armadura": [("Cota de Malha", "f"), ("Couraça de Ferro", "f"), ("Gibão de Couro Curtido", "m"),
                 ("Manto Forrado", "m"), ("Brigantina", "f"), ("Armadura de Placas", "f")],
    "reliquia": [("Medalhão", "m"), ("Amuleto", "m"), ("Anel de Sinete", "m"),
                 ("Talismã", "m"), ("Relicário", "m"), ("Pingente de Osso", "m")],
}
ADJETIVOS = [
    [("Gasto", "Gasta"), ("Rústico", "Rústica"), ("Desgastado", "Desgastada")],
    [("Temperado", "Temperada"), ("Enegrecido", "Enegrecida"), ("Bem-forjado", "Bem-forjada")],
    [("Consagrado", "Consagrada"), ("Sombrio", "Sombria"), ("Vigilante", "Vigilante")],
    [("Sepulcral", "Sepulcral"), ("Ancestral", "Ancestral"), ("Votivo", "Votiva")],
    [("Imortal", "Imortal"), ("Derradeiro", "Derradeira"), ("Inextinguível", "Inextinguível")],
]
EPITETOS = [
    "da Vigília", "dos Esquecidos", "do Último Inverno", "das Cinzas", "do Juramento Quebrado",
    "dos Penitentes", "da Longa Noite", "do Reino Caído", "das Marés de Breu", "do Silêncio",
]

# ------------------------------------------------------------------ regiões
NIVEIS_POR_CICLO = 65  # aumento de nível dos inimigos a cada volta completa da Roda

REGIOES = [
    {
        "nome": "Charnecas do Luto", "nivel_base": 1, "nivel_chefe": 6, "extensao": 60,
        "desc": "Planícies varridas por um vento sem origem, onde os campos de uma guerra esquecida ainda guardam seus mortos.",
        "ambiente": [
            "O vento carrega cinza dos fogos de uma guerra que ninguém mais nomeia.",
            "Estandartes rasgados pendem de lanças fincadas na lama, curvados como lápides.",
            "Corvos acompanham a marcha em silêncio, pousando e voltando a levantar voo.",
            "A névoa baixa engole o horizonte e devolve apenas o eco distante de sinos.",
        ],
        "inimigos": [("Saqueador Faminto", 1.0, 1.0), ("Cão de Carniça", 0.8, 1.2),
                     ("Soldado Esquecido", 1.1, 0.9), ("Corvo-Ceifeiro", 0.7, 1.3),
                     ("Desertor Enlouquecido", 1.0, 1.1)],
        "perigos": ["Uma geada súbita corta os ossos; o frio cobra seu tributo.",
                    "O solo cede sob os pés e revela uma vala comum meio aberta."],
        "guardiao": "Capitão Sem Nome",
        "marco": "Com a queda do Capitão Sem Nome, o caminho para o Bosque dos Corvos Silenciosos se abre.",
    },
    {
        "nome": "Bosque dos Corvos Silenciosos", "nivel_base": 6, "nivel_chefe": 12, "extensao": 70,
        "desc": "Floresta de troncos negros onde nenhuma ave canta e a luz chega pálida, filtrada por galhos como dedos.",
        "ambiente": [
            "Os galhos se entrelaçam acima, e a luz chega ao chão como cinza peneirada.",
            "Há marcas de garras nos troncos, a uma altura que você prefere não medir.",
            "Em algum ponto da mata, algo imita o som dos seus próprios passos.",
        ],
        "inimigos": [("Lobo Escalvado", 1.0, 1.1), ("Caçador Apodrecido", 1.1, 1.0),
                     ("Eremita Possuído", 0.9, 1.3), ("Aranha do Musgo", 0.8, 1.2),
                     ("Espectro da Clareira", 0.9, 1.2)],
        "perigos": ["Esporos de uma flor pálida turvam a visão e pesam nos pulmões.",
                    "Raízes traiçoeiras prendem seu tornozelo antes de soltá-lo, a custo."],
        "guardiao": "Anciã das Raízes",
        "marco": "A Anciã das Raízes se desfaz em folhas secas. Além da mata, erguem-se muralhas partidas.",
    },
    {
        "nome": "Ruínas da Cidade Sepulta", "nivel_base": 12, "nivel_chefe": 19, "extensao": 80,
        "desc": "Uma metrópole soterrada por seu próprio orgulho, cujas torres ainda apontam para um céu que a esqueceu.",
        "ambiente": [
            "Arcos quebrados emolduram praças onde ninguém celebra há séculos.",
            "Nas paredes, afrescos desbotados mostram uma corte que sorria demais.",
            "O vento assobia pelos sinos mudos, compondo uma litania sem fim.",
        ],
        "inimigos": [("Guarda Sepulto", 1.2, 1.0), ("Sacerdote Murmurante", 0.9, 1.3),
                     ("Gárgula Rachada", 1.3, 0.9), ("Pilhador de Tumbas", 0.9, 1.1),
                     ("Sombra do Cortejo", 0.8, 1.3)],
        "perigos": ["Uma laje cede e você cai entre ossos antes de reencontrar o caminho.",
                    "Um sussurro coletivo ecoa nas ruínas e quase lhe rouba o juízo."],
        "guardiao": "Magistrado Sepulto",
        "marco": "O Magistrado Sepulto cumpre enfim sua última sentença. A estrada desce rumo ao pântano.",
    },
    {
        "nome": "Pântano de Breu", "nivel_base": 19, "nivel_chefe": 27, "extensao": 90,
        "desc": "Lodo escuro e viscoso, em que bolhas de gás sobem como suspiros e nada que afunda retorna inteiro.",
        "ambiente": [
            "A cada passo, o breu estala e relutante devolve a bota.",
            "Luzes pálidas dançam ao longe, convidando a uma morte sem testemunhas.",
            "O ar cheira a ferrugem e a coisas que já foram vivas.",
        ],
        "inimigos": [("Afogado Errante", 1.1, 1.1), ("Sanguessuga Colossal", 1.3, 0.9),
                     ("Bruxa do Lodo", 0.9, 1.3), ("Fogo-Fátuo Voraz", 0.7, 1.4),
                     ("Cavaleiro Naufragado", 1.2, 1.1)],
        "perigos": ["Gases tóxicos sobem do lodo e queimam a garganta.",
                    "Você afunda até a cintura e luta longamente para se libertar."],
        "guardiao": "Leviatã de Breu",
        "marco": "O Leviatã de Breu submerge para sempre. A terra firme, enfim, volta a existir sob os seus pés.",
    },
    {
        "nome": "Planalto dos Ossos Gélidos", "nivel_base": 27, "nivel_chefe": 36, "extensao": 100,
        "desc": "Altiplano varrido por nevascas, onde ossadas de gigantes emergem do gelo como costelas de um mundo morto.",
        "ambiente": [
            "A neve range sob as botas, e o próprio ar parece ferir ao ser respirado.",
            "Ossadas enormes despontam do gelo, polidas pelo vento de eras.",
            "A nevasca engole o som; sua respiração é a única voz que resta.",
        ],
        "inimigos": [("Lobo Espectral das Geleiras", 1.0, 1.2), ("Nômade Congelado", 1.1, 1.0),
                     ("Colosso de Gelo Rachado", 1.5, 0.9), ("Harpia Cinzenta", 0.8, 1.3),
                     ("Vigia da Nevasca", 1.0, 1.2)],
        "perigos": ["Uma rajada glacial arranca-lhe o calor do corpo de uma só vez.",
                    "O gelo se parte sob o peso e a queda deixa feridas profundas."],
        "guardiao": "Jarl Congelado",
        "marco": "O Jarl Congelado se estilhaça em mil fragmentos. Ao sul, a terra se abre em galerias antigas.",
    },
    {
        "nome": "Catacumbas do Reino Caído", "nivel_base": 36, "nivel_chefe": 46, "extensao": 110,
        "desc": "Galerias intermináveis onde uma dinastia inteira foi emparedada com seus segredos e remorsos.",
        "ambiente": [
            "Nichos se alinham nas paredes, cada qual com um nome que o tempo já apagou.",
            "A umidade escorre pelas pedras como lágrimas que não têm quem as chore.",
            "Uma coroa rolou até seus pés, vazia, e ficou ali a lhe encarar.",
        ],
        "inimigos": [("Guarda Real Insepulto", 1.2, 1.1), ("Necrólogo Sem Voz", 0.9, 1.4),
                     ("Quimera de Ossos", 1.4, 1.1), ("Herdeiro Corrompido", 1.0, 1.3),
                     ("Carrasco Eterno", 1.3, 1.3)],
        "perigos": ["Um mecanismo antigo dispara lâminas das paredes sem aviso.",
                    "O ar viciado das galerias aperta o peito e turva os pensamentos."],
        "guardiao": "Rainha Sem Coroa",
        "marco": "A Rainha Sem Coroa deixa cair o cetro. Das profundezas, vem um calor que não é de fogo comum.",
    },
    {
        "nome": "Abismo das Brasas", "nivel_base": 46, "nivel_chefe": 57, "extensao": 120,
        "desc": "Fenda incandescente onde a própria rocha sangra luz, e cada respiração tem gosto de metal fundido.",
        "ambiente": [
            "Rios de brasa riscam a escuridão, iluminando paredes que parecem respirar.",
            "O calor distorce o ar, e sombras longas dançam sem donos.",
            "Cinzas caem como neve rubra, pousando em seus ombros sem peso algum.",
        ],
        "inimigos": [("Cultista Calcinado", 1.0, 1.3), ("Servo das Brasas", 1.2, 1.2),
                     ("Verme de Magma", 1.5, 1.1), ("Anjo Queimado", 1.1, 1.5),
                     ("Arauto Incandescente", 1.3, 1.4)],
        "perigos": ["Uma rajada de brasa lambe suas costas e chamusca o couro.",
                    "O solo racha e vapores ardentes irrompem ao seu redor."],
        "guardiao": "Fornalheiro Primordial",
        "marco": "O Fornalheiro Primordial se apaga. No fim da fenda, um salão imenso aguarda, silencioso.",
    },
    {
        "nome": "O Trono Vazio", "nivel_base": 57, "nivel_chefe": 70, "extensao": 130,
        "desc": "Salão sem teto nem paredes, onde um trono de pedra negra espera por alguém que talvez nunca tenha existido.",
        "ambiente": [
            "O chão reflete um céu que não está acima de você.",
            "Cada passo ecoa um instante depois, como se outro caminhasse ao seu lado.",
            "O trono permanece ao longe, sempre à mesma distância, sempre vazio.",
        ],
        "inimigos": [("Sentinela do Vazio", 1.2, 1.3), ("Eco de um Rei", 1.0, 1.5),
                     ("Cavaleiro Sem Reino", 1.4, 1.2), ("Devoto da Ausência", 1.0, 1.4),
                     ("Lembrança Hostil", 0.9, 1.6)],
        "perigos": ["A ausência pesa sobre seus ombros, e por um instante você esquece quem é.",
                    "Uma voz sem boca recita seus fracassos, um a um."],
        "guardiao": "O Rei que Jamais Foi",
        "marco": "O Rei que Jamais Foi se desfaz sem ruído. O trono continua vazio; a Roda, porém, volta a girar.",
    },
]

# -------------------------------------------------------------------- textos
TEXTOS = {
    "inicio": "Nas cinzas de um mundo que já foi outro, {nome}, {origem} e {classe}, ergue-se e começa a caminhar.",
    "ciclo": "A Roda das Cinzas completa mais uma volta. As terras renascem, mais cruéis do que antes (Ciclo {n}).",
    "chegada": "Você adentra {regiao}. {desc}",
    "encontro": [
        "{inimigo} (nível {n}) emerge diante de você.",
        "Passos pesados anunciam {inimigo} (nível {n}).",
        "Entre as sombras, {inimigo} (nível {n}) bloqueia o caminho.",
        "Algo se move à frente: é {inimigo} (nível {n}).",
    ],
    "chefe": [
        "O ar se torna denso. {inimigo} (nível {n}) guarda a passagem e o encara.",
        "Você alcança o limiar da região. {inimigo} (nível {n}) ergue-se para o último combate.",
    ],
    "gate": "As portas do guardião {inimigo} parecem grandes demais para suas forças atuais (nível recomendado {n}). Você refaz veredas conhecidas para ganhar vigor.",
    "ataque": [
        "Você atinge {inimigo} e lhe tira {dano} de vitalidade.",
        "O golpe encontra carne e osso: {dano} de dano em {inimigo}.",
        "{inimigo} cede terreno sob o golpe ({dano}).",
    ],
    "critico": [
        "Um golpe certeiro abre uma brecha na defesa de {inimigo}: {dano} de dano crítico!",
        "Você encontra o ponto fraco de {inimigo} e causa {dano} de dano crítico!",
    ],
    "erro": [
        "O golpe passa a um palmo de {inimigo}.",
        "{inimigo} se esquiva por entre a névoa.",
    ],
    "dano_recebido": [
        "{inimigo} o fere: {dano} de vitalidade perdida.",
        "Um golpe de {inimigo} atravessa sua guarda ({dano}).",
    ],
    "desvio": [
        "Você desvia do ataque de {inimigo}.",
        "O golpe de {inimigo} resvala em seu equipamento sem causar dano.",
    ],
    "devastador": "O ataque de {inimigo} é devastador: {dano} de vitalidade perdida de uma só vez.",
    "vitoria": [
        "{inimigo} tomba. A marcha prossegue. (+{xp} XP)",
        "{inimigo} cai e não se levanta. (+{xp} XP)",
        "O silêncio retorna depois da queda de {inimigo}. (+{xp} XP)",
    ],
    "recuo": [
        "Ferido além do prudente, você recua de {inimigo} e se retira para recompor as forças.",
        "O perigo supera suas forças atuais. Você abandona o combate com {inimigo} e foge para a sombra.",
    ],
    "descida": "Os sucessivos recuos mostram que a ameaça supera suas forças. Você retorna pelos caminhos da região anterior, em busca de vigor.",
    "descanso": [
        "Você se detém para estancar as feridas e recuperar o fôlego.",
        "Acampa junto a um abrigo precário e deixa a exaustão escorrer do corpo.",
        "O corpo cobra seu preço; você descansa até o tremor das mãos cessar.",
    ],
    "forja_inicio": [
        "Junto a uma fogueira improvisada, você começa a refinar {item}.",
        "Você bate o metal de {item} com paciência, ouvindo o que ele pede.",
    ],
    "forja_ok": "O refino é bem-sucedido: {item} agora é +{n}.",
    "forja_falha": "O metal rejeita o trabalho. O refino de {item} falha e os fragmentos se perdem.",
    "nivel": "Você alcança o nível {n}. Algo se assenta em seu íntimo, como metal que esfria.",
    "maestria": "A maestria \"{nome}\" alcança o nível {n}.",
    "equipou": "Você equipa {item} ({raridade}).",
    "achado": "Entre os despojos você encontra {item} ({raridade}), mas já possui algo melhor. O resto é desmontado em fragmentos.",
    "perigo": "{texto} (-{dano} de vitalidade)",
    "descanso_fim": "As forças retornam. Você retoma a marcha.",
}

MARCOS_NIVEL = {
    5: "Marco: nível 5. Você já não é um forasteiro nestas terras.",
    10: "Marco: nível 10. Seu nome começa a ser sussurrado em acampamentos distantes.",
    20: "Marco: nível 20. A dor deixou de ser surpresa; tornou-se companheira.",
    30: "Marco: nível 30. Poucos chegaram tão longe e voltaram inteiros.",
    40: "Marco: nível 40. As cicatrizes contam uma história mais longa que a sua memória.",
    50: "Marco: nível 50. Você caminha onde até os mortos hesitam.",
    75: "Marco: nível 75. Lendas antigas parecem escritas sobre alguém como você.",
    100: "Marco: nível 100. O mundo inteiro conhece o peso dos seus passos.",
}
