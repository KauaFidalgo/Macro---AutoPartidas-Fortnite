import unittest
from pathlib import Path
from time import monotonic
from unittest.mock import Mock, patch

import cv2

from automation import (
    EM_PARTIDA,
    INICIANDO_PARTIDA,
    LOBBY,
    REINICIANDO,
    RETORNANDO_LOBBY,
    ELIMINADO,
    MacroController
)
from config import HUD_SUMIU_SEGUNDOS, PASTA_REFERENCIAS, TIMEOUT_FILA, TIMEOUT_PARTIDA


class AutomationCycleTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.referencias = Path(PASTA_REFERENCIAS)

    def setUp(self):
        self.eventos = []
        with patch("automation.keyboard", None):
            self.controller = MacroController(self.eventos.append)
        self.controller._clicar = Mock(return_value=True)
        self.controller._segurar_frente = Mock()

    def carregar_tela(self, nome):
        tela = cv2.imread(str(self.referencias / nome), cv2.IMREAD_GRAYSCALE)
        self.assertIsNotNone(tela, f"Não foi possível carregar {nome}")
        return tela

    def test_confirma_o_ciclo_visual_ate_nova_fila(self):
        lobby = self.carregar_tela("lobby.png")
        partida = self.carregar_tela("em_partida.png")
        eliminado = self.carregar_tela("tela_eliminado.png")

        self.controller._passo_lobby(lobby)
        self.assertEqual(self.controller.fase, LOBBY)
        self.controller._passo_lobby(lobby)
        self.assertEqual(self.controller.fase, REINICIANDO)

        self.controller._passo_reiniciando(lobby)
        self.controller._passo_reiniciando(lobby)
        self.assertEqual(self.controller.fase, INICIANDO_PARTIDA)
        self.assertEqual(self.controller._clicar.call_count, 1)

        self.controller._passo_iniciando_partida(partida)
        self.assertEqual(self.controller.fase, INICIANDO_PARTIDA)
        self.controller._passo_iniciando_partida(partida)
        self.assertEqual(self.controller.fase, EM_PARTIDA)

        self.controller.ultimo_hud = monotonic()
        self.controller._passo_em_partida(eliminado)
        self.assertEqual(self.controller.fase, EM_PARTIDA)
        self.controller.w_pressionado = True
        self.controller._tecla_cima = Mock()
        self.controller.ultimo_hud = monotonic() - HUD_SUMIU_SEGUNDOS - 1
        self.controller._passo_em_partida(eliminado)
        self.assertEqual(self.controller.fase, ELIMINADO)
        self.assertFalse(self.controller.w_pressionado)

        self.controller._passo_eliminado(eliminado)
        self.assertEqual(self.controller.fase, RETORNANDO_LOBBY)
        self.assertEqual(self.controller._clicar.call_count, 2)

        self.controller._passo_retornando_lobby(lobby)
        self.controller._passo_retornando_lobby(lobby)
        self.assertEqual(self.controller.fase, REINICIANDO)
        self.assertEqual(self.controller.ciclos, 1)

        self.controller._passo_reiniciando(lobby)
        self.controller._passo_reiniciando(lobby)
        self.assertEqual(self.controller.fase, INICIANDO_PARTIDA)
        self.assertEqual(self.controller._clicar.call_count, 3)

    def test_transicao_invalida_e_rejeitada(self):
        with self.assertRaises(RuntimeError):
            self.controller._mudar_fase(EM_PARTIDA)

    def test_timeouts_nao_simulam_transicoes_visuais(self):
        partida = self.carregar_tela("em_partida.png")
        eliminado = self.carregar_tela("tela_eliminado.png")

        self.controller.fase = INICIANDO_PARTIDA
        self.controller.fase_inicio = monotonic() - TIMEOUT_FILA - 1
        self.controller._passo_iniciando_partida(eliminado)
        self.assertEqual(self.controller.fase, INICIANDO_PARTIDA)

        self.controller.fase = EM_PARTIDA
        self.controller.fase_inicio = monotonic() - TIMEOUT_PARTIDA - 1
        self.controller.ultimo_hud = monotonic()
        self.controller.w_pressionado = True
        self.controller._tecla_cima = Mock()
        self.controller._passo_em_partida(partida)
        self.assertEqual(self.controller.fase, EM_PARTIDA)
        self.assertFalse(self.controller.w_pressionado)


if __name__ == "__main__":
    unittest.main()
