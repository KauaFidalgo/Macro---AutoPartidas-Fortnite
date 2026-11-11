import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from queue import Queue, Empty
from datetime import datetime
import os

import pystray
from PIL import Image, ImageDraw

from automation import MacroController
from logger import registrar


BG = "#111827"
PANEL = "#1E293B"
BORDER = "#334155"
WHITE = "#F8FAFC"
MUTED = "#94A3B8"
GREEN = "#22C55E"
YELLOW = "#EAB308"
RED = "#EF4444"
BLUE = "#3B82F6"


class MacroInterface:

    def __init__(self, janela):

        self.janela = janela
        self.janela.title("Macro Lab 6.0")
        self.janela.geometry("760x690")
        self.janela.minsize(650, 620)
        self.janela.configure(bg=BG)

        self.fila = Queue()
        self.eventos = 0
        self.icon = None
        self.oculto = False
        self.fechando = False

        self.macro = MacroController(
            callback=self.enviar_evento
        )

        self.criar_interface()

        self.janela.bind(
            "<Unmap>",
            self.ao_minimizar
        )

        self.janela.protocol(
            "WM_DELETE_WINDOW",
            self.minimizar
        )

        self.atualizar()
        self.processar_fila()

    def criar_interface(self):

        container = tk.Frame(self.janela, bg=BG)
        container.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=25
        )

        header = tk.Frame(container, bg=BG)
        header.pack(fill="x", pady=(0, 20))

        tk.Label(
            header,
            text="◆ MACRO LAB",
            font=("Segoe UI", 23, "bold"),
            fg=WHITE,
            bg=BG
        ).pack(side="left")

        tk.Label(
            header,
            text="VERSION 6.0",
            font=("Segoe UI", 9, "bold"),
            fg=BLUE,
            bg=BG
        ).pack(side="right", pady=10)

        self.status_label = tk.Label(
            container,
            text="DESLIGADO",
            font=("Segoe UI", 20, "bold"),
            fg=RED,
            bg=PANEL,
            pady=20
        )

        self.status_label.pack(fill="x", pady=10)

        indicadores = tk.Frame(container, bg=BG)
        indicadores.pack(fill="x", pady=12)

        self.ciclo_label = self.criar_indicador(
            indicadores, "PARTIDAS", "0"
        )

        self.tempo_label = self.criar_indicador(
            indicadores, "TEMPO ATIVO", "00:00:00"
        )

        self.evento_label = self.criar_indicador(
            indicadores, "EVENTOS", "0"
        )

        tk.Label(
            container,
            text="CONTROLES",
            font=("Segoe UI", 10, "bold"),
            fg=WHITE,
            bg=BG
        ).pack(anchor="w", pady=(20, 10))

        controles = tk.Frame(container, bg=BG)
        controles.pack(fill="x")

        self.criar_botao(
            controles, "INICIAR", GREEN,
            self.iniciar
        )

        self.criar_botao(
            controles, "PAUSAR", "#A16207",
            self.pausar
        )

        self.criar_botao(
            controles, "STOP", "#B91C1C",
            self.parar
        )

        extras = tk.Frame(container, bg=BG)
        extras.pack(fill="x", pady=10)

        self.criar_botao(
            extras, "REFERÊNCIAS", BLUE,
            self.abrir_referencias
        )

        self.criar_botao(
            extras, "MINIMIZAR", "#475569",
            self.minimizar
        )

        tk.Label(
            container,
            text="HISTÓRICO DE MONITORAMENTO",
            font=("Segoe UI", 10, "bold"),
            fg=WHITE,
            bg=BG
        ).pack(anchor="w", pady=(15, 10))

        tabela_frame = tk.Frame(container, bg=PANEL)
        tabela_frame.pack(fill="both", expand=True)

        self.tabela = ttk.Treeview(
            tabela_frame,
            columns=("hora", "evento"),
            show="headings",
            height=8
        )

        self.tabela.heading("hora", text="HORÁRIO")
        self.tabela.heading("evento", text="ATIVIDADE")

        self.tabela.column(
            "hora", width=100, anchor="center"
        )

        self.tabela.column("evento", width=450)

        self.tabela.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        tk.Label(
            container,
            text="MACRO LAB 6.0 • BACKGROUND AUTOMATION",
            font=("Segoe UI", 8),
            fg=MUTED,
            bg=BG
        ).pack(pady=(15, 0))

    def criar_indicador(self, pai, titulo, valor):

        card = tk.Frame(
            pai,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=4
        )

        tk.Label(
            card,
            text=titulo,
            font=("Segoe UI", 8, "bold"),
            fg=MUTED,
            bg=PANEL
        ).pack(pady=(12, 5))

        label = tk.Label(
            card,
            text=valor,
            font=("Segoe UI", 16, "bold"),
            fg=WHITE,
            bg=PANEL
        )

        label.pack(pady=(0, 12))

        return label

    def criar_botao(self, pai, texto, cor, comando):

        tk.Button(
            pai,
            text=texto,
            command=comando,
            font=("Segoe UI", 9, "bold"),
            bg=cor,
            fg=WHITE,
            activebackground=cor,
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            cursor="hand2",
            height=2
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=4
        )

    # Comunicação segura entre thread e interface
    def enviar_evento(self, mensagem):
        self.fila.put(mensagem)

    def processar_fila(self):

        try:

            while True:

                mensagem = self.fila.get_nowait()

                if isinstance(mensagem, tuple) and mensagem[0] == "__acao__":
                    mensagem[1]()
                    if self.fechando:
                        return
                    continue

                registrar(mensagem)

                self.eventos += 1

                hora = datetime.now().strftime(
                    "%H:%M:%S"
                )

                self.tabela.insert(
                    "",
                    0,
                    values=(hora, mensagem)
                )

                self.evento_label.config(
                    text=str(self.eventos)
                )

        except Empty:
            pass

        if not self.fechando:
            self.janela.after(200, self.processar_fila)

    def atualizar(self):

        estado = self.macro.obter_status()

        cores = {
            "EXECUTANDO": GREEN,
            "PAUSADO": YELLOW,
            "DESLIGADO": RED
        }

        texto = estado

        if estado == "EXECUTANDO":
            texto = f"{estado} • {self.macro.fase}"

        self.status_label.config(
            text=texto,
            fg=cores[estado]
        )

        self.ciclo_label.config(
            text=str(self.macro.ciclos)
        )

        segundos = self.macro.obter_tempo()

        h = segundos // 3600
        m = (segundos % 3600) // 60
        s = segundos % 60

        self.tempo_label.config(
            text=f"{h:02}:{m:02}:{s:02}"
        )

        self.janela.after(
            250,
            self.atualizar
        )

    def iniciar(self):
        self.macro.iniciar()

    def pausar(self):
        self.macro.pausar()

    def parar(self):
        self.macro.parar()

    def abrir_referencias(self):

        pasta = os.path.abspath(os.path.join(os.path.dirname(__file__), "referencias"))

        os.makedirs(pasta, exist_ok=True)

        os.startfile(pasta)

    # Ícone da bandeja
    def criar_imagem_icone(self):

        imagem = Image.new(
            "RGB", (64, 64), "#111827"
        )

        desenho = ImageDraw.Draw(imagem)

        desenho.rounded_rectangle(
            (7, 7, 57, 57),
            radius=12,
            fill="#2563EB"
        )

        desenho.ellipse(
            (20, 20, 44, 44),
            fill="#FFFFFF"
        )

        return imagem

    def criar_bandeja(self):

        if self.icon:
            return

        menu = pystray.Menu(
            pystray.MenuItem(
                "Abrir Macro Lab",
                self.abrir_janela
            ),
            pystray.MenuItem(
                "Iniciar",
                self.acao_iniciar
            ),
            pystray.MenuItem(
                "Pausar",
                self.acao_pausar
            ),
            pystray.MenuItem(
                "STOP",
                self.acao_parar
            ),
            pystray.MenuItem(
                "Encerrar programa",
                self.acao_sair
            )
        )

        self.icon = pystray.Icon(
            "MacroLab",
            self.criar_imagem_icone(),
            "Macro Lab 6.0",
            menu
        )

        self.icon.run_detached()

    def ao_minimizar(self, evento):

        if evento.widget == self.janela:
            if self.janela.state() == "iconic":
                self.minimizar()

    def minimizar(self):

        self.criar_bandeja()

        self.oculto = True

        self.janela.withdraw()

    def abrir_janela(self, icon=None, item=None):

        self.janela.after(
            0,
            self.mostrar_janela
        )

    def mostrar_janela(self):

        self.janela.deiconify()
        self.janela.state("normal")
        self.oculto = False

    def acao_iniciar(self, icon, item):
        self.fila.put(("__acao__", self.iniciar))

    def acao_pausar(self, icon, item):
        self.fila.put(("__acao__", self.pausar))

    def acao_parar(self, icon, item):
        self.fila.put(("__acao__", self.parar))

    def acao_sair(self, icon, item):
        self.fila.put(("__acao__", self.fechar))

    def fechar(self):

        if self.fechando:
            return

        self.fechando = True

        self.macro.parar()

        if self.icon:
            self.icon.stop()
            self.icon = None

        self.janela.destroy()
