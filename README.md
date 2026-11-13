# Macro Lab

Aplicação desktop em Python para captura de tela, reconhecimento de referências visuais e registro de eventos. Use a automação de entrada somente em aplicações próprias ou em ambientes de teste nos quais você tenha autorização.

## Requisitos

- Windows 10 ou 11
- Python 3.11 ou superior

## Instalação

Abra o PowerShell nesta pasta e execute:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente, use os executáveis diretamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## Execução

Com o ambiente ativado:

```powershell
python main.py
```

Clique em **INICIAR** com a tela do Lobby visível. O ciclo é controlado pelos estados `LOBBY`, `REINICIANDO`, `INICIANDO_PARTIDA`, `EM_PARTIDA`, `ELIMINADO` e `RETORNANDO_LOBBY`. Os botões de início, retorno e revanche precisam ser reconhecidos em duas capturas consecutivas antes de qualquer clique. A entrada na partida é confirmada pelo minimapa e pela área de inventário do HUD; o movimento com **W** só começa após essa confirmação.

Quando o HUD desaparece, o controlador solta **W** imediatamente. Só muda para `ELIMINADO` após reconhecer a interface de fim; então aguarda o botão **RETORNAR AO LOBBY** e o botão **JOGAR NOVAMENTE** ficarem visíveis antes de clicar. Se surgir uma confirmação de saída configurada, ela também é clicada uma única vez. O Lobby só é considerado carregado quando o botão **JOGAR** for reconhecido. Timeouts geram avisos e mantêm o controlador aguardando evidência visual, sem assumir uma transição nem clicar às cegas.

Pressione **F8** para interromper a automação imediatamente. A inicialização registra no histórico se o atalho global pôde ser configurado. O programa precisa manter a sessão de desktop desbloqueada e visível para capturar a tela.

## Referências visuais e calibração

O botão **Referências** abre a pasta `referencias`. Os templates de botões são pesquisados em várias escalas para tolerar diferenças de resolução. `botao_jogar_novamente.png` identifica a tela de eliminação junto com o botão de retorno. O HUD de partida é verificado pelas bordas do minimapa e do inventário, em regiões proporcionais ao tamanho da captura; os limites ficam em `config.py` (`LIMIAR_BORDAS_MINIMAPA` e `LIMIAR_BORDAS_INVENTARIO`).

Se a interface do jogo mudar, recapture os botões e ajuste os limites do HUD. `em_partida.png`, `lobby.png` e `tela_eliminado.png` também podem ser usados para diagnóstico visual; o reconhecimento do HUD não compara uma captura inteira de partida, que varia enquanto a câmera se move. Para inspecionar as correspondências e salvar uma captura da tela atual, execute:

```powershell
python teste_visao.py
```

Para validar as detecções e as transições usando as imagens de referência do projeto:

```powershell
python -m unittest discover -s tests -v
```

## Estrutura

- `main.py`: inicialização da aplicação e ajuste de DPI no Windows.
- `interface.py`: janela Tkinter, histórico e ícone da bandeja.
- `automation.py`: máquina de estados, teclado/mouse e ciclo de monitoramento.
- `vision.py`: captura, cache de referências, busca multiescala e leitura do HUD.
- `config.py`: limites de reconhecimento, imagens, teclas e tempos.
- `logger.py`: gravação do histórico.
- `referencias/`: imagens usadas pelo reconhecimento.

O arquivo `historico.log` fica junto aos arquivos do projeto, mesmo que a aplicação seja iniciada a partir de outra pasta.
