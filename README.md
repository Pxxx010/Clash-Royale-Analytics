# 📊 Análise de Batalhas - Clash Royale

Este projeto realiza análises estatísticas de batalhas do Clash Royale utilizando MongoDB como banco de dados.

## 🚀 Funcionalidades

O sistema oferece as seguintes análises:

1. **Análise de Vitórias/Derrotas com uma Carta Específica**
   - Calcula a taxa de vitória/derrota quando uma carta específica é usada

2. **Análise de Decks com Alta Taxa de Vitória**
   - Identifica decks que tiveram mais de X% de vitórias

3. **Análise de Derrotas com Combos de Cartas**
   - Analisa quantas derrotas ocorreram com combos específicos de cartas

4. **Análise de Vitórias com Carta Específica (Menos Troféus)**
   - Identifica vitórias com uma carta específica quando o jogador tinha menos troféus que o oponente

5. **Análise de Combos de Cartas com Alta Taxa de Vitória**
   - Encontra combos de N cartas que tiveram mais de Y% de vitórias

6. **Análise de Clãs Enfrentados**
   - Estatísticas sobre os clãs enfrentados, incluindo taxa de vitória e média de troféus

7. **Análise de Performance por Horário**
   - Analisa o desempenho em diferentes horários do dia

8. **Análise de Evolução de Troféus**
   - Acompanha a evolução dos troféus ao longo do tempo

## ⚙️ Requisitos

- Python 3.x
- MongoDB
- Bibliotecas Python:
  - pymongo
  - datetime

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITÓRIO]
```

2. Instale as dependências:
```bash
pip install pymongo
```

3. Configure o arquivo `config.py` com suas credenciais do MongoDB:
```python
MONGO_URI = "sua_uri_do_mongodb"
DB_NAME = "nome_do_banco_de_dados"
```

## 🎮 Como Usar

1. Execute o script:
```bash
python import_dados.py
python main.py.py
```

2. Escolha uma opção do menu (1-8) para realizar a análise desejada

3. Siga as instruções específicas para cada análise

4. Após ver os resultados, pressione Enter para voltar ao menu

5. Escolha 0 para sair do programa

## 📊 Estrutura do Banco de Dados

O banco de dados deve conter uma coleção chamada "battles" com documentos no seguinte formato:

```json
{
    "utcTime": "data_hora",
    "is_winner": true/false,
    "team": {
        "cards": [
            {"name": "nome_da_carta"},
            ...
        ],
        "startingTrophies": [numero],
        "crowns": [numero]
    },
    "opponent": {
        "clan": ["nome_do_cla"],
        "cards": [
            {"name": "nome_da_carta"},
            ...
        ],
        "startingTrophies": [numero],
        "crowns": [numero]
    }
}
```

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 