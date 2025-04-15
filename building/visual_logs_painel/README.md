# Analisador de TroubleLog

Este aplicativo Streamlit permite analisar arquivos de log do sistema de alarme (TroubleLog.txt), processando-os e exibindo os dados em formato tabular.

## Funcionalidades

- Upload de arquivos TroubleLog.txt
- Processamento automático usando expressões regulares
- Exibição dos dados em formato tabular
- Filtragem por local e status
- Estatísticas de ocorrências por local e status
- Download dos dados processados em formato CSV

## Como executar

1. Certifique-se de ter as dependências instaladas:
```
pip install streamlit pandas
```

2. Execute o aplicativo:
```
cd building/visual_logs_painel
streamlit run src/app.py
```

3. Acesse o aplicativo pelo navegador no endereço indicado (geralmente http://localhost:8501)

## Como usar

1. Clique no botão "Browse files" para selecionar o arquivo TroubleLog.txt
2. O aplicativo processará automaticamente o arquivo
3. Use os filtros para examinar dados específicos
4. Visualize as estatísticas para identificar padrões de problemas
5. Baixe os dados processados se necessário

## Estrutura do projeto

```
visual_logs_painel/
├── data/           # Pasta contendo exemplos de arquivos TroubleLog.txt
├── src/            # Código-fonte do aplicativo
│   └── app.py      # Aplicativo principal
└── README.md       # Este arquivo
``` 