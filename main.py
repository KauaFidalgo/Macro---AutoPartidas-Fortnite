import ctypes
import tkinter as tk

# Evita desencontro de escala (DPI) entre o screenshot e as imagens de referencia
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from interface import MacroInterface


if __name__ == "__main__":

    janela = tk.Tk()

    app = MacroInterface(janela)

    janela.mainloop()