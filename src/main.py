#!/usr/bin/env python3
"""
Arquivo principal que orquestra a execução das etapas do projeto.
"""

import os
from busca_noticias import etapa_coleta
from valida_json import percorrer_jsons

def main():
    DIR_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DIR_NEWS = os.path.join(DIR_BASE, "data", "news")
    FEEDS = os.path.join(DIR_BASE, "rss_feeds.json")

    print("\n====== Iniciando coleta de notícias ======")
    etapa_coleta(FEEDS, DIR_NEWS)
    print("====== Coleta concluída com sucesso ======")
    
    print("\n====== Validando notícias nos arquivos JSON ======")
    percorrer_jsons(DIR_NEWS)
    print("====== Arquivos JSON validados com sucesso ======")
    
if __name__ == '__main__':
    main()
