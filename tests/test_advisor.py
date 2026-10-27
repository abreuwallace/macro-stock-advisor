"""
Testes Automatizados para o Robô de Recomendação Macro (B3).
"""
import unittest
from config.settings import SETTINGS
from collectors.macro_collector import MacroCollector
from collectors.market_collector import MarketCollector
from collectors.fund_collector import FundamentalCollector
from engines.macro_regime import MacroRegimeEngine
from engines.stock_screener import StockScreener
from engines.price_engine import PriceEngine
from portfolio.allocator import PortfolioAllocator
from ai.report_agent import ReportAgent
from engines.projections import ProjectionEngine
from engines.monte_carlo import MonteCarloEngine
from engines.robustness_diagnostic import RobustnessDiagnostic
from engines.opportunity_engine import OpportunityEngine

class TestMacroAdvisor(unittest.TestCase):

    def test_settings_integrity(self):
        self.assertEqual(SETTINGS.EQUITY_CAPITAL, 20_000.00)
        self.assertEqual(SETTINGS.TOTAL_PATRIMONY, 100_000.00)
        self.assertGreaterEqual(SETTINGS.MIN_ASSETS, 4)
        self.assertLessEqual(SETTINGS.MAX_ASSETS, 6)

    def test_macro_regime_classification(self):
        engine = MacroRegimeEngine()
        # Simula juros altos
        snapshot_high = {"selic_rate": 13.75, "ipca_12m": 4.5, "real_rate": 9.25, "usd_brl": 5.4, "brent_usd": 78.0}
        regime = engine.analyze_regime(snapshot_high, user_profile="Segura / Dividendos")
        self.assertIn("Juros", regime["regime_name"])
        self.assertGreater(regime["sector_weights"]["Utilities"], 1.3)
        self.assertGreater(regime["sector_weights"]["Financeiro"], 1.2)

    def test_price_engine_bounds(self):
        engine = PriceEngine()
        mock_stock = {
            "tech": {
                "current_price": 30.00,
                "support_price": 28.50,
                "resistance_price": 33.00,
                "atr_14": 0.80
            },
            "fund": {
                "analyst_target_price": 36.00
            }
        }
        prices = engine.calculate_price_levels(mock_stock)
        self.assertGreater(prices["target_price"], prices["current_price"])
        self.assertLess(prices["stop_loss_price"], prices["current_price"])
        self.assertGreaterEqual(prices["potential_gain_pct"], 10.0)
        self.assertLessEqual(abs(prices["max_loss_pct"]), 8.0)
        self.assertGreaterEqual(prices["risk_reward_ratio"], 1.5)

    def test_portfolio_allocation_cap(self):
        allocator = PortfolioAllocator(total_capital=20_000.00)
        mock_top_stocks = [
            {
                "score": 85.0,
                "confidence_pct": 88,
                "meta": {"ticker": "BBAS3", "name": "Banco do Brasil", "sector": "Financeiro"},
                "price_levels": {
                    "current_price": 25.00,
                    "target_price": 30.00,
                    "potential_gain_pct": 20.0,
                    "stop_loss_price": 23.50,
                    "max_loss_pct": -6.0,
                    "entry_action": "Comprar a R$ 25.00"
                },
                "fund": {"dividend_yield": 9.0, "pe_ratio": 4.5, "roe": 21.0}
            },
            {
                "score": 82.0,
                "confidence_pct": 85,
                "meta": {"ticker": "EGIE3", "name": "Engie Brasil", "sector": "Utilities"},
                "price_levels": {
                    "current_price": 40.00,
                    "target_price": 48.00,
                    "potential_gain_pct": 20.0,
                    "stop_loss_price": 37.50,
                    "max_loss_pct": -6.2,
                    "entry_action": "Comprar a R$ 40.00"
                },
                "fund": {"dividend_yield": 7.5, "pe_ratio": 8.0, "roe": 25.0}
            },
            {
                "score": 80.0,
                "confidence_pct": 82,
                "meta": {"ticker": "CXSE3", "name": "Caixa Seguridade", "sector": "Financeiro"},
                "price_levels": {
                    "current_price": 15.00,
                    "target_price": 18.00,
                    "potential_gain_pct": 20.0,
                    "stop_loss_price": 14.10,
                    "max_loss_pct": -6.0,
                    "entry_action": "Comprar a R$ 15.00"
                },
                "fund": {"dividend_yield": 8.5, "pe_ratio": 8.5, "roe": 40.0}
            },
            {
                "score": 78.0,
                "confidence_pct": 80,
                "meta": {"ticker": "TAEE11", "name": "Taesa", "sector": "Utilities"},
                "price_levels": {
                    "current_price": 35.00,
                    "target_price": 42.00,
                    "potential_gain_pct": 20.0,
                    "stop_loss_price": 32.80,
                    "max_loss_pct": -6.3,
                    "entry_action": "Comprar a R$ 35.00"
                },
                "fund": {"dividend_yield": 9.2, "pe_ratio": 7.5, "roe": 19.0}
            }
        ]

        res = allocator.allocate_portfolio(mock_top_stocks)
        self.assertLessEqual(res["total_allocated"], 20_000.00)
        self.assertGreaterEqual(res["total_allocated"], 19_500.00)
        self.assertGreaterEqual(res["cash_remaining"], 0.0)
        self.assertEqual(len(res["allocations"]), 4)

    def test_report_agent_output(self):
        agent = ReportAgent()
        mock_stock = {
            "score": 88.0,
            "confidence_pct": 90,
            "meta": {"ticker": "ITUB4", "name": "Itaú Unibanco", "sector": "Financeiro"},
            "tech": {"current_price": 35.00, "rsi_14": 42.0},
            "fund": {"dividend_yield": 6.8, "roe": 22.0, "pe_ratio": 7.8},
            "price_levels": {
                "current_price": 35.00,
                "entry_min": 34.20,
                "entry_max": 35.50,
                "target_price": 42.00,
                "potential_gain_pct": 20.0,
                "stop_loss_price": 32.80,
                "max_loss_pct": -6.3,
            }
        }
        report = agent.generate_stock_report(
            stock_item=mock_stock,
            macro_snapshot={"selic_rate": 13.75},
            macro_regime={"regime_name": "Juros Reais Elevados"}
        )
        self.assertIn("ITUB4", report["content"])
        self.assertIn("Tese de Investimento", report["content"])
        self.assertIn("Itaú", report["content"])

    def test_projection_engine(self):
        engine = ProjectionEngine()
        mock_allocations = [
            {
                "shares_count": 100,
                "invested_amount": 4000.0,
                "target_price": 48.0,
                "stop_loss_price": 37.5,
                "dividend_yield": 9.0
            },
            {
                "shares_count": 200,
                "invested_amount": 4000.0,
                "target_price": 24.0,
                "stop_loss_price": 18.8,
                "dividend_yield": 8.5
            }
        ]
        target_res = engine.calculate_target_realization(
            capital=20000.0,
            allocations=mock_allocations,
            cdi_annual_rate=13.75
        )
        self.assertEqual(target_res["target_value_stocks"], 9600.0)
        self.assertEqual(target_res["capital_gain_brl"], 1600.0)
        self.assertGreater(target_res["dividends_1y_brl"], 0.0)

        df_growth = engine.simulate_long_term_growth(
            initial_capital=20000.0,
            monthly_contribution=300.0,
            dividend_yield_annual=9.0,
            growth_annual=6.0,
            cdi_annual=13.75,
            years=3
        )
        self.assertGreater(len(df_growth), 0)
        self.assertGreater(df_growth.iloc[-1]["Carteira Ações"], df_growth.iloc[0]["Carteira Ações"])

        stress = engine.calculate_stress_test(
            capital=20000.0,
            allocations=mock_allocations,
            total_patrimony=100000.0
        )
        self.assertGreater(stress["reserve_capital"], 0.0)
        self.assertTrue(stress["reserve_covers_loss"])

    def test_monte_carlo_engine(self):
        engine = MonteCarloEngine(n_simulations=100, n_days=50)
        mock_allocations = [
            {"ticker": "ITUB4", "invested_amount": 10000.0},
            {"ticker": "BBAS3", "invested_amount": 10000.0}
        ]
        res = engine.run_simulation(mock_allocations, initial_capital=20000.0)
        self.assertIn("mean_final_value", res)
        self.assertIn("variance", res)
        self.assertGreater(res["mean_final_value"], 0.0)
        self.assertGreater(res["prob_profit_pct"], 0.0)
        self.assertIn("P50", res["percentiles_over_time"])

    def test_robustness_diagnostic(self):
        engine = RobustnessDiagnostic()
        mock_allocations = [
            {"ticker": "BBAS3", "name": "Banco do Brasil", "sector": "Financeiro", "weight_pct": 20.0, "score": 90, "confidence_pct": 90},
            {"ticker": "TAEE11", "name": "Taesa", "sector": "Utilities", "weight_pct": 20.0, "score": 86, "confidence_pct": 86},
            {"ticker": "BBSE3", "name": "BB Seguridade", "sector": "Financeiro", "weight_pct": 20.0, "score": 89, "confidence_pct": 89},
            {"ticker": "CXSE3", "name": "Caixa Seguridade", "sector": "Financeiro", "weight_pct": 20.0, "score": 88, "confidence_pct": 88},
            {"ticker": "ISAE4", "name": "ISA CTEEP", "sector": "Utilities", "weight_pct": 20.0, "score": 85, "confidence_pct": 85},
        ]
        res = engine.run_full_diagnosis(mock_allocations, {}, {})
        self.assertGreaterEqual(res["overall_robustness_score"], 80.0)
        self.assertEqual(res["hhi_index"], 2000)
        self.assertEqual(len(res["sensitivity_tests"]), 4)
        self.assertEqual(len(res["confidence_audit"]), 5)

    def test_opportunity_engine(self):
        engine = OpportunityEngine()
        opps = engine.scan_opportunities()
        self.assertGreater(len(opps), 0)
        top = opps[0]
        self.assertIn("ticker", top)
        self.assertIn("drawdown_pct", top)
        self.assertIn("turnaround_catalysts", top)
        self.assertIn("asymmetry_ratio", top)
        self.assertGreater(top["upside_pct"], 30.0)
        self.assertGreaterEqual(top["confidence_score"], 65.0)

if __name__ == "__main__":
    unittest.main()

