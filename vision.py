from pathlib import Path

import cv2
import numpy as np
import pyautogui

from config import (
    PASTA_REFERENCIAS,
    PRECISAO_RECONHECIMENTO
)

EXTENSOES = (".png", ".jpg", ".jpeg", ".bmp")

_cache = {}

# Ultima precisao medida para cada imagem (usado no diagnostico)
ultimas_precisoes = {}


def capturar():
    """Captura a tela e retorna uma matriz cinza validada."""
    captura = np.asarray(pyautogui.screenshot())
    if captura.ndim != 3 or captura.shape[2] < 3:
        raise RuntimeError("A captura de tela retornou um formato inesperado.")
    return cv2.cvtColor(captura[:, :, :3], cv2.COLOR_RGB2GRAY)


def _carregar(nome):
    caminho = Path(PASTA_REFERENCIAS) / nome

    if not caminho.is_file():
        return None

    try:
        modificado = caminho.stat().st_mtime_ns
    except OSError:
        return None
    guardado = _cache.get(nome)

    if guardado and guardado[0] == modificado:
        return guardado[1]

    imagem = cv2.imread(str(caminho), cv2.IMREAD_GRAYSCALE)
    if imagem is None or imagem.size == 0:
        ultimas_precisoes.pop(nome, None)
        return None

    _cache[nome] = (modificado, imagem)
    return imagem


def localizar(tela, nome, precisao_minima=PRECISAO_RECONHECIMENTO):
    """Procura a imagem `nome` dentro de `tela`.

    Retorna o centro (x, y) se achar, ou None.
    """
    if tela is None or not isinstance(tela, np.ndarray) or tela.ndim != 2 or tela.size == 0:
        raise ValueError("A tela precisa ser uma matriz grayscale não vazia.")
    if not 0 <= precisao_minima <= 1:
        raise ValueError("A precisão mínima deve estar entre 0 e 1.")

    referencia = _carregar(nome)

    if referencia is None:
        return None

    altura, largura = referencia.shape

    if altura > tela.shape[0] or largura > tela.shape[1]:
        return None

    if float(referencia.std()) == 0.0:
        ultimas_precisoes[nome] = 0.0
        return None

    comparacao = cv2.matchTemplate(
        tela, referencia, cv2.TM_CCOEFF_NORMED
    )

    _, precisao, _, (x, y) = cv2.minMaxLoc(comparacao)

    ultimas_precisoes[nome] = float(precisao)

    if np.isfinite(precisao) and precisao >= precisao_minima:
        return (x + largura // 2, y + altura // 2)

    return None


def analisar_tela():
    """Modo de teste: lista tudo que foi reconhecido na pasta."""
    tela = capturar()
    resultados = []

    pasta = Path(PASTA_REFERENCIAS)
    if not pasta.is_dir():
        return resultados

    for caminho in sorted(pasta.iterdir()):

        if not caminho.is_file() or caminho.suffix.lower() not in EXTENSOES:
            continue

        arquivo = caminho.name

        referencia = _carregar(arquivo)

        if referencia is None:
            continue

        altura, largura = referencia.shape

        if altura > tela.shape[0] or largura > tela.shape[1]:
            continue

        if float(referencia.std()) == 0.0:
            ultimas_precisoes[arquivo] = 0.0
            continue

        comparacao = cv2.matchTemplate(
            tela, referencia, cv2.TM_CCOEFF_NORMED
        )

        _, precisao, _, posicao = cv2.minMaxLoc(comparacao)

        if (
            np.isfinite(precisao)
            and precisao >= PRECISAO_RECONHECIMENTO
        ):
            resultados.append({
                "nome": arquivo,
                "precisao": float(precisao),
                "posicao": posicao
            })

    return resultados
