# Crônicas de Cinzas

RPG **100% idle** em português do Brasil, de tom sombrio e épico. O personagem marcha, luta, recua, descansa, forja e evolui sozinho; você acompanha a crônica. Existe em duas versões que compartilham o mesmo núcleo:

- **Terminal (`CronicasDeCinzas-CMD.exe`)**: roda no `cmd.exe` / Windows Terminal.
- **Janela (`CronicasDeCinzas.exe`)**: interface desktop (tkinter), com instalador.

## Stack e por quê

**Python 3.10+ (somente biblioteca padrão) + PyInstaller + Inno Setup.**

- Zero dependências de runtime: o jogo usa `json`, `random`, `tkinter`, `msvcrt` etc. Nada para instalar além de Python e PyInstaller para compilar.
- Iteração rápida: a simulação roda e é testada em qualquer sistema; só o empacotamento exige Windows.
- O núcleo (`core/`) não importa nenhuma interface, então trocar ou acrescentar camadas (web, Qt, etc.) não exige mexer nas regras.
- Dois `.exe` (um com janela, outro com console) em vez de um só: um executável "windowed" não tem console, e um "console" abre uma janela preta ao clicar duas vezes. Dois pontos de entrada pequenos resolvem isso sem truques.

## Arquitetura

```
cronicas_de_cinzas/
├── core/                    # engine: sem I/O de tela, sem dependência de UI
│   ├── dados.py             # atributos, origens, classes, maestrias, regiões e TODOS os textos (PT-BR)
│   ├── itens.py             # geração, raridade, afixos, refinamento
│   ├── criacao.py           # rolagem 4d6, distribuição de pontos, criação rápida
│   ├── motor.py             # simulação por tempo, fases, combate, progressão, offline
│   ├── persistencia.py      # save JSON atômico, backup, exportar/importar, reset
│   └── util.py              # formatação (tempo, números, romanos)
├── ui/
│   ├── cmd_ui.py            # terminal: ANSI, redesenho único por quadro, teclas sem bloquear
│   └── gui_ui.py            # janela tkinter
├── tests/test_core.py       # 20 testes (simulação, save, offline, criação)
├── main.py                  # entrada única: --cmd / --gui / --ascii / --dir / --versao
├── main_gui.py              # entrada do .exe com janela
├── main_cmd.py              # entrada do .exe de terminal
├── build.bat                # testes + PyInstaller + instalador
├── installer.iss            # script do Inno Setup
├── jogar_cmd.bat            # roda do código-fonte, em modo terminal
└── requirements-build.txt
```

### Como a simulação funciona

- Todo o estado é um `dict` serializável (`Motor.s`). `Motor.avancar(dt)` consome o tempo em passos fixos de 0,25 s (1 s no offline), então o resultado **não depende da taxa de quadros nem da velocidade da máquina**.
- Fases: *Marchando pela Região*, *Em Combate*, *Recuperando Forças*, *Forjando e Aprimorando*, *Consolidando Patamar*. Após cada etapa, `_decidir()` escolhe a próxima (descansar se vida < 40 % ou fadiga ≥ 88; forjar se houver fragmentos; senão marchar).
- **Atributos** (Força, Destreza, Vitalidade, Intelecto, Vontade) geram: vida máxima, dano, defesa, precisão, crítico, intervalo de ciclo, recuperação e resistência à fadiga. Cada vocação usa um atributo principal para o dano.
- **Equipamentos**: arma, armadura e relíquia com 5 raridades (Comum a Lendário), afixos de atributo e **refino até +12** (custo crescente em fragmentos, chance decrescente, falha perde os fragmentos). Itens melhores são equipados sozinhos; o excedente é desmontado em fragmentos.
- **Maestrias** (7) evoluem com o uso: armas, precisão, guarda, fortitude, sobrevivência, forja e técnica da vocação.
- **Regiões**: 8 zonas de dificuldade progressiva, cada uma com inimigos, perigos ambientais e um guardião. Se o nível está abaixo do recomendado, o herói não enfrenta o guardião: percorre a região de novo para ganhar força. Com vida abaixo de 20 % ele **recua**; três recuos seguidos o fazem voltar à região anterior. Concluída a última região, a **Roda das Cinzas** gira: as terras recomeçam mais cruéis (Ciclo II, III...).
- **Marcos**: primeiro sangue, níveis-chave, guardiões, refinos +5/+10, primeiro item lendário, primeiro recuo, ciclos.
- **Crônica**: log em prosa, com categorias (combate, perigo, alerta, marco, item, forja...). Os golpes comuns ficam como "detalhe" e só aparecem se você ligar a opção.
- **Ritmo de referência**: ~1 h para o nível ~9; ~12 h para o nível ~36; uma volta completa da Roda em ~36–48 h.

