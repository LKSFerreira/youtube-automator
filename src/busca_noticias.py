#!/usr/bin/env python3
"""
Módulo responsável por coletar e salvar as notícias dos feeds RSS,
realizando diversas validações e tratamento do conteúdo para remover
tags HTML que possam comprometer a consistência do JSON.
"""

import feedparser
import json
import os
import uuid
from datetime import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm
from colorama import init, Fore

# Inicializa o colorama
init()

def limpar_texto(texto: str) -> str:
    """
    Remove todas as tags HTML e converte entidades para texto simples.
    
    Parâmetros:
        texto (str): Texto contendo possíveis tags HTML.
    
    Retorna:
        str: Texto limpo, sem tags.
    """
    if not texto:
        return ""
    # O separator garante que haja espaçamento entre textos removidos das tags
    return BeautifulSoup(texto, "html.parser").get_text(separator=" ", strip=True)

def carregar_feeds(caminho_arquivo: str) -> list:
    """
    Carrega a lista de feeds a partir de um arquivo JSON.
    
    Parâmetros:
        caminho_arquivo (str): Caminho para o arquivo JSON contendo os feeds.
    
    Retorna:
        list: Lista de dicionários com as informações de cada feed.
    
    Lança:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se o arquivo estiver vazio ou não contiver uma lista válida.
    """
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo de feeds não encontrado: {caminho_arquivo}")

    if os.path.getsize(caminho_arquivo) == 0:
        raise ValueError(f"O arquivo de feeds está vazio: {caminho_arquivo}")

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            feeds = json.load(arquivo)
    except json.JSONDecodeError as erro:
        raise ValueError(f"Erro na leitura do arquivo de feeds (JSON inválido): {erro}")

    if not isinstance(feeds, list) or len(feeds) == 0:
        raise ValueError("O arquivo de feeds não contém uma lista válida de feeds.")
    
    return feeds

def coletar_noticias(feed_info: dict) -> list:
    """
    Coleta as notícias de um feed RSS utilizando o feedparser.
    
    Parâmetros:
        feed_info (dict): Dicionário contendo informações do feed (ex.: fonte e url).
    
    Retorna:
        list: Lista de notícias extraídas do feed.
    """
    noticias = []
    fonte = feed_info.get('fonte', 'Fonte desconhecida')
    url_feed = feed_info.get('url', '').strip()

    if not url_feed:
        print(f"[ERRO] A URL para o feed '{fonte}' está vazia ou não foi definida.")
        return noticias

    print(f"Processando feed: {fonte} - {url_feed}")

    # Tenta processar o feed; se ocorrer erro, informa e passa para o próximo
    try:
        feed = feedparser.parse(url_feed)
    except Exception as erro:
        print(f"[ERRO] Não foi possível processar o feed '{fonte}' ({url_feed}): {erro}")
        return noticias

    # Se feed.bozo estiver ativo, indica que houve um problema na interpretação do feed
    if getattr(feed, "bozo", False):
        print(f"[ERRO] Feed com formato inválido ou URL incorreta para '{fonte}': {url_feed}")
        return noticias

    # Itera sobre cada item/notícia do feed
    for item in feed.entries:
        try:
            titulo = item.get('title', 'Sem título')
            # Caso o conteúdo venha com tags HTML, remove-as
            conteudo_bruto = item.get('summary', item.get('description', 'Sem conteúdo'))
            conteudo = limpar_texto(conteudo_bruto)
            url = item.get('link', '')

            # Extrai data de publicação: tenta usar published_parsed ou updated_parsed
            if 'published_parsed' in item and item.published_parsed:
                data_publicacao = datetime(*item.published_parsed[:6]).strftime('%Y-%m-%d')
            elif 'updated_parsed' in item and item.updated_parsed:
                data_publicacao = datetime(*item.updated_parsed[:6]).strftime('%Y-%m-%d')
            else:
                # Se não houver data, utiliza a data atual
                data_publicacao = datetime.now().strftime('%Y-%m-%d')
            
            noticia = {
                "id": str(uuid.uuid4()),
                "titulo": limpar_texto(titulo),
                "conteudo": conteudo,
                "fonte": fonte,
                "data": data_publicacao,
                "url": url
            }
            noticias.append(noticia)
        except Exception as erro_item:
            print(f"[ERRO] Problema ao processar um item do feed '{fonte}': {erro_item}")
    
    return noticias

