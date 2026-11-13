from pathlib import Path

import cv2
import numpy as np
import pyautogui

from config import (
    PASTA_REFERENCIAS,
    PRECISAO_RECONHECIMENTO,
    LIMIAR_BORDAS_MINIMAPA,
    LIMIAR_BORDAS_INVENTARIO
)

EXTENSOES = (".png", ".jpg", ".jpeg", ".bmp")
ESCALAS_RECONHECIMENTO = (
    1.0, 1.55, 1.5, 1.6, 0.95, 1.05, 0.9, 1.1, 1.2, 1.3, 1.4, 0.8
)

_cache = {}

# Ultima precisao medida para cada imagem (usado no diagnostico)
ultimas_precisoes = {}


def capturar(cores=False):
    """Captura a tela e retorna uma matriz RGB ou grayscale validada."""
    captura = np.asarray(pyautogui.screenshot())
    if captura.ndim != 3 or captura.shape[2] < 3:
        raise RuntimeError("A captura de tela retornou um formato inesperado.")
    if cores:
        return captura[:, :, :3].copy()
    return cv2.cvtColor(captura[:, :, :3], cv2.COLOR_RGB2GRAY)


def _carregar(nome):
    caminho = Path(PASTA_REFERENCIAS) / nome

    if not caminho.is_file():
        ultimas_precisoes.pop(nome, None)
        return None

    try:
        modificado = caminho.stat().st_mtime_ns
    except OSError:
        ultimas_precisoes.pop(nome, None)
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


def localizar(tela, nome, precisao_minima=PRECISAO_RECONHECIMENTO, regiao=None):
    """Procura a imagem `nome` dentro de `tela`.

    `regiao`, quando informada, usa limites normalizados (x1, y1, x2, y2).
    Retorna o centro (x, y) global se achar, ou None.
    """
    if tela is None or not isinstance(tela, np.ndarray) or tela.ndim != 2 or tela.size == 0:
        raise ValueError("A tela precisa ser uma matriz grayscale não vazia.")
    if not 0 <= precisao_minima <= 1:
        raise ValueError("A precisão mínima deve estar entre 0 e 1.")

    tela_completa = tela
    deslocamento = (0, 0)
    if regiao is not None:
        if (
            len(regiao) != 4
            or any(not 0 <= limite <= 1 for limite in regiao)
            or regiao[0] >= regiao[2]
            or regiao[1] >= regiao[3]
        ):
            raise ValueError("A região deve conter limites normalizados válidos.")

        altura_completa, largura_completa = tela.shape
        x1 = round(largura_completa * regiao[0])
        y1 = round(altura_completa * regiao[1])
        x2 = round(largura_completa * regiao[2])
        y2 = round(altura_completa * regiao[3])
        tela = tela[y1:y2, x1:x2]
        deslocamento = (x1, y1)

    referencia = _carregar(nome)

    if referencia is None:
        return None

    if float(referencia.std()) == 0.0:
        ultimas_precisoes[nome] = 0.0
        return None

    altura, largura = referencia.shape
    escalas = (
        ESCALAS_RECONHECIMENTO
        if altura <= tela_completa.shape[0] // 2
        and largura <= tela_completa.shape[1] // 2
        else (1.0,)
    )
    melhor_precisao = -1.0
    melhor_posicao = None
    melhor_tamanho = (largura, altura)

    for escala in escalas:
        nova_largura = max(1, round(largura * escala))
        nova_altura = max(1, round(altura * escala))

        if nova_altura > tela.shape[0] or nova_largura > tela.shape[1]:
            continue

        if nova_largura == largura and nova_altura == altura:
            imagem_referencia = referencia
        else:
            interpolacao = (
                cv2.INTER_AREA if escala < 1.0 else cv2.INTER_CUBIC
            )
            imagem_referencia = cv2.resize(
                referencia,
                (nova_largura, nova_altura),
                interpolation=interpolacao
            )

        comparacao = cv2.matchTemplate(
            tela, imagem_referencia, cv2.TM_CCOEFF_NORMED
        )
        _, precisao, _, posicao = cv2.minMaxLoc(comparacao)

        if np.isfinite(precisao) and precisao > melhor_precisao:
            melhor_precisao = float(precisao)
            melhor_posicao = posicao
            melhor_tamanho = (nova_largura, nova_altura)
            if precisao_minima > 0 and melhor_precisao >= precisao_minima:
                ultimas_precisoes[nome] = melhor_precisao
                x, y = melhor_posicao
                return (
                    x + deslocamento[0] + melhor_tamanho[0] // 2,
                    y + deslocamento[1] + melhor_tamanho[1] // 2
                )

    if melhor_posicao is None:
        ultimas_precisoes.pop(nome, None)
        return None

    ultimas_precisoes[nome] = melhor_precisao

    if melhor_precisao >= precisao_minima:
        x, y = melhor_posicao
        return (
            x + melhor_tamanho[0] // 2,
            y + melhor_tamanho[1] // 2
        )

    return None


def medir_hud_partida(tela):
    """Mede as bordas do minimapa e do inventário em regiões fixas do HUD."""
    if tela is None or not isinstance(tela, np.ndarray) or tela.ndim != 2 or tela.size == 0:
        raise ValueError("A tela precisa ser uma matriz grayscale não vazia.")

    altura, largura = tela.shape
    regioes = {
        "minimapa": (0.91, 0.025, 0.995, 0.15),
        "inventario": (0.78, 0.87, 0.998, 0.998)
    }
    medidas = {}

    for nome, (x1, y1, x2, y2) in regioes.items():
        regiao = tela[
            round(altura * y1):round(altura * y2),
            round(largura * x1):round(largura * x2)
        ]
        if regiao.size == 0:
            medidas[nome] = 0.0
            continue

        bordas = cv2.Canny(regiao, 40, 100)
        medidas[nome] = float(cv2.countNonZero(bordas) / bordas.size)

    return medidas


def detectar_hud_partida(tela):
    """Confirma o HUD pelo minimapa e pelos atalhos de inventário."""
    medidas = medir_hud_partida(tela)
    return (
        medidas["minimapa"] >= LIMIAR_BORDAS_MINIMAPA
        and medidas["inventario"] >= LIMIAR_BORDAS_INVENTARIO
    )


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
