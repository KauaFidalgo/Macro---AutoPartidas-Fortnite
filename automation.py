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

from vision import capturar, localizar, medir_hud_partida, ultimas_precisoes
from config import (
    DIAGNOSTICO_A_CADA,
    HUD_SUMIU_SEGUNDOS,
    IMG_CONFIRMAR,
    IMG_ELIMINADO,
    IMG_JOGAR,
    IMG_JOGAR_NOVAMENTE,
    IMG_SAIR,
    INTERVALO_MONITORAMENTO,
    LIMIAR_BORDAS_INVENTARIO,
    LIMIAR_BORDAS_MINIMAPA,
    PRECISAO_RECONHECIMENTO,
    REGIAO_ACOES_ELIMINACAO,
    REGIAO_BOTAO_JOGAR,
    REPRESSIONAR_FRENTE_A_CADA,
    TECLA_FRENTE,
    TECLA_PARADA,
    TIMEOUT_FILA,
    TIMEOUT_PARTIDA,
    TIMEOUT_SAINDO
)

LOBBY = "LOBBY"
INICIANDO_PARTIDA = "INICIANDO_PARTIDA"
EM_PARTIDA = "EM_PARTIDA"
ELIMINADO = "ELIMINADO"
RETORNANDO_LOBBY = "RETORNANDO_LOBBY"
REINICIANDO = "REINICIANDO"

TRANSICOES = {
    LOBBY: {REINICIANDO},
    REINICIANDO: {INICIANDO_PARTIDA},
    INICIANDO_PARTIDA: {EM_PARTIDA, LOBBY},
    EM_PARTIDA: {ELIMINADO},
    ELIMINADO: {RETORNANDO_LOBBY},
    RETORNANDO_LOBBY: {REINICIANDO}
}

AMOSTRAS_PARA_CONFIRMAR = 2


