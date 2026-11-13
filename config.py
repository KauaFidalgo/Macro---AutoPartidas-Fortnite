INTERVALO_MONITORAMENTO = 1.0

PRECISAO_RECONHECIMENTO = 0.88
LIMIAR_BORDAS_MINIMAPA = 0.10
LIMIAR_BORDAS_INVENTARIO = 0.04
REGIAO_BOTAO_JOGAR = (0.02, 0.72, 0.30, 0.96)
REGIAO_ACOES_ELIMINACAO = (0.58, 0.32, 0.995, 0.60)

from pathlib import Path

# Resolve assets relative to this file, independent of the launch directory.
PASTA_REFERENCIAS = str(Path(__file__).resolve().parent / "referencias")

NOME_PROJETO = "Macro Lab"
VERSAO = "6.0"

# ---------------------------------------------------------------
# Imagens de referencia (salvar dentro da pasta "referencias")
# ---------------------------------------------------------------
IMG_JOGAR = "botao_jogar.png"          # botao JOGAR no lobby
IMG_EM_PARTIDA = "em_partida.png"      # captura de referencia para diagnostico
IMG_SAIR = "botao_sair_retornar_ao_lobby.png"  # botao de sair / voltar ao lobby
IMG_ELIMINADO = "tela_eliminado.png"   # tela de eliminado
IMG_JOGAR_NOVAMENTE = "botao_jogar_novamente.png"
IMG_LOBBY = "lobby.png"                # algo que so aparece no lobby
IMG_CONFIRMAR = "botao_confirmar.png"  # confirmacao de sair (opcional)

# ---------------------------------------------------------------
# Teclas e tempos
# ---------------------------------------------------------------
DIAGNOSTICO_A_CADA = 5.0          # segundos entre logs de "melhor precisao"

TECLA_FRENTE = "w"
REPRESSIONAR_FRENTE_A_CADA = 10.0   # segundos
HUD_SUMIU_SEGUNDOS = 8.0            # HUD ausente por esse tempo = eliminado / fim
TIMEOUT_FILA = 600                  # 10 min na fila sem iniciar partida
TIMEOUT_PARTIDA = 2400              # 40 min maximo numa partida
TIMEOUT_SAINDO = 120                # 2 min tentando sair

# Tecla global para parar o macro mesmo com o jogo em tela cheia
TECLA_PARADA = "f8"