### Persistência e progresso offline

- Save em `%APPDATA%\CronicasDeCinzas\save.json` (fora da pasta de instalação, então atualizar ou desinstalar **preserva o progresso**). Gravação atômica (`.tmp` + `os.replace`) com cópia `save.bak`; se o save principal estiver corrompido, o backup é usado.
- Autosave a cada 30 s e ao sair.
- Ao abrir, o tempo decorrido desde o último save é simulado (até 24 h) e mostrado em um **relatório** (níveis, abates, léguas, recuos, itens, refinos, marcos). Durante a ausência a crônica só registra marcos e alertas, para não ser inundada.
- Exportação: `%APPDATA%\CronicasDeCinzas\exportacoes\cronicas_AAAAMMDD_HHMMSS.json` (também importável). **Reiniciar** pede confirmação e guarda uma cópia `save_anterior_*.json`.

## Controles

**Terminal** (tecla única, sem Enter): `P` pausa/retoma · `V` velocidade (x1 a x100) · `1` painel · `2` atributos · `3` equipamentos · `4` maestrias · `5` jornada · `6` crônica · `D` detalhes de combate · `X` exportar save · `Z` reiniciar (confirmação) · `Q` salvar e sair.
Opções: `--ascii` (molduras sem Unicode), `--dir PASTA` (outra pasta de saves).

**Janela**: botões Pausar, Velocidade, Exportar, Importar, Reiniciar e Sair; barra de espaço também pausa.

## Rodar do código-fonte

```bat
python main.py --cmd        :: terminal
python main.py --gui        :: janela
python -m unittest discover -s tests -v
```

## Gerar os `.exe` e o instalador (Windows)

Pré-requisitos: **Python 3.10+** (instalação padrão do python.org, com tcl/tk) e, para o instalador, **Inno Setup 6.3+** (`winget install JRSoftware.InnoSetup`).

Tudo de uma vez:

```bat
build.bat
```

Passo a passo manual (equivalente):

```bat
python -m venv .venv
.venv\Scripts\activate
pip install pyinstaller

python -m unittest discover -s tests

pyinstaller --noconfirm --clean --onefile --windowed --name CronicasDeCinzas ^
  --paths . --distpath dist --workpath build\gui --specpath build main_gui.py

pyinstaller --noconfirm --clean --onefile --console --name CronicasDeCinzas-CMD ^
  --paths . --distpath dist --workpath build\cmd --specpath build main_cmd.py

"%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" installer.iss
```

Saídas: `dist\CronicasDeCinzas.exe`, `dist\CronicasDeCinzas-CMD.exe` e `instalador\CronicasDeCinzas-Instalador-1.0.0.exe`.

O instalador:
- instala em `%LocalAppData%\Programs\CronicasDeCinzas` (ou em *Arquivos de Programas*, se o usuário escolher instalar para todos);
- cria atalhos no Menu Iniciar (janela e terminal) e, opcionalmente, na Área de Trabalho;
- não toca nos saves ao atualizar ou desinstalar.

Para usar um ícone, coloque `assets\icone.ico` e o `build.bat` o aplica automaticamente.

### Observações

- Executáveis `--onefile` do PyInstaller às vezes disparam falsos positivos de antivírus. Se acontecer, troque `--onefile` por `--onedir` e ajuste a seção `[Files]` do `.iss` para copiar a pasta inteira.
- No `cmd.exe` clássico, use uma fonte com suporte a caracteres de moldura (Consolas/Cascadia). Se a moldura ficar quebrada, abra com `--ascii`.

## Onde ajustar o jogo

- Equilíbrio: fórmulas em `core/motor.py` (`xp_proximo_nivel`, `stats_inimigo`, `derivados`).
- Conteúdo e textos: tudo em `core/dados.py` (regiões, inimigos, perigos, frases, marcos).
- Novas classes ou origens: acrescente uma entrada em `CLASSES` / `ORIGENS`; nenhuma outra mudança é necessária.
