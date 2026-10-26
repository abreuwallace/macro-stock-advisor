"""
Orquestrador Principal do Robô de Recomendação Macroeconômica (B3).
Integra Macro -> Setores -> Fundamentalista -> Preços/Alvos -> Alocação R$ 20k -> Relatórios IA.
Execução paralela multithread para alta velocidade de varredura.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
from config.universe import UNIVERSE_B3
from config.settings import SETTINGS
from collectors.macro_collector import MacroCollector
from collectors.market_collector import MarketCollector
from collectors.fund_collector import FundamentalCollector
from engines.macro_regime import MacroRegimeEngine
from engines.stock_screener import StockScreener
from engines.price_engine import PriceEngine
from portfolio.allocator import PortfolioAllocator
from ai.report_agent import ReportAgent

logger = logging.getLogger(__name__)

class MacroStockAdvisor:
    """Motor de Recomendação Integrado para Ações Brasileiras."""

    def __init__(self, api_key: Optional[str] = None):
        self.macro_collector = MacroCollector()
        self.market_collector = MarketCollector()
        self.fund_collector = FundamentalCollector()
        self.regime_engine = MacroRegimeEngine()
        self.screener = StockScreener()
        self.price_engine = PriceEngine()
        self.allocator = PortfolioAllocator(total_capital=SETTINGS.EQUITY_CAPITAL)
        self.report_agent = ReportAgent(api_key=api_key)

    def _fetch_single_stock(self, symbol: str, meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Busca dados de mercado e fundamentos para um ativo em paralelo."""
        try:
            tech = self.market_collector.get_stock_technical_metrics(symbol)
            if not tech:
                return None
            fund = self.fund_collector.get_stock_fundamentals(symbol)
            return {
                "symbol": symbol,
                "meta": meta,
                "tech": tech,
                "fund": fund
            }
        except Exception as e:
            logger.warning(f"Erro ao processar {symbol}: {e}")
            return None

    def analyze(self, user_profile: str = "Segura / Dividendos & Qualidade", top_n: int = 5) -> Dict[str, Any]:
        """
        Executa a esteira analítica completa em tempo real:
        1. Snapshot Macro e Detecção de Regime
        2. Coleta paralela de cotações e balanços
        3. Scoring e Ranking Quantamental
        4. Cálculo de Preço-Alvo e Stop Loss
        5. Alocação da Carteira de R$ 20.000
        6. Síntese dos Relatórios de Decisão
        """
        # 1. Macro & Regime
        macro_snapshot = self.macro_collector.get_macro_snapshot()
        regime = self.regime_engine.analyze_regime(macro_snapshot, user_profile=user_profile)

        # 2. Varredura Multithread do Universo de Ações
        evaluated_stocks: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(self._fetch_single_stock, symbol, meta)
                for symbol, meta in UNIVERSE_B3.items()
            ]
            for future in as_completed(futures):
                res = future.result()
                if res is not None:
                    evaluated_stocks.append(res)

        # 3. Ranking Quantamental
        ranked_candidates = self.screener.rank_stocks(
            stocks_data=evaluated_stocks,
            sector_weights=regime["sector_weights"],
            top_n=top_n
        )

        # 4. Cálculo de Níveis de Preço (Entrada, Alvo e Stop)
        for item in ranked_candidates:
            item["price_levels"] = self.price_engine.calculate_price_levels(item)

        # 5. Dimensionamento do Capital (R$ 20.000)
        portfolio_plan = self.allocator.allocate_portfolio(ranked_candidates)

        # 6. Geração de Relatórios Explicativos
        detailed_reports = {}
        for item in ranked_candidates:
            ticker = item["meta"]["ticker"]
            rep = self.report_agent.generate_stock_report(
                stock_item=item,
                macro_snapshot=macro_snapshot,
                macro_regime=regime
            )
            detailed_reports[ticker] = rep

        return {
            "macro_snapshot": macro_snapshot,
            "macro_regime": regime,
            "ranked_stocks": ranked_candidates,
            "portfolio_plan": portfolio_plan,
            "reports": detailed_reports,
            "user_profile": user_profile,
            "capital_allocated": SETTINGS.EQUITY_CAPITAL,
            "patrimony_total": SETTINGS.TOTAL_PATRIMONY,
        }

if __name__ == "__main__":
    import time
    t0 = time.time()
    advisor = MacroStockAdvisor()
    res = advisor.analyze()
    print(f"Análise concluída em {time.time() - t0:.2f} segundos!")
    print("Regime:", res["macro_regime"]["regime_name"])
    print("Top Selecionadas:", [s["meta"]["ticker"] for s in res["ranked_stocks"]])
    print("Total Alocado em R$:", res["portfolio_plan"]["total_allocated"])