class MacroController:

    def __init__(self, callback=None):
        self.callback = callback
        self.running = False
        self.paused = False

        self.ciclos = 0
        self.tempo_acumulado = 0
        self.inicio_tempo = None

        self.fase = LOBBY
        self.fase_inicio = time.monotonic()
        self.ultimo_hud = 0.0
        self.ultimo_w = 0.0
        self.w_pressionado = False
        self.ultimo_diagnostico = 0.0
        self.ultima_medicao_hud = {}
        self.alerta_timeout_registrado = False
        self._evidencias = {}
        self._acao_enviada = False

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.thread = None
        self.lock = threading.Lock()

        self._registrar_atalho()

    def registrar(self, mensagem):
        if self.callback:
            self.callback(mensagem)

    def _registrar_atalho(self):
        if keyboard is None:
            self.registrar(
                f"ERRO: atalho de emergência {TECLA_PARADA.upper()} indisponível "
                "(biblioteca keyboard não instalada)"
            )
            return

        try:
            keyboard.add_hotkey(TECLA_PARADA, self.parar)
            self.registrar(
                f"Atalho de emergência {TECLA_PARADA.upper()} registrado"
            )
        except Exception as erro:
            self.registrar(
                f"ERRO ao registrar atalho {TECLA_PARADA.upper()}: "
                f"{type(erro).__name__}: {erro}"
            )

    def _mudar_fase(self, fase, motivo=""):
        permitidas = TRANSICOES.get(self.fase, set())
        if fase not in permitidas:
            raise RuntimeError(
                f"Transição de estado inválida: {self.fase} -> {fase}"
            )

        self.fase = fase
        self.fase_inicio = time.monotonic()
        self._evidencias.clear()
        self._acao_enviada = False
        self.alerta_timeout_registrado = False

        texto = f"Fase: {fase}"
        if motivo:
            texto += f" ({motivo})"
        self.registrar(texto)

    def _confirmar(self, nome, detectado):
        if not detectado:
            self._evidencias[nome] = 0
            return False

        quantidade = self._evidencias.get(nome, 0) + 1
        self._evidencias[nome] = quantidade
        return quantidade >= AMOSTRAS_PARA_CONFIRMAR

    def _diagnostico(self, *nomes):
        agora = time.monotonic()
        if agora - self.ultimo_diagnostico < DIAGNOSTICO_A_CADA:
            return

        self.ultimo_diagnostico = agora
        for nome in nomes:
            precisao = ultimas_precisoes.get(nome)
            if precisao is None:
                self.registrar(
                    f"[{self.fase}] '{nome}' ausente em referencias "
                    "ou incompatível com a resolução atual"
                )
            else:
                self.registrar(
                    f"[{self.fase}] '{nome}': score {precisao:.1%} "
                    f"(mínimo {PRECISAO_RECONHECIMENTO:.0%})"
                )

    def _diagnostico_hud(self):
        agora = time.monotonic()
        if agora - self.ultimo_diagnostico < DIAGNOSTICO_A_CADA:
            return

        self.ultimo_diagnostico = agora
        mapa = self.ultima_medicao_hud.get("minimapa", 0.0)
        inventario = self.ultima_medicao_hud.get("inventario", 0.0)
        self.registrar(
            f"[{self.fase}] HUD: minimapa {mapa:.1%} "
            f"(mín. {LIMIAR_BORDAS_MINIMAPA:.0%}), inventário "
            f"{inventario:.1%} (mín. {LIMIAR_BORDAS_INVENTARIO:.0%})"
        )

    def _tempo_na_fase(self):
        return time.monotonic() - self.fase_inicio

    def _registrar_timeout(self, contexto):
        if self._tempo_na_fase() > TIMEOUT_SAINDO:
            self._registrar_aviso(
                f"{contexto} há mais de {TIMEOUT_SAINDO}s; "
                "aguardando confirmação visual e sem executar cliques"
            )

    def _registrar_aviso(self, mensagem):
        if not self.alerta_timeout_registrado:
            self.registrar(f"AVISO: {mensagem}")
            self.alerta_timeout_registrado = True

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

    def _segurar_frente(self):
        if self.stop_event.is_set():
            return
        self._tecla_baixo(TECLA_FRENTE)
        self.w_pressionado = True
        self.ultimo_w = time.monotonic()

    def _soltar_frente(self):
        if self.w_pressionado:
            self._tecla_cima(TECLA_FRENTE)
            self.w_pressionado = False

    def _clicar(self, posicao):
        if self.stop_event.is_set():
            return False

        x, y = posicao
        pyautogui.moveTo(x, y, duration=0)
        if self.stop_event.is_set():
            return False
        pyautogui.click()
        return True

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
            self._evidencias.clear()
            self._acao_enviada = False
            self.alerta_timeout_registrado = False
            self.stop_event.clear()
            self.pause_event.clear()

            self.thread = threading.Thread(target=self.monitorar, daemon=True)
            self.thread.start()

        self.registrar("Macro iniciado")

    def pausar(self):
        with self.lock:
            if not self.running or self.paused:
                return

            self.tempo_acumulado += time.monotonic() - self.inicio_tempo
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
        except Exception as erro:
            self.registrar(
                f"ERRO ao soltar {TECLA_FRENTE.upper()} durante a parada: "
                f"{type(erro).__name__}: {erro}"
            )

        self.registrar("Macro encerrado")

    def monitorar(self):
        while not self.stop_event.is_set():
            if self.pause_event.is_set():
                try:
                    self._soltar_frente()
                except Exception as erro:
                    self.registrar(
                        f"ERRO ao soltar {TECLA_FRENTE.upper()} na pausa: "
                        f"{type(erro).__name__}: {erro}"
                    )
                self.stop_event.wait(0.3)
                continue

            try:
                self._passo()
            except Exception as erro:
                try:
                    self._soltar_frente()
                except Exception as erro_tecla:
                    self.registrar(
                        f"ERRO ao liberar movimento após falha: "
                        f"{type(erro_tecla).__name__}: {erro_tecla}"
                    )
                self.registrar(
                    f"Erro no estado {self.fase}: "
                    f"{type(erro).__name__}: {erro}"
                )

            self.stop_event.wait(INTERVALO_MONITORAMENTO)

        try:
            self._soltar_frente()
        except Exception as erro:
            self.registrar(
                f"ERRO ao liberar movimento no encerramento: "
                f"{type(erro).__name__}: {erro}"
            )

    def _passo(self):
        tela = capturar()

        if self.fase == LOBBY:
            self._passo_lobby(tela)
        elif self.fase == REINICIANDO:
            self._passo_reiniciando(tela)
        elif self.fase == INICIANDO_PARTIDA:
            self._passo_iniciando_partida(tela)
        elif self.fase == EM_PARTIDA:
            self._passo_em_partida(tela)
        elif self.fase == ELIMINADO:
            self._passo_eliminado(tela)
        elif self.fase == RETORNANDO_LOBBY:
            self._passo_retornando_lobby(tela)

    def _passo_lobby(self, tela):
        jogar = localizar(tela, IMG_JOGAR, regiao=REGIAO_BOTAO_JOGAR)
        if self._confirmar("botao_jogar_lobby", bool(jogar)):
            self._mudar_fase(REINICIANDO, "botão JOGAR confirmado no Lobby")
        else:
            self._diagnostico(IMG_JOGAR)

    def _passo_reiniciando(self, tela):
        jogar = localizar(tela, IMG_JOGAR, regiao=REGIAO_BOTAO_JOGAR)
        if not self._confirmar("botao_jogar_reiniciar", bool(jogar)):
            self._diagnostico(IMG_JOGAR)
            return

        if self._acao_enviada:
            return
        self._acao_enviada = True
        if self._clicar(jogar):
            self._mudar_fase(INICIANDO_PARTIDA, "botão JOGAR clicado")

    def _passo_iniciando_partida(self, tela):
        jogar = localizar(tela, IMG_JOGAR, regiao=REGIAO_BOTAO_JOGAR)
        if self._tempo_na_fase() > 5:
            if self._confirmar("botao_jogar_fila_cancelada", bool(jogar)):
                self._mudar_fase(
                    LOBBY, "fila cancelada; botão JOGAR reapareceu"
                )
                return
        else:
            self._confirmar("botao_jogar_fila_cancelada", False)

        self.ultima_medicao_hud = medir_hud_partida(tela)
        hud_detectado = (
            self.ultima_medicao_hud["minimapa"] >= LIMIAR_BORDAS_MINIMAPA
            and self.ultima_medicao_hud["inventario"]
            >= LIMIAR_BORDAS_INVENTARIO
        )

        if self._confirmar("hud_partida", hud_detectado):
            self.ultimo_hud = time.monotonic()
            self._segurar_frente()
            self._mudar_fase(EM_PARTIDA, "minimapa e inventário confirmados")
            return

        if self._tempo_na_fase() > TIMEOUT_FILA:
            self._registrar_aviso(
                "timeout aguardando início da partida; "
                "sem confirmação visual para mudar de estado"
            )

        self._diagnostico_hud()

    def _eliminacao_visivel(self, tela):
        retornar = localizar(tela, IMG_SAIR, regiao=REGIAO_ACOES_ELIMINACAO)
        jogar_novamente = localizar(
            tela, IMG_JOGAR_NOVAMENTE, regiao=REGIAO_ACOES_ELIMINACAO
        )
        tela_eliminado = localizar(tela, IMG_ELIMINADO)
        confirmado = bool(retornar and (jogar_novamente or tela_eliminado))
        return retornar, confirmado

    def _passo_em_partida(self, tela):
        agora = time.monotonic()
        self.ultima_medicao_hud = medir_hud_partida(tela)
        hud_detectado = (
            self.ultima_medicao_hud["minimapa"] >= LIMIAR_BORDAS_MINIMAPA
            and self.ultima_medicao_hud["inventario"]
            >= LIMIAR_BORDAS_INVENTARIO
        )

        if hud_detectado:
            self.ultimo_hud = agora
            self._confirmar("tela_eliminado", False)
        else:
            self._soltar_frente()
            _, eliminacao_detectada = self._eliminacao_visivel(tela)
            if self._confirmar("tela_eliminado", eliminacao_detectada):
                self._mudar_fase(
                    ELIMINADO,
                    "interface de eliminação confirmada"
                )
                self._evidencias["interface_eliminacao_pronta"] = 1
            elif agora - self.ultimo_hud > TIMEOUT_SAINDO:
                self._registrar_aviso(
                    "HUD ausente, mas a interface de eliminação ainda "
                    "não foi reconhecida; sem executar cliques"
                )
            elif agora - self.ultimo_hud > HUD_SUMIU_SEGUNDOS:
                self._diagnostico(IMG_SAIR, IMG_JOGAR_NOVAMENTE)
            return

        if self._tempo_na_fase() > TIMEOUT_PARTIDA:
            self._soltar_frente()
            self._registrar_aviso(
                "limite de duração da partida atingido; "
                "movimento interrompido até nova evidência visual"
            )
            return

        if not self.w_pressionado or agora - self.ultimo_w > REPRESSIONAR_FRENTE_A_CADA:
            self._soltar_frente()
            self._segurar_frente()

        if not hud_detectado:
            self._diagnostico_hud()

    def _passo_eliminado(self, tela):
        retornar, eliminacao_detectada = self._eliminacao_visivel(tela)
        if self._confirmar("interface_eliminacao_pronta", eliminacao_detectada):
            if not self._acao_enviada:
                self._acao_enviada = True
                if self._clicar(retornar):
                    self._mudar_fase(
                        RETORNANDO_LOBBY,
                        "botão RETORNAR AO LOBBY clicado"
                    )
            return

        self._diagnostico(IMG_SAIR, IMG_JOGAR_NOVAMENTE)
        self._registrar_timeout("interface de eliminação")

    def _passo_retornando_lobby(self, tela):
        confirmar = localizar(tela, IMG_CONFIRMAR)
        if self._confirmar("confirmacao_saida", bool(confirmar)):
            if not self._acao_enviada:
                self._acao_enviada = True
                if self._clicar(confirmar):
                    self.registrar("Confirmação de retorno ao Lobby clicada")
            return

        jogar = localizar(tela, IMG_JOGAR, regiao=REGIAO_BOTAO_JOGAR)
        if self._confirmar("lobby_carregado", bool(jogar)):
            self.ciclos += 1
            self._mudar_fase(
                REINICIANDO,
                f"Lobby confirmado; partida {self.ciclos} concluída"
            )
            return

        self._diagnostico(IMG_JOGAR)
        self._registrar_timeout("retorno ao Lobby")

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
