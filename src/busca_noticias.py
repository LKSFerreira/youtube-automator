#!/usr/bin/env python3
"""
Módulo responsável por coletar e salvar as notícias dos feeds RSS,
realizando diversas validações e tratamento do conteúdo para remover
tags HTML que possam comprometer a consistência do JSON.
"""

from datetime import datetime
import json
import os
import uuid
import feedparser
from bs4 import BeautifulSoup
from tqdm import tqdm
from colorama import init, Fore

# Inicializa o colorama
init()


def limpar_texto(texto: str) -> str:
    """
    Remove tags HTML e converte para texto simples.

    Args:
        texto: Texto original que pode conter tags HTML

    Returns:
        Texto limpo sem formatações
    """
    if not texto:
        return ""
    if not texto.lstrip().startswith("<"):
        # Se o texto não iniciar com '<', podemos supor que não é markup
        return texto
    return BeautifulSoup(texto, "html.parser").get_text(separator=" ", strip=True)


def processar_conteudo(texto: str) -> tuple:
    """
    Extrai a URL da primeira imagem (campo imagem) e retorna o conteúdo limpo
    sem quaisquer tags HTML.

    Args:
        texto: Conteúdo original com tags HTML.

    Returns:
        tuple: (imagem, conteudo_limpo)
    """
    soup = BeautifulSoup(texto, 'html.parser')
    img_tag = soup.find('img')
    imagem = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ''
    conteudo_limpo = soup.get_text(separator=' ', strip=True)
    return imagem, conteudo_limpo


def carregar_feeds(caminho_arquivo: str) -> list:
    """
    Carrega a lista de feeds do arquivo JSON.

    Args:
        caminho_arquivo: Caminho para o arquivo JSON com os feeds

    Returns:
        Lista de feeds carregados

    Raises:
        ValueError: Se o arquivo estiver inválido
    """
    with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        feeds = json.load(arquivo)

    if not isinstance(feeds, list) or not feeds:
        raise ValueError("Arquivo de feeds inválido ou vazio")

    return feeds


def coletar_noticias(feed: dict) -> list:
    """
    Coleta notícias de um feed RSS.

    Args:
        feed: Dicionário com dados do feed (fonte e url)

    Returns:
        Lista de notícias coletadas
    """
    noticias = []
    fonte = feed.get('fonte', 'Desconhecida')
    url = feed.get('url', '').strip()

    if not url:
        print(f"URL vazia para feed: {fonte}")
        return noticias

    try:
        feed_dados = feedparser.parse(url)

        for item in feed_dados.entries:
            noticia = criar_noticia(item, fonte)
            noticias.append(noticia)

    except Exception as erro:
        print(f"Erro ao processar feed {fonte}: {erro}")

    return noticias


def criar_noticia(item: dict, fonte: str) -> dict:
    """
    Cria objeto de notícia a partir de item do feed.

    Args:
        item: Item do feed RSS
        fonte: Nome da fonte da notícia

    Returns:
        Dicionário com dados da notícia, incluindo imagem extraída e conteúdo limpo.
    """
    data = obter_data_publicacao(item)
    # Extrai a imagem e limpa o conteúdo do HTML
    imagem, conteudo = processar_conteudo(
        item.get('summary', item.get('description', '')))

    return {
        "id": str(uuid.uuid4()),
        "titulo": limpar_texto(item.get('title', 'Sem título')),
        "conteudo": conteudo,
        "imagem": imagem,
        "fonte": fonte,
        "data": data,
        "url": item.get('link', '')
    }


def obter_data_publicacao(item: dict) -> str:
    """
    Extrai data de publicação do item.

    Args:
        item: Item do feed RSS

    Returns:
        Data formatada como string YYYY-MM-DD
    """
    if item.get('published_parsed'):
        return datetime(*item.published_parsed[:6]).strftime('%Y-%m-%d')
    elif item.get('updated_parsed'):
        return datetime(*item.updated_parsed[:6]).strftime('%Y-%m-%d')
    return datetime.now().strftime('%Y-%m-%d')


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
                    print(
                        f"[ERRO] Conteúdo inválido no arquivo {nome_arquivo}. Substituindo pelo novo conteúdo.")
                    noticias_existentes = []
            except Exception as erro:
                print(
                    f"[ERRO] Falha ao ler o arquivo existente {nome_arquivo}: {erro}")
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
                json.dump(noticias_combinadas, arquivo,
                          ensure_ascii=False, indent=4)
        except Exception as erro_salvar:
            print(
                f"[ERRO] Problema ao salvar notícias para a data {data}: {erro_salvar}")


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
            print(
                f"[AVISO] Nenhuma notícia coletada para o feed: {feed_info.get('fonte', 'Fonte desconhecida')}")

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
