#!/usr/bin/env python3
from typing import List
import subprocess
import os

def executar_scripts() -> None:
    """
    Executa os scripts do projeto na ordem correta.
    Em caso de erro em algum script, interrompe a execução.
    """
    diretorio_base = os.path.dirname(os.path.abspath(__file__))
    diretorio_news = os.path.join(diretorio_base, "..", "data", "news")
    diretorio_news_compiladas = os.path.join(diretorio_base, "..", "data", "news_compiladas")
    

    scripts = [
        ["python", "src/busca_noticias.py"],
        ["python", "src/valida_json.py", diretorio_news]
    ]
    
    for comando in scripts:
        resultado = subprocess.run(comando)
        
        if resultado.returncode != 0:
            print(f"Erro ao executar {comando[1]}. Processo interrompido.")
            break

if __name__ == '__main__':
    executar_scripts()
