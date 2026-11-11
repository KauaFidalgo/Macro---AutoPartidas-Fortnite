import ctypes
import os
import time

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

import cv2
import pyautogui

from config import PASTA_REFERENCIAS, PRECISAO_RECONHECIMENTO
from vision import capturar, localizar, ultimas_precisoes, EXTENSOES

print("Deixe o Fortnite visivel na tela (ex.: no Lobby).")

for i in range(5, 0, -1):
    print(f"Capturando em {i}...")
    time.sleep(1)

tela = capturar()
cv2.imwrite("debug_tela.png", tela)

print()
print(f"Tamanho da captura: {tela.shape[1]}x{tela.shape[0]}")
print(f"Tamanho da tela (pyautogui): {pyautogui.size()}")
print(f"Brilho medio da captura: {tela.mean():.1f}  (perto de 0 = tela preta)")
print("Captura salva em debug_tela.png")
print()

if not os.path.isdir(PASTA_REFERENCIAS):
    print(f"Pasta '{PASTA_REFERENCIAS}' nao encontrada em {os.getcwd()}")
    raise SystemExit

for arquivo in sorted(os.listdir(PASTA_REFERENCIAS)):

    if not arquivo.lower().endswith(EXTENSOES):
        continue

    imagem = cv2.imread(
        os.path.join(PASTA_REFERENCIAS, arquivo),
        cv2.IMREAD_GRAYSCALE
    )

    if imagem is None:
        print(f"{arquivo}: NAO FOI POSSIVEL LER A IMAGEM")
        continue

    achou = localizar(tela, arquivo, precisao_minima=0)
    precisao = ultimas_precisoes.get(arquivo)

    if precisao is None:
        print(
            f"{arquivo}: imagem {imagem.shape[1]}x{imagem.shape[0]} "
            f"e maior que a tela"
        )
        continue

    status = "RECONHECIDO" if precisao >= PRECISAO_RECONHECIMENTO else "nao"

    print(
        f"{arquivo}: {precisao:.1%} -> {status} "
        f"(imagem {imagem.shape[1]}x{imagem.shape[0]}, posicao {achou})"
    )