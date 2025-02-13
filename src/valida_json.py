#!/usr/bin/env python3
"""
Script para validar e corrigir a estrutura dos arquivos JSON de notícias.
Percorre os arquivos no diretório de notícias, valida sua estrutura e tenta 
corrigir problemas simples. Se não conseguir corrigir, registra o erro em 
data/logs/jsons_bugs.log.
"""

import os
import json
import re
import uuid
from datetime import datetime
import sys
from tqdm import tqdm
from colorama import init, Fore, Style

# Inicializa o colorama
init()

CHAVES_OBRIGATORIAS = ['id', 'titulo', 'conteudo', 'fonte', 'data', 'url']

DIR_NEWS = os.path.join("data", "news")
DIR_LOGS = os.path.join("data", "logs")
LOG_FILE = os.path.join(DIR_LOGS, "jsons_bugs.log")

def registrar_erro(mensagem: str) -> None:
    """
    Registra mensagem de erro exibindo-o em vermelho.
    
    Args:
        mensagem: Texto do erro ocorrido.
    """
    print(f"{Fore.RED}[ERRO] {mensagem}{Style.RESET_ALL}")

def corrigir_json(conteudo: str) -> str:
    """
    Tenta corrigir JSON mal formatado.
    
    Args:
        conteudo: String JSON com possíveis erros.
        
    Returns:
        JSON corrigido.
    """
    return re.sub(r",\s*([}\]])", r"\1", conteudo)

def validar_dados(dados: list, arquivo: str) -> list:
    """
    Valida e corrige a estrutura dos dados.
    
    Args:
        dados: Lista de dicionários para validar.
        arquivo: Nome do arquivo sendo processado.
        
    Returns:
        Lista de dados validados e corrigidos.
    """
    if not isinstance(dados, list):
        raise ValueError("Dados devem ser uma lista")

    dados_validados = []
    for i, item in enumerate(dados):
        if not isinstance(item, dict):
            registrar_erro(f"Item {i} inválido em {arquivo}")
            continue

        item_validado = validar_item(item, i, arquivo)
        dados_validados.append(item_validado)
    return dados_validados

def validar_item(item: dict, posicao: int, arquivo: str) -> dict:
    """
    Valida e corrige um item individual.
    
    Args:
        item: Dicionário a ser validado.
        posicao: Índice do item na lista.
        arquivo: Nome do arquivo.
        
    Returns:
        Item validado e corrigido.
    """
    for chave in CHAVES_OBRIGATORIAS:
        if chave not in item:
            if chave == "id":
                item[chave] = str(uuid.uuid4())
            else:
                item[chave] = ""
            registrar_erro(f"Chave '{chave}' ausente no item {posicao} de {arquivo}")
    return item

def processar_arquivo(caminho: str) -> None:
    """
    Processa um arquivo JSON completo.
    
    Args:
        caminho: Caminho do arquivo a ser processado.
    """
    with open(caminho, "r", encoding="utf-8") as arquivo:
        conteudo = arquivo.read()

    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError:
        conteudo = corrigir_json(conteudo)
        dados = json.loads(conteudo)

    dados_validados = validar_dados(dados, caminho)

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados_validados, arquivo, indent=2, ensure_ascii=False)

def percorrer_jsons(diretorio: str) -> None:
    """
    Percorre todos os arquivos JSON no diretório especificado com barra de progresso.
    
    Args:
        diretorio: Caminho do diretório contendo os arquivos JSON.
    """
    if not os.path.exists(diretorio):
        print(f"{Fore.RED}Diretório '{diretorio}' não encontrado.{Style.RESET_ALL}")
        return

    arquivos = [
        os.path.join(diretorio, f)
        for f in os.listdir(diretorio)
        if f.lower().endswith('.json')
    ]

    with tqdm(arquivos, desc="Validando JSON", unit="arquivo", 
              colour='green', bar_format="{l_bar}{bar:30}{r_bar}{bar:-30b}") as barra:
        for arquivo in barra:
            processar_arquivo(arquivo)

def main():
    """
    Função principal que processa o diretório informado via argumento.
    """
    if len(sys.argv) < 2:
        print(f"{Fore.RED}[ERRO] É necessário informar o diretório dos arquivos JSON{Style.RESET_ALL}")
        sys.exit(1)

    diretorio = sys.argv[1]

    if not os.path.exists(diretorio):
        print(f"{Fore.RED}[ERRO] Diretório não encontrado: {diretorio}{Style.RESET_ALL}")
        sys.exit(1)

    print("\n====== Iniciando validação dos JSON ======")
    percorrer_jsons(diretorio)
    print("====== Validação concluída com sucesso ======")

if __name__ == "__main__":
    main()