import unittest
from pathlib import Path

import cv2

from config import (
    IMG_JOGAR,
    IMG_JOGAR_NOVAMENTE,
    IMG_SAIR,
    PASTA_REFERENCIAS,
    REGIAO_ACOES_ELIMINACAO,
    REGIAO_BOTAO_JOGAR
)
from vision import detectar_hud_partida, localizar, ultimas_precisoes


class VisionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.referencias = Path(PASTA_REFERENCIAS)

    def carregar_tela(self, nome):
        tela = cv2.imread(str(self.referencias / nome), cv2.IMREAD_GRAYSCALE)
        self.assertIsNotNone(tela, f"Não foi possível carregar {nome}")
        return tela

    def test_hud_distingue_partida_de_lobby_e_eliminacao(self):
        partida = self.carregar_tela("em_partida.png")
        lobby = self.carregar_tela("lobby.png")
        eliminado = self.carregar_tela("tela_eliminado.png")

        self.assertTrue(detectar_hud_partida(partida))
        self.assertFalse(detectar_hud_partida(lobby))
        self.assertFalse(detectar_hud_partida(eliminado))

    def test_botoes_da_eliminacao_sao_localizados_em_escala_diferente(self):
        eliminado = self.carregar_tela("tela_eliminado.png")
        partida = self.carregar_tela("em_partida.png")

        posicao_retorno = localizar(
            eliminado, IMG_SAIR, regiao=REGIAO_ACOES_ELIMINACAO
        )
        posicao_jogar_novamente = localizar(
            eliminado, IMG_JOGAR_NOVAMENTE, regiao=REGIAO_ACOES_ELIMINACAO
        )
        posicao_jogar = localizar(
            self.carregar_tela("lobby.png"),
            IMG_JOGAR,
            regiao=REGIAO_BOTAO_JOGAR
        )
        precisao_retorno = ultimas_precisoes[IMG_SAIR]
        precisao_jogar_novamente = ultimas_precisoes[IMG_JOGAR_NOVAMENTE]

        self.assertIsNotNone(posicao_retorno)
        self.assertIsNotNone(posicao_jogar_novamente)
        self.assertIsNotNone(posicao_jogar)
        self.assertIsNone(
            localizar(partida, IMG_SAIR, regiao=REGIAO_ACOES_ELIMINACAO)
        )
        self.assertIsNone(
            localizar(
                partida, IMG_JOGAR_NOVAMENTE,
                regiao=REGIAO_ACOES_ELIMINACAO
            )
        )
        self.assertGreaterEqual(precisao_retorno, 0.88)
        self.assertGreaterEqual(precisao_jogar_novamente, 0.88)


if __name__ == "__main__":
    unittest.main()
