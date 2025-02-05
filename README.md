# YouTube Automator

Este projeto é uma ferramenta para coletar notícias de feeds RSS utilizando a biblioteca `feedparser`. O objetivo é facilitar a agregação de informações relevantes a partir de diversas fontes de notícias.

## Estrutura do Projeto

- `src/main.py`: Ponto de entrada da aplicação que inicializa o processo de coleta de notícias.
- `src/feed_parser.py`: Contém a lógica para coletar e processar os feeds RSS.
- `src/__init__.py`: Marca o diretório `src` como um pacote Python.
- `requirements.txt`: Lista as dependências do projeto.
- `README.md`: Documentação do projeto.

## Instalação

Para instalar as dependências do projeto, execute o seguinte comando:

```
pip install -r requirements.txt
```

## Uso

Para executar o projeto, utilize o seguinte comando:

```
python src/main.py
```

## Roadmap

- Implementar suporte a mais formatos de feed.
- Adicionar uma interface gráfica para visualização das notícias.
- Melhorar a lógica de agrupamento de notícias por data.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.