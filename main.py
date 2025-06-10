import tkinter as tk
import sys
import os
from pathlib import Path

# Adicionar pasta atual ao path para importações
if hasattr(sys, '_MEIPASS'):
    # Executando como executável
    base_path = sys._MEIPASS
else:
    # Executando como script
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

from gui import FinanceApp

def main():
    """Função principal do programa"""
    # Configurar diretório de trabalho
    if hasattr(sys, '_MEIPASS'):
        # Executável PyInstaller - diretório onde está o .exe
        work_dir = os.path.dirname(sys.executable)
    else:
        # Script Python - diretório do script
        work_dir = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(work_dir)
    
    try:
        root = tk.Tk()
        app = FinanceApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Erro ao iniciar aplicação: {e}")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()
