# Análise de Dados TSW-Simplex

Este é um aplicativo web desenvolvido com Streamlit para análise de dados de logs do TSW-Simplex. O aplicativo permite visualizar e analisar dados de dispositivos, status e falhas de forma interativa.

## Requisitos

- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone este repositório:
```bash
git clone https://github.com/caiquemiranda/dash-maintenance-report
cd dash-maintenance-report
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
- No Windows:
```bash
.\venv\Scripts\activate
```
- No Linux/Mac:
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Executando o Aplicativo

1. Certifique-se de que o ambiente virtual está ativado

2. Execute o aplicativo:
```bash
streamlit run src/app.py
```

3. O aplicativo será aberto automaticamente no seu navegador padrão. Se não abrir, você pode acessar manualmente em:
```
http://localhost:8501
```

## Funcionalidades

- Upload de arquivos de log .txt
- Visualização dos dados processados em formato de tabela
- Filtros interativos por:
  - Período de datas
  - NODE
  - Tipo de dispositivo
  - Status
- Análise específica por dispositivo
- Visualizações gráficas:
  - Contagem por tipo de dispositivo
  - Contagem por status
  - Contagem por NODE
  - Top 10 falhas mais frequentes
- Download dos dados processados em formato CSV

## Estrutura do Projeto

```
dash-maintenance-report/
├── src/
│   ├── app.py              # Aplicativo principal
│   ├── utils.py            # Funções utilitárias
│   ├── parser.py           # Processamento de logs
│   ├── visualizations.py   # Funções de visualização
│   └── device_analysis.py  # Análise de dispositivos
├── requirements.txt        # Dependências do projeto
└── README.md              # Este arquivo
```

## Suporte

Para suporte ou dúvidas, por favor abra uma issue no repositório do projeto.
