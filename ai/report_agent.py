"""
Agente Gerador de Relatórios Executivos de Recomendação com IA (Gemini).
Produz justificativas fundamentadas, teses de investimento, catalisadores e riscos
com instruções passo a passo para execução no Itaú.
"""
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ReportAgent:
    """Gera relatórios de recomendação de investimento com fundamentação Top-Down."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Não foi possível inicializar o cliente Gemini: {e}")

    def generate_stock_report(
        self,
        stock_item: Dict[str, Any],
        macro_snapshot: Dict[str, Any],
        macro_regime: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Gera um relatório executivo completo para a ação recomendada:
        Tese de Compra, Catalisadores, Riscos e Instruções de Execução no Itaú.
        """
        meta = stock_item["meta"]
        tech = stock_item["tech"]
        fund = stock_item["fund"]
        prices = stock_item["price_levels"]
        score = stock_item.get("score", 75)
        conf = stock_item.get("confidence_pct", 85)

        ticker = meta["ticker"]
        name = meta["name"]
        sector = meta["sector"]
        current_p = prices["current_price"]
        entry_min = prices["entry_min"]
        entry_max = prices["entry_max"]
        target_p = prices["target_price"]
        upside = prices["potential_gain_pct"]
        stop_p = prices["stop_loss_price"]
        loss_pct = prices["max_loss_pct"]
        dy = fund.get("dividend_yield", 0.0)
        roe = fund.get("roe", "N/D")
        pe = fund.get("pe_ratio", "N/D")
        selic = macro_snapshot.get("selic_rate", 10.5)

        # Se houver Gemini API Key disponível, enriquece via LLM
        if self.client:
            try:
                prompt = f"""
                Você é um estrategista-chefe de investimentos especializado em Ações Brasileiras (B3) e análise macroeconômica Top-Down.
                O investidor possui R$ 20.000,00 para alocar em ações com foco em MÁXIMA SEGURANÇA E DIVIDENDOS (preservação de capital).
                
                Dados do Ativo:
                - Empresa: {name} ({ticker})
                - Setor: {sector}
                - Preço Atual: R$ {current_p:.2f}
                - Faixa de Entrada Ideal: R$ {entry_min:.2f} até R$ {entry_max:.2f}
                - Preço-Alvo: R$ {target_p:.2f} (+{upside}%)
                - Stop Loss de Proteção: R$ {stop_p:.2f} ({loss_pct}%)
                - Dividend Yield Projetado: {dy}% a.a.
                - P/L: {pe}x | ROE: {roe}%
                - Cenário Macro: Selic a {selic}%, Regime: {macro_regime.get('regime_name')}.
                
                Escreva um relatório executivo objetivo em português do Brasil com:
                1. Tese de Investimento (Por que comprar no cenário macro atual?)
                2. Catalisadores de Alta (O que fará a ação valorizar?)
                3. Principais Riscos e Pontos de Atenção (O que pode dar errado?)
                4. Instrução Clara de Operação no App do Itaú / Íon
                Seja direto, profissional, sem enrolação. Formate em Markdown claro.
                """
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                if response and response.text:
                    return {
                        "source": "Gemini AI",
                        "content": response.text.strip()
                    }
            except Exception as e:
                logger.warning(f"Erro ao consultar Gemini, usando gerador analítico nativo: {e}")

        # Gerador Analítico Nativo (Institucional e Estruturado)
        content = self._build_deterministic_report(
            ticker=ticker,
            name=name,
            sector=sector,
            current_p=current_p,
            entry_min=entry_min,
            entry_max=entry_max,
            target_p=target_p,
            upside=upside,
            stop_p=stop_p,
            loss_pct=loss_pct,
            dy=dy,
            roe=roe,
            pe=pe,
            selic=selic,
            regime_name=macro_regime.get("regime_name", "Defensivo"),
            conf=conf
        )

        return {
            "source": "Motor Quantamental Nativo",
            "content": content
        }

    def _build_deterministic_report(
        self, ticker, name, sector, current_p, entry_min, entry_max,
        target_p, upside, stop_p, loss_pct, dy, roe, pe, selic, regime_name, conf
    ) -> str:
        """Gera um relatório profissional completo e estruturado de alta fidelidade."""
        return f"""
### 📊 Tese de Investimento: {name} ({ticker})
**Nível de Confiança do Modelo:** {conf}% | **Perfil:** Seguro & Defensivo | **Setor:** {sector}

#### 1. Racional Macroeconômico e Setorial
- **Ambiente de Juros e Inflação:** Com a Selic em **{selic}% ao ano**, o cenário favorece fortemente empresas com geração de caixa consistente, baixo endividamento e modelos de negócios resilientes.
- **Proteção do Setor {sector}:** O setor de atuação de {name} possui demanda essencial e histórica capacidade de repasse inflacionário, mitigando oscilações bruscas do PIB.
- **Retorno ao Acionista:** O Dividend Yield projetado de **{dy}%** oferece uma remuneração expressiva em proventos isentos de IR, superando a volatilidade do mercado.

#### 2. Indicadores Fundamentalistas
- **Valuation (P/L):** Negociando a **{pe}x lucros**, o papel apresenta margem de segurança contra correções severas.
- **Rentabilidade (ROE):** Retorno sobre patrimônio de **{roe}%**, comprovando excelente eficiência e liderança no segmento.

#### 3. Gatilhos Operacionais para Execução no Itaú
- **Preço Atual na B3:** R$ {current_p:.2f}
- **Faixa de Entrada Recomendada:** **R$ {entry_min:.2f} a R$ {entry_max:.2f}** (Não pagar acima de R$ {entry_max:.2f} para evitar compras no topo de curto prazo).
- **Preço-Alvo (Realização de Lucro):** **R$ {target_p:.2f}** (Potencial de ganho estimado de **+{upside}%**).
- **Preço de Saída / Stop Loss de Proteção:** **R$ {stop_p:.2f}** (Risco estritamente controlado em **{loss_pct}%**).

#### 4. Principais Riscos e Monitoramento
- Eventuais revisões regulatórias setoriais ou mudanças na política de distribuição de proventos da administração.
- Mudanças inesperadas na trajetória da política monetária do Banco Central.

#### 5. Como Operar no App do Itaú / Itaú Íon
1. Abra o app **Itaú** ou **Íon Itaú** e vá na aba **Investir > Renda Variável**.
2. Digite o ticker **{ticker}** (ou **{ticker}F** se for fração menor que 100 ações).
3. Insira o preço limite dentro da faixa de **R$ {entry_min:.2f} a R$ {entry_max:.2f}**.
4. Configure a ordem de venda com objetivo em **R$ {target_p:.2f}** e mantenha o alarme de proteção no stop em **R$ {stop_p:.2f}**.
"""

