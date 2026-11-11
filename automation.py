import threading
import time

import pyautogui

try:
    import pydirectinput
    pydirectinput.PAUSE = 0
except ImportError:
    pydirectinput = None

try:
    import keyboard
except ImportError:
    keyboard = None

from vision import capturar, localizar, ultimas_precisoes
from config import (
    INTERVALO_MONITORAMENTO,
    IMG_JOGAR, IMG_EM_PARTIDA, IMG_SAIR, IMG_CONFIRMAR,
    IMG_ELIMINADO, IMG_LOBBY, DIAGNOSTICO_A_CADA, PRECISAO_RECONHECIMENTO,
    TECLA_FRENTE, REPRESSIONAR_FRENTE_A_CADA,
    HUD_SUMIU_SEGUNDOS, ESC_SE_NADA_APARECER,
    TIMEOUT_FILA, TIMEOUT_PARTIDA, TIMEOUT_SAINDO,
    TECLA_PARADA
)

LOBBY = "LOBBY"
FILA = "FILA"
PARTIDA = "PARTIDA"
SAINDO = "SAINDO"


class MacroController:

    def __init__(self, callback=None):

        self.callback = callback

        self.running = False
        self.paused = False

        self.ciclos = 0  # partidas concluidas
        self.tempo_acumulado = 0
        self.inicio_tempo = None

        self.fase = LOBBY
        self.fase_inicio = time.monotonic()
        self.ultimo_hud = 0.0
        self.ultimo_w = 0.0
        self.ultimo_visto_saindo = 0.0
        self.w_pressionado = False
        self.ultimo_diagnostico = 0.0

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.thread = None

        self.lock = threading.Lock()

        self._registrar_atalho()

    # ------------------------------------------------------------
    # Utilitarios
    # ------------------------------------------------------------
    def registrar(self, mensagem):

        if self.callback:
            self.callback(mensagem)

    def _registrar_atalho(self):

        if keyboard is None:
            return

        try:
            keyboard.add_hotkey(TECLA_PARADA, self.parar)
        except Exception:
            pass

    def _mudar_fase(self, fase, motivo=""):

        self.fase = fase
        self.fase_inicio = time.monotonic()

        texto = f"Fase: {fase}"
        if motivo:
            texto += f" ({motivo})"

        self.registrar(texto)

    def _diagnostico(self, *nomes):
        """Loga a melhor precisao medida quando algo nao e reconhecido."""

        agora = time.monotonic()

        if agora - self.ultimo_diagnostico < DIAGNOSTICO_A_CADA:
            return

        self.ultimo_diagnostico = agora

        for nome in nomes:
            valor = ultimas_precisoes.get(nome)

            if valor is None:
                self.registrar(
                    f"[{self.fase}] '{nome}' nao encontrado na pasta "
                    f"referencias (ou maior que a tela)"
                )
            else:
                self.registrar(
                    f"[{self.fase}] '{nome}': melhor {valor:.1%} "
                    f"(minimo {PRECISAO_RECONHECIMENTO:.0%})"
                )

    def _tempo_na_fase(self):
        return time.monotonic() - self.fase_inicio

    # ------------------------------------------------------------
    # Entrada (teclado / mouse)
    # ------------------------------------------------------------
    def _tecla_baixo(self, tecla):

        if pydirectinput:
            pydirectinput.keyDown(tecla)
        else:
            pyautogui.keyDown(tecla)

    def _tecla_cima(self, tecla):

        if pydirectinput:
            pydirectinput.keyUp(tecla)
        else:
            pyautogui.keyUp(tecla)

    def _apertar(self, tecla):

        self._tecla_baixo(tecla)
        time.sleep(0.08)
        self._tecla_cima(tecla)

    def _clicar(self, posicao):

        x, y = posicao
        pyautogui.moveTo(x, y, duration=0.25)
        time.sleep(0.1)
        pyautogui.click()

    def _segurar_frente(self):

        self._tecla_baixo(TECLA_FRENTE)
        self.w_pressionado = True
        self.ultimo_w = time.monotonic()

    def _soltar_frente(self):

        if self.w_pressionado:
            self._tecla_cima(TECLA_FRENTE)
            self.w_pressionado = False

    # ------------------------------------------------------------
    # Controle (chamado pela interface)
    # ------------------------------------------------------------
    def iniciar(self):

        with self.lock:

            if self.running and not self.paused:
                return

            if self.running and self.paused:

                self.paused = False
                self.pause_event.clear()
                self.inicio_tempo = time.monotonic()

                self.registrar("Macro retomado")
                return

            self.running = True
            self.paused = False

            self.ciclos = 0
            self.tempo_acumulado = 0
            self.inicio_tempo = time.monotonic()

            self.fase = LOBBY
            self.fase_inicio = time.monotonic()

            self.stop_event.clear()
            self.pause_event.clear()

            self.thread = threading.Thread(
                target=self.monitorar,
                daemon=True
            )

            self.thread.start()

        self.registrar("Macro iniciado")

    def pausar(self):

        with self.lock:

            if not self.running or self.paused:
                return

            self.tempo_acumulado += (
                time.monotonic() - self.inicio_tempo
            )

            self.inicio_tempo = None
            self.paused = True
            self.pause_event.set()

        self.registrar("Macro pausado")

    def parar(self):

        with self.lock:

            if not self.running:
                return

            self.running = False
            self.paused = False

            self.stop_event.set()
            self.pause_event.clear()

            self.inicio_tempo = None
            self.tempo_acumulado = 0

        try:
            self._soltar_frente()
        except Exception:
            pass

        self.registrar("Macro encerrado")

    # ------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------
    def monitorar(self):

        while not self.stop_event.is_set():

            if self.pause_event.is_set():

                try:
                    self._soltar_frente()
                except Exception:
                    pass

                self.stop_event.wait(0.3)
                continue

            try:
                self._passo()

            except Exception as erro:
                self.registrar(f"Erro no macro: {erro}")

            self.stop_event.wait(INTERVALO_MONITORAMENTO)

        try:
            self._soltar_frente()
        except Exception:
            pass

    def _passo(self):

        tela = capturar()

        if self.fase == LOBBY:
            self._passo_lobby(tela)

        elif self.fase == FILA:
            self._passo_fila(tela)

        elif self.fase == PARTIDA:
            self._passo_partida(tela)

        elif self.fase == SAINDO:
            self._passo_saindo(tela)

    # --- LOBBY: clica em JOGAR ---------------------------------
    def _passo_lobby(self, tela):

        posicao = localizar(tela, IMG_JOGAR)

        if posicao:
            self._clicar(posicao)
            self._mudar_fase(FILA, "botao JOGAR clicado")
        else:
            self._diagnostico(IMG_JOGAR)

    # --- FILA: espera a partida comecar ------------------------
    def _passo_fila(self, tela):

        if localizar(tela, IMG_EM_PARTIDA):
            self.ultimo_hud = time.monotonic()
            self._segurar_frente()
            self._mudar_fase(PARTIDA, "partida iniciada")
            return

        # Se o botao JOGAR voltou, a fila foi cancelada
        if localizar(tela, IMG_JOGAR) and self._tempo_na_fase() > 5:
            self._mudar_fase(LOBBY, "fila cancelada")
            return

        if self._tempo_na_fase() > TIMEOUT_FILA:
            self._mudar_fase(LOBBY, "timeout na fila")

    # --- PARTIDA: anda pra frente e detecta o fim --------------
    def _passo_partida(self, tela):

        agora = time.monotonic()

        if localizar(tela, IMG_EM_PARTIDA):
            self.ultimo_hud = agora

        # Mantem o W pressionado (anti-AFK)
        if (
            not self.w_pressionado
            or agora - self.ultimo_w > REPRESSIONAR_FRENTE_A_CADA
        ):
            self._soltar_frente()
            self._segurar_frente()

        # Tela de eliminado ou botao de sair apareceu
        if localizar(tela, IMG_ELIMINADO):
            self._soltar_frente()
            self._mudar_fase(SAINDO, "tela de eliminado")
            return

        if localizar(tela, IMG_SAIR):
            self._soltar_frente()
            self._mudar_fase(SAINDO, "botao sair detectado")
            return

        # HUD sumiu por um tempo = eliminado ou partida encerrada
        if agora - self.ultimo_hud > HUD_SUMIU_SEGUNDOS:
            self._soltar_frente()
            self._mudar_fase(SAINDO, "HUD da partida sumiu")
            return

        if self._tempo_na_fase() > TIMEOUT_PARTIDA:
            self._soltar_frente()
            self._mudar_fase(SAINDO, "timeout da partida")

    # --- SAINDO: volta pro lobby -------------------------------
    def _passo_saindo(self, tela):

        agora = time.monotonic()

        confirmar = localizar(tela, IMG_CONFIRMAR)

        if confirmar:
            self._clicar(confirmar)
            self.ultimo_visto_saindo = agora
            self.registrar("Saida confirmada")
            return

        sair = localizar(tela, IMG_SAIR)

        if sair:
            self._clicar(sair)
            self.ultimo_visto_saindo = agora
            self.registrar("Clicou em sair")
            return

        if localizar(tela, IMG_JOGAR) or localizar(tela, IMG_LOBBY):
            self.ciclos += 1
            self._mudar_fase(
                LOBBY, f"partida {self.ciclos} concluida"
            )
            return

        # Nada reconhecido: tenta abrir o menu com ESC
        if (
            agora - max(self.ultimo_visto_saindo, self.fase_inicio)
            > ESC_SE_NADA_APARECER
        ):
            self._apertar("esc")
            self.ultimo_visto_saindo = agora
            self.registrar("Nada reconhecido, ESC pressionado")

        if self._tempo_na_fase() > TIMEOUT_SAINDO:
            self._mudar_fase(LOBBY, "timeout ao sair")

    # ------------------------------------------------------------
    def obter_tempo(self):

        tempo = self.tempo_acumulado

        if self.running and not self.paused:
            tempo += time.monotonic() - self.inicio_tempo

        return int(tempo)

    def obter_status(self):

        if not self.running:
            return "DESLIGADO"

        if self.paused:
            return "PAUSADO"

        return "EXECUTANDO"