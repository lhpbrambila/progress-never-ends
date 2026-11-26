# -*- coding: utf-8 -*-
"""Talentos por vocação.

O herói ganha um talento a cada 5 níveis e outro ao derrotar um guardião pela primeira vez em
cada volta da Roda. A escolha é automática, seguindo o 'caminho' definido na criação (por
padrão, o primeiro caminho da vocação). Cada talento pode ser aprimorado até RANK_MAX vezes;
'efeito' é o bônus por grau (frações: 0.01 = +1% por grau).
"""

RANK_MAX = 30


def _t(nome, desc, **efeito):
    return {"nome": nome, "desc": desc, "efeito": efeito}


def _c(nome, desc, prioridade):
    return {"nome": nome, "desc": desc, "prioridade": prioridade}


TALENTOS = {
    "penitente": {
        "caminhos": {
            "expiacao": _c("Via da Expiação", "Cada golpe é uma sentença. Foco em dano e na técnica.",
                           {"sentenca": 3, "contricao": 3, "carrasco": 2, "cicatriz": 1}),
            "martirio": _c("Via do Martírio", "A dor é o preço e a armadura. Foco em resistir.",
                           {"carne": 3, "cicatriz": 3, "prece": 2, "sentenca": 1}),
        },
        "talentos": {
            "sentenca": _t("Sentença Implacável", "O aço cai sem hesitar.", dano_pct=0.008, crit_dano=0.004),
            "contricao": _t("Peso da Contrição", "A culpa dá força ao braço.", tecnica_pct=0.015),
            "carrasco": _t("Carrasco dos Reis", "Os guardiões também prestam contas.", dano_chefe_pct=0.010),
            "carne": _t("Carne Mortificada", "O corpo aprende a aceitar a dor.", pv_pct=0.007, reducao_dano=0.001),
            "prece": _t("Prece Sussurrada", "Entre um golpe e outro, uma oração.", regen_pct=0.010, fadiga_red=0.008),
            "cicatriz": _t("Cicatrizes Votivas", "Cada marca é uma promessa.", defesa_pct=0.008),
        },
    },
    "cacador": {
        "caminhos": {
            "espreita": _c("Via da Espreita", "Esperar, escolher o ponto fraco e não errar.",
                           {"sombra": 3, "emboscada": 3, "presa": 2, "rastro": 1}),
            "andarilho": _c("Via do Andarilho", "Quem anda leve vive mais. Foco em agilidade e sobrevivência.",
                            {"rastro": 3, "pele": 3, "trofeu": 2, "presa": 1}),
        },
        "talentos": {
            "sombra": _t("Lâmina na Sombra", "O golpe vem de onde ninguém olha.", crit=0.002, crit_dano=0.006),
            "rastro": _t("Rastro Silencioso", "Passos que não deixam eco.", esquiva=0.002, vel_marcha_pct=0.004),
            "presa": _t("Olho da Presa", "Nenhum movimento passa despercebido.", precisao=0.002, dano_pct=0.004),
            "emboscada": _t("Emboscada Perfeita", "A técnica da vocação, afiada pela paciência.", tecnica_pct=0.015),
            "pele": _t("Pele Curtida", "Couro grosso contra veneno e vento.", defesa_pct=0.006, resist_veneno=0.008),
            "trofeu": _t("Troféus de Caça", "Cada presa deixa algo para trás.", xp_pct=0.004, fragmentos_pct=0.006),
        },
    },
    "sacerdote": {
        "caminhos": {
            "pira": _c("Via da Pira", "A chama sepulcral consome o que encontra.",
                       {"chama": 3, "revelacao": 2, "oferenda": 2, "litania": 1}),
            "vigilia": _c("Via da Vigília", "Rezar pelos mortos mantém o corpo de pé.",
                          {"fe": 3, "litania": 3, "cinzas": 2, "chama": 1}),
        },
        "talentos": {
            "chama": _t("Chama Votiva", "A litania arde mais forte.", tecnica_pct=0.015, dano_pct=0.004),
            "litania": _t("Litania dos Mortos", "Os mortos devolvem um pouco do que levaram.",
                          regen_pct=0.010, roubo_vida=0.0006),
            "fe": _t("Fé Cinzenta", "Uma fé sem deus, mas firme.", pv_pct=0.006, fadiga_red=0.008),
            "cinzas": _t("Cinzas Consagradas", "A cinza protege quem a carrega.",
                         resist_veneno=0.010, reducao_dano=0.001),
            "revelacao": _t("Revelação Sepulcral", "O que está oculto se mostra.", crit=0.0015, xp_pct=0.004),
            "oferenda": _t("Oferenda", "Pagar para ver o inimigo cair.", dano_chefe_pct=0.008, defesa_pct=0.004),
        },
    },
    "guardiao": {
        "caminhos": {
            "muralha": _c("Via da Muralha", "Nada passa. Foco em defesa e vitalidade.",
                          {"juramento": 3, "bastiao": 3, "serenidade": 2, "memoria": 1}),
            "vigia": _c("Via da Vigia", "Quem vigia, golpeia primeiro e melhor.",
                        {"voto": 3, "sentinela": 2, "memoria": 2, "juramento": 1}),
        },
        "talentos": {
            "juramento": _t("Juramento Inquebrável", "O voto resiste ao golpe.", defesa_pct=0.008, reducao_dano=0.0012),
            "bastiao": _t("Bastião Vivo", "O corpo como muralha.", pv_pct=0.008),
            "sentinela": _t("Olhar da Sentinela", "O perigo não chega de surpresa.", precisao=0.002, crit=0.0012),
            "voto": _t("Voto de Ferro", "Cumprir o dever custa caro ao inimigo.", dano_pct=0.006, tecnica_pct=0.010),
            "serenidade": _t("Serenidade do Dever", "Dever também é descanso.", regen_pct=0.010, fadiga_red=0.010),
            "memoria": _t("Memória do Reino", "O que se lembra dá força.", xp_pct=0.004, dano_chefe_pct=0.006),
        },
    },
    "lanceiro": {
        "caminhos": {
            "vanguarda": _c("Via da Vanguarda", "Quem avança primeiro rompe a linha inimiga.",
                            {"investida": 3, "quebra": 2, "alcance": 2, "formacao": 1}),
            "reduto": _c("Via do Reduto", "Segurar a posição custe o que custar.",
                         {"formacao": 3, "veterano": 3, "folego": 2, "investida": 1}),
        },
        "talentos": {
            "investida": _t("Investida Cerrada", "A lança não pede licença.", tecnica_pct=0.015, dano_pct=0.003),
            "alcance": _t("Domínio do Alcance", "A distância certa decide tudo.", precisao=0.002, crit=0.0015),
            "formacao": _t("Postura de Formação", "O corpo lembra a linha de escudos.", defesa_pct=0.008),
            "folego": _t("Fôlego de Marcha", "Léguas e léguas sob o peso da armadura.",
                         fadiga_red=0.010, vel_marcha_pct=0.004),
            "quebra": _t("Quebra-Escudos", "Os guardiões também têm linha de defesa.", dano_chefe_pct=0.010),
            "veterano": _t("Veterano de Cercos", "Quem sobreviveu a muitos cercos, sobrevive a mais um.",
                           pv_pct=0.006, xp_pct=0.003),
        },
    },
    "alquimista": {
        "caminhos": {
            "corrosao": _c("Via da Corrosão", "Dano que se espalha, em golpes voláteis.",
                           {"vitriolo": 3, "volatil": 3, "reagente": 2, "destilacao": 1}),
            "transmutacao": _c("Via da Transmutação", "O que sobra vira recurso. Foco em fragmentos e sobrevivência.",
                               {"destilacao": 3, "antidoto": 3, "pele": 2, "reagente": 1}),
        },
        "talentos": {
            "vitriolo": _t("Vitríolo Concentrado", "O frasco queima mais fundo.", tecnica_pct=0.020),
            "destilacao": _t("Destilação Paciente", "Nada se perde, tudo se destila.",
                             fragmentos_pct=0.008, forja=0.003),
            "antidoto": _t("Antídotos de Campo", "Aprendeu a se curar do que prepara.",
                           resist_veneno=0.012, regen_pct=0.006),
            "volatil": _t("Mistura Volátil", "Quando explode, explode bem.", crit_dano=0.008, crit=0.0012),
            "reagente": _t("Reagentes Raros", "Cada inimigo é um ingrediente.", xp_pct=0.004, dano_pct=0.004),
            "pele": _t("Pele Tratada", "Untada com o que os outros evitam.", defesa_pct=0.006, reducao_dano=0.001),
        },
    },
    "ceifeiro": {
        "caminhos": {
            "ceifa": _c("Via da Ceifa", "A colheita é metódica e sem pressa.",
                        {"colheita": 3, "foice": 3, "pressagio": 2, "paz": 1}),
            "errancia": _c("Via da Errância", "Andar sem destino, sem fardos.",
                           {"errante": 3, "mortalha": 3, "paz": 2, "foice": 1}),
        },
        "talentos": {
            "colheita": _t("Colheita Silenciosa", "Cada vida colhida devolve um suspiro.",
                           tecnica_pct=0.012, roubo_vida=0.0006),
            "foice": _t("Arco da Foice", "O golpe descreve sempre o mesmo círculo.", dano_pct=0.006, crit=0.001),
            "pressagio": _t("Presságio da Morte", "Sabe quando o fim chega.", crit_dano=0.008, dano_chefe_pct=0.006),
            "errante": _t("Passo do Errante", "A estrada nunca o prende.", esquiva=0.002, vel_marcha_pct=0.004),
            "mortalha": _t("Mortalha Leve", "Veste-se de nada e quase nada o atinge.",
                           reducao_dano=0.0012, defesa_pct=0.004),
            "paz": _t("Paz dos Ceifados", "Os mortos agradecem em silêncio.", regen_pct=0.010, xp_pct=0.003),
        },
    },
    "monge": {
        "caminhos": {
            "punhos": _c("Via dos Punhos", "A disciplina se faz golpe.",
                         {"punho": 3, "palma": 3, "voto_silencio": 2, "equilibrio": 1}),
            "calma": _c("Via da Calma", "Nada abala quem sabe respirar.",
                        {"respiro": 3, "equilibrio": 3, "disciplina": 2, "palma": 1}),
        },
        "talentos": {
            "palma": _t("Palma do Silêncio", "A mão aberta é a mais letal.", tecnica_pct=0.015, crit=0.0012),
            "respiro": _t("Respiração Contada", "Cada inspiração, uma pequena cura.", regen_pct=0.010, fadiga_red=0.008),
            "punho": _t("Punho Enfaixado", "Ossos que aprenderam a quebrar pedra.", dano_pct=0.007),
            "equilibrio": _t("Equilíbrio Perfeito", "O corpo sabe onde está sem olhar.",
                             esquiva=0.0025, precisao=0.0015),
            "disciplina": _t("Disciplina do Claustro", "Anos de silêncio, anos de força.",
                             defesa_pct=0.006, pv_pct=0.005),
            "voto_silencio": _t("Voto de Silêncio", "O que não se diz também se aprende.",
                                xp_pct=0.004, dano_chefe_pct=0.006),
        },
    },
}