def agrupar_noticias_por_data(noticias: list) -> dict:
    """
    Agrupa as notícias por data de publicação.
    
    Parâmetros:
        noticias (list): Lista de notícias.
    
    Retorna:
        dict: Dicionário onde a chave é a data (YYYY-MM-DD) e o valor é uma lista de notícias.
    """
    agrupadas = {}
    for noticia in noticias:
        data = noticia.get("data")
        if data not in agrupadas:
            agrupadas[data] = []
        agrupadas[data].append(noticia)
    return agrupadas

def salvar_noticias(agrupadas: dict, diretorio_saida: str) -> None:
    """
    Salva as notícias agrupadas por data em arquivos JSON separados.
    Se o arquivo para determinada data já existir, realiza um append dos novos
    itens à lista existente, garantindo que não haja duplicatas (mesmo título, fonte e data).
    
    Parâmetros:
        agrupadas (dict): Dicionário com notícias agrupadas por data.
        diretorio_saida (str): Caminho do diretório onde os arquivos serão salvos.
    """
    os.makedirs(diretorio_saida, exist_ok=True)
    
    for data, noticias in tqdm(agrupadas.items(), desc="Salvando notícias", unit="data", colour='green', bar_format="{l_bar}{bar:30}{r_bar}{bar:-30b}"):
        nome_arquivo = os.path.join(diretorio_saida, f"{data}.json")
        # Se o arquivo existir, carrega o conteúdo existente e realiza o append
        if os.path.exists(nome_arquivo):
            try:
                with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
                    noticias_existentes = json.load(arquivo)
                # Verifica se as notícias existentes são uma lista
                if not isinstance(noticias_existentes, list):
                    print(f"[ERRO] Conteúdo inválido no arquivo {nome_arquivo}. Substituindo pelo novo conteúdo.")
                    noticias_existentes = []
            except Exception as erro:
                print(f"[ERRO] Falha ao ler o arquivo existente {nome_arquivo}: {erro}")
                noticias_existentes = []
        else:
            noticias_existentes = []

        # Cria um conjunto de chaves únicas das notícias existentes
        existentes_keys = set()
        for n in noticias_existentes:
            titulo = n.get('titulo', '').strip().lower()
            fonte = n.get('fonte', '').strip()
            data_noticia = n.get('data', '')
            existentes_keys.add((titulo, fonte, data_noticia))

        # Processar as novas notícias para remover duplicatas
        novas_sem_duplicatas = []
        novas_keys = set()
        for noticia in noticias:
            titulo = noticia.get('titulo', '').strip().lower()
            fonte = noticia.get('fonte', '').strip()
            data_noticia = noticia.get('data', '')
            key = (titulo, fonte, data_noticia)
            
            if key not in existentes_keys and key not in novas_keys:
                novas_sem_duplicatas.append(noticia)
                novas_keys.add(key)

        # Combina as notícias existentes com as novas sem duplicatas
        noticias_combinadas = noticias_existentes + novas_sem_duplicatas

        try:
            with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
                json.dump(noticias_combinadas, arquivo, ensure_ascii=False, indent=4)
        except Exception as erro_salvar:
            print(f"[ERRO] Problema ao salvar notícias para a data {data}: {erro_salvar}")

def etapa_coleta(caminho_feeds: str, diretorio_saida: str) -> None:
    """
    Realiza a etapa completa de coleta, agrupamento e salvamento das notícias.
    
    Parâmetros:
        caminho_feeds (str): Caminho para o arquivo JSON de feeds.
        diretorio_saida (str): Diretório onde os JSONs serão salvos.
    """
    try:
        feeds = carregar_feeds(caminho_feeds)
    except Exception as erro:
        print(f"[ERRO] {erro}")
        return

    todas_noticias = []
    for feed_info in feeds:
        noticias_feed = coletar_noticias(feed_info)
        if noticias_feed:
            todas_noticias.extend(noticias_feed)
        else:
            print(f"[AVISO] Nenhuma notícia coletada para o feed: {feed_info.get('fonte', 'Fonte desconhecida')}")
    
    if not todas_noticias:
        print("[ERRO] Nenhuma notícia foi coletada de nenhum feed.")
        return

    noticias_agrupadas = agrupar_noticias_por_data(todas_noticias)
    salvar_noticias(noticias_agrupadas, diretorio_saida)

def main():
    DIR_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DIR_NEWS = os.path.join(DIR_BASE, "data", "news")
    FEEDS = os.path.join(DIR_BASE, "rss_feeds.json")
    
    print("\n====== Iniciando coleta de notícias ======")
    etapa_coleta(FEEDS, DIR_NEWS)
    print("====== Coleta concluída com sucesso ======")

if __name__ == "__main__":
    main()