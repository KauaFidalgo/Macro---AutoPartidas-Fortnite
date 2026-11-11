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

O botão **Referências** abre a pasta `referencias`. As imagens devem representar elementos visuais estáveis da aplicação de teste e estar na mesma resolução/escala usada durante a captura. O arquivo `historico.log` fica junto aos arquivos do projeto, mesmo que a aplicação seja iniciada a partir de outra pasta.

Para inspecionar o reconhecimento visual em uma tela de teste, execute:

```powershell
python teste_visao.py
```

## Estrutura

- `main.py`: inicialização da aplicação e ajuste de DPI no Windows.
- `interface.py`: janela Tkinter, histórico e ícone da bandeja.
- `automation.py`: controlador e ciclo de monitoramento configurado no projeto.
- `vision.py`: captura, cache de referências e comparação de imagens.
- `config.py`: parâmetros e nomes de referências.
- `logger.py`: gravação do histórico.
- `referencias/`: imagens usadas pelo reconhecimento.

O programa precisa manter a sessão de desktop desbloqueada e visível para capturar a tela. Mudanças de resolução, escala do Windows, tema ou animações podem exigir novas imagens de referência e ajuste de `PRECISAO_RECONHECIMENTO` em `config.py`.
