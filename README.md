# 📈 Robô de Recomendação Macroeconômica B3 (Itaú Advisory)

Sistema inteligente e automatizado de apoio à decisão de investimentos em Renda Variável (B3), baseado em análise Top-Down (Macroeconomia -> Setores -> Fundamentalista -> Níveis de Entrada/Alvo/Stop).

## 🚀 Funcionalidades
- **Monitoramento Macroeconômico ao Vivo:** Taxa Selic, IPCA 12m e projeções oficiais do Banco Central (BACEN SGS), cotação do Dólar, Petróleo Brent e Ibovespa.
- **Detecção de Ciclos Econômicos:** Identifica o regime atual e prioriza setores favorecidos (foco em *Segurança, Dividendos e Preservação de Capital*).
- **Filtro Quantamental B3:** Varredura em tempo real de liquidez, valuation (P/L, P/VP), ROE e Dividend Yield.
- **Parâmetros Operacionais Precisos:** Faixa de compra ideal, Preço-Alvo (Take Profit) e Stop Loss inteligente baseado em ATR.
- **Dimensionamento da Carteira de R$ 20.000:** Quantidades exatas em lotes padrão e fracionário para execução fácil no Itaú / Íon.
- **Aba de Projeções e Juros Compostos:** Simulação de 1 a 10 anos com reinvestimento de proventos (efeito bola de neve) e teste de estresse patrimonial.
- **Relatórios Executivos:** Teses explicativas com nível de confiança para cada ação.

## 🛠️ Tecnologias
- [Python 3.11+](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [Plotly](https://plotly.com/)
- [yfinance](https://github.com/ranaroussi/yfinance)
- [Banco Central do Brasil (BACEN SGS API)](https://dadosabertos.bcb.gov.br/)

## 💻 Execução Local
```bash
# Criar ambiente e instalar dependências
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Iniciar o dashboard
./run_dashboard.sh
```
