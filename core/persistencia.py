# -*- coding: utf-8 -*-
"""Persistência em JSON local: save atômico, backup, exportação, importação e reset."""
import json
import os
import shutil
import sys
import time

VERSAO_SAVE = 1
NOME_PASTA = "UltimaVigilia"


class ErroSave(Exception):
    pass


def diretorio_dados():
    """Pasta de dados do jogador. Fica fora da pasta de instalação para sobreviver a atualizações."""
    forcado = os.environ.get("VIGILIA_DIR")
    if forcado:
        base = forcado
    elif sys.platform.startswith("win"):
        base = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), NOME_PASTA)
    else:
        base = os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"),
                            "ultima-vigilia")
    os.makedirs(base, exist_ok=True)
    return base


def caminho_save():
    return os.path.join(diretorio_dados(), "save.json")


def caminho_backup():
    return os.path.join(diretorio_dados(), "save.bak")


def existe_save():
    return os.path.exists(caminho_save()) or os.path.exists(caminho_backup())


def _validar(dados):
    if not isinstance(dados, dict):
        raise ErroSave("Formato de save inválido.")
    if dados.get("versao") != VERSAO_SAVE:
        raise ErroSave("Versão de save não suportada: %r." % dados.get("versao"))
    for chave in ("personagem", "regiao", "fase", "tempo_jogado"):
        if chave not in dados:
            raise ErroSave("Save incompleto: falta '%s'." % chave)
    return dados


def salvar(estado):
    """Grava o save de forma atômica e mantém uma cópia de segurança do anterior."""
    estado["versao"] = VERSAO_SAVE
    estado["salvo_em"] = time.time()
    destino = caminho_save()
    tmp = destino + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    if os.path.exists(destino):
        try:
            shutil.copy2(destino, caminho_backup())
        except OSError:
            pass
    os.replace(tmp, destino)


def _ler(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return _validar(json.load(f))


def carregar():
    """Lê o save; se estiver corrompido, tenta o backup. Retorna None se não houver nada."""
    erros = []
    for caminho in (caminho_save(), caminho_backup()):
        if os.path.exists(caminho):
            try:
                return _ler(caminho)
            except (OSError, ValueError, ErroSave) as e:
                erros.append("%s: %s" % (os.path.basename(caminho), e))
    if erros:
        raise ErroSave("Não foi possível ler o save (%s)." % "; ".join(erros))
    return None


def exportar(estado):
    """Cria uma cópia datada em <dados>/exportacoes e retorna o caminho."""
    pasta = os.path.join(diretorio_dados(), "exportacoes")
    os.makedirs(pasta, exist_ok=True)
    nome = "vigilia_%s.json" % time.strftime("%Y%m%d_%H%M%S")
    caminho = os.path.join(pasta, nome)
    copia = dict(estado)
    copia["versao"] = VERSAO_SAVE
    copia["salvo_em"] = time.time()
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(copia, f, ensure_ascii=False, indent=1)
    return caminho


def importar(caminho):
    """Valida e devolve o estado de um arquivo exportado (não grava nada)."""
    try:
        return _ler(caminho)
    except (OSError, ValueError) as e:
        raise ErroSave("Não foi possível importar: %s" % e)


def apagar():
    """Reset: guarda uma cópia 'save_anterior_*.json' antes de remover o save atual."""
    atual = caminho_save()
    if os.path.exists(atual):
        pasta = os.path.join(diretorio_dados(), "exportacoes")
        os.makedirs(pasta, exist_ok=True)
        shutil.copy2(atual, os.path.join(pasta, "save_anterior_%s.json" % time.strftime("%Y%m%d_%H%M%S")))
    for caminho in (atual, caminho_backup()):
        if os.path.exists(caminho):
            os.remove(caminho)
