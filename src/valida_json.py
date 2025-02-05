#!/usr/bin/env python3
"""
Script para validar e corrigir a estrutura dos arquivos JSON de notícias.
Percorre os arquivos no diretório de notícias, valida sua estrutura e tenta 
corrigir problemas simples. Se não conseguir corrigir, registra o erro em 
data/logs/jsons_bugs.log.
"""

import os
import re
import json
import uuid
from datetime import datetime
from tqdm import tqdm
from colorama import init, Fore

# Inicializa o colorama
init()

# Lista de chaves obrigatórias para cada objeto JSON
CHAVES_OBRIGATORIAS = ["id", "titulo", "conteudo", "fonte", "data", "url"]

# Caminhos dos diretórios
DIR_NEWS = os.path.join("data", "news")
DIR_LOGS = os.path.join("data", "logs")
LOG_FILE = os.path.join(DIR_LOGS, "jsons_bugs.log")

def log_erro(mensagem: str) -> None:
    """Registra a mensagem de erro no arquivo de log."""
    os.makedirs(DIR_LOGS, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] {mensagem}\n")

def tentar_corrigir_json(conteudo: str) -> str:
    """
    Tenta corrigir erros simples no conteúdo JSON, como vírgulas extras antes de
    '}' ou ']'.
    
    Parâmetros:
        conteudo (str): Conteúdo original do arquivo.
        
    Retorna:
        str: Conteúdo possivelmente corrigido.
    """
    conteudo_corrigido = re.sub(r",\s*([}\]])", r"\1", conteudo)
    return conteudo_corrigido

def validar_estrutura_dados(dados: any, arquivo: str) -> list:
    """
    Valida a estrutura dos dados carregados do JSON.
    Se os dados não forem uma lista ou se algum objeto estiver com chaves faltando,
    tenta corrigir adicionando valores padrão.
    """
    if not isinstance(dados, list):
        raise ValueError("O JSON não contém uma lista de objetos.")

    dados_corrigidos = []
    for i, item in enumerate(dados):
        if not isinstance(item, dict):
            log_erro(f"Arquivo '{arquivo}': Item na posição {i} não é um objeto. Ignorado.")
            continue

        for chave in CHAVES_OBRIGATORIAS:
            if chave not in item:
                if chave == "id":
                    item[chave] = str(uuid.uuid4())
                    log_erro(f"Arquivo '{arquivo}': Item na posição {i} estava sem '{chave}'. Novo UUID gerado.")
                else:
                    item[chave] = ""
                    log_erro(f"Arquivo '{arquivo}': Item na posição {i} estava sem '{chave}'. Valor padrão atribuído.")
        dados_corrigidos.append(item)
    return dados_corrigidos

def processar_arquivo(arquivo_json: str) -> None:
    """
    Processa um arquivo JSON: tenta carregar, corrigir e validar sua estrutura.
    """
    try:
        with open(arquivo_json, "r", encoding="utf-8") as f:
            conteudo = f.read()
        
        try:
            dados = json.loads(conteudo)
        except json.JSONDecodeError as e:
            log_erro(f"Arquivo '{arquivo_json}': Erro de JSONDecodeError: {e}. Tentando corrigir...")
            conteudo_corrigido = tentar_corrigir_json(conteudo)
            try:
                dados = json.loads(conteudo_corrigido)
                log_erro(f"Arquivo '{arquivo_json}': Correção simples aplicada com sucesso.")
            except json.JSONDecodeError as e2:
                raise ValueError(f"Não foi possível corrigir o JSON: {e2}")
        
        dados_validados = validar_estrutura_dados(dados, arquivo_json)
        
        with open(arquivo_json, "w", encoding="utf-8") as f:
            json.dump(dados_validados, f, ensure_ascii=False, indent=4)

    except Exception as erro:
        log_erro(f"Arquivo '{arquivo_json}': Falha na validação/correção: {erro}")

def percorrer_jsons(diretorio: str) -> None:
    """
    Percorre todos os arquivos JSON no diretório especificado com barra de progresso.
    """
    if not os.path.exists(diretorio):
        print(f"Diretório '{diretorio}' não encontrado.")
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
    DIR_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DIR_NEWS = os.path.join(DIR_BASE, "data", "news")

    print("\n====== Validando notícias nos arquivos JSON ======")
    percorrer_jsons(DIR_NEWS)
    print("====== Arquivos JSON validados com sucesso ======")

if __name__ == "__main__":
    main()