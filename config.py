INTERVALO_MONITORAMENTO = 1.0

PRECISAO_RECONHECIMENTO = 0.88

from pathlib import Path

# Resolve assets relative to this file, independent of the launch directory.
PASTA_REFERENCIAS = str(Path(__file__).resolve().parent / "referencias")

NOME_PROJETO = "Macro Lab"
VERSAO = "6.0"

# ---------------------------------------------------------------
# Imagens de referencia (salvar dentro da pasta "referencias")
# ---------------------------------------------------------------
IMG_JOGAR = "botao_jogar.png"          # botao JOGAR no lobby
IMG_EM_PARTIDA = "em_partida.png"      # algo fixo do HUD durante a partida
IMG_SAIR = "botao_sair_retornar_ao_lobby.png"  # botao de sair / voltar ao lobby
IMG_ELIMINADO = "tela_eliminado.png"   # tela de eliminado
IMG_LOBBY = "lobby.png"                # algo que so aparece no lobby
IMG_CONFIRMAR = "botao_confirmar.png"  # confirmacao de sair (opcional)

# ---------------------------------------------------------------
# Teclas e tempos
# ---------------------------------------------------------------
DIAGNOSTICO_A_CADA = 5.0          # segundos entre logs de "melhor precisao"

TECLA_FRENTE = "w"
REPRESSIONAR_FRENTE_A_CADA = 10.0   # segundos
HUD_SUMIU_SEGUNDOS = 8.0            # HUD ausente por esse tempo = eliminado / fim
ESC_SE_NADA_APARECER = 6.0          # segundos na fase SAINDO sem achar botoes
TIMEOUT_FILA = 600                  # 10 min na fila sem iniciar partida
TIMEOUT_PARTIDA = 2400              # 40 min maximo numa partida
TIMEOUT_SAINDO = 120                # 2 min tentando sair

# Tecla global para parar o macro mesmo com o jogo em tela cheia
TECLA_PARADA = "f8"
