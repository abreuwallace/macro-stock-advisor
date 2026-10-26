"""
Motor de Projeções Financeiras e Simulações de Carteira.
Calcula o efeito dos preços-alvo, dividendos reinvestidos (efeito bola de neve),
comparativo com o CDI/Cofrinho e cenários de gestão de risco/stress test.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np

class ProjectionEngine:
    """Calcula projeções financeiras objetivas e simulações para a carteira de ações."""

    def calculate_target_realization(
        self,
        capital: float,
        allocations: List[Dict[str, Any]],
        cdi_annual_rate: float = 13.75
    ) -> Dict[str, Any]:
        """
        Calcula o cenário de realização de metas:
        O que acontece quando os ativos atingem o Preço-Alvo recomendado (+ Upside)
        somado aos Dividendos do período (6 a 12 meses).
        """
        total_invested = sum(a["invested_amount"] for a in allocations)
        total_target_value = sum(
            a["shares_count"] * a["target_price"] for a in allocations
        )
        capital_gain_brl = round(total_target_value - total_invested, 2)
        capital_gain_pct = round((capital_gain_brl / total_invested) * 100, 2) if total_invested > 0 else 0.0

        # Dividendos esperados em 1 ano (isentos de IR)
        dividends_1y_brl = round(
            sum(a["invested_amount"] * (a["dividend_yield"] / 100.0) for a in allocations), 2
        )
        dividend_yield_avg = round((dividends_1y_brl / total_invested) * 100, 2) if total_invested > 0 else 0.0

        total_final_equity = round(total_target_value + dividends_1y_brl, 2)
        total_return_brl = round(capital_gain_brl + dividends_1y_brl, 2)
        total_return_pct = round((total_return_brl / total_invested) * 100, 2) if total_invested > 0 else 0.0

        # Comparativo com o CDI líquido (100% CDI com alíquota de IR de 17.5% para 1 ano)
        cdi_net_rate = (cdi_annual_rate * 0.825) / 100.0
        cdi_gain_brl = round(total_invested * cdi_net_rate, 2)
        cdi_final_capital = round(total_invested + cdi_gain_brl, 2)

        alpha_brl = round(total_final_equity - cdi_final_capital, 2)

        return {
            "initial_capital": capital,
            "total_invested": total_invested,
            "target_value_stocks": round(total_target_value, 2),
            "capital_gain_brl": capital_gain_brl,
            "capital_gain_pct": capital_gain_pct,
            "dividends_1y_brl": dividends_1y_brl,
            "dividend_yield_avg": dividend_yield_avg,
            "total_final_equity": total_final_equity,
            "total_return_brl": total_return_brl,
            "total_return_pct": total_return_pct,
            "cdi_final_capital": cdi_final_capital,
            "cdi_gain_brl": cdi_gain_brl,
            "cdi_net_rate_pct": round(cdi_net_rate * 100, 2),
            "alpha_vs_cdi_brl": alpha_brl,
        }

    def simulate_long_term_growth(
        self,
        initial_capital: float = 20_000.00,
        monthly_contribution: float = 0.0,
        dividend_yield_annual: float = 9.0,
        growth_annual: float = 6.0,  # Crescimento real conservador dos lucros/cotação
        cdi_annual: float = 13.75,
        years: int = 5,
        reinvest_dividends: bool = True
    ) -> pd.DataFrame:
        """
        Simula a evolução patrimonial mês a mês ao longo de N anos.
        Compara Carteira Recomendada (com e sem reinvestimento) vs Cofrinho CDI.
        """
        months = years * 12
        monthly_div_rate = ((1 + (dividend_yield_annual / 100.0)) ** (1 / 12)) - 1
        monthly_growth_rate = ((1 + (growth_annual / 100.0)) ** (1 / 12)) - 1
        monthly_stock_total_rate = monthly_div_rate + monthly_growth_rate if reinvest_dividends else monthly_growth_rate

        # CDI mensal líquido de IR médio (~15% longo prazo)
        cdi_net_annual = (cdi_annual * 0.85) / 100.0
        monthly_cdi_rate = ((1 + cdi_net_annual) ** (1 / 12)) - 1

        records = []
        stock_equity = initial_capital
        cdi_equity = initial_capital
        accumulated_dividends = 0.0
        total_invested = initial_capital

        for m in range(months + 1):
            if m == 0:
                records.append({
                    "Mês": 0,
                    "Ano": 0.0,
                    "Total Aportado": total_invested,
                    "Carteira Ações": round(stock_equity, 2),
                    "Cofrinho CDI": round(cdi_equity, 2),
                    "Dividendo Mensal": 0.0,
                    "Dividendos Acumulados": 0.0,
                })
                continue

            # Aporte mensal
            total_invested += monthly_contribution
            stock_equity += monthly_contribution
            cdi_equity += monthly_contribution

            # Rendimento de ações
            div_month = stock_equity * monthly_div_rate
            accumulated_dividends += div_month

            if reinvest_dividends:
                stock_equity = (stock_equity * (1 + monthly_stock_total_rate))
            else:
                stock_equity = (stock_equity * (1 + monthly_growth_rate))

            # Rendimento CDI
            cdi_equity = cdi_equity * (1 + monthly_cdi_rate)

            if m % 6 == 0 or m == months:
                records.append({
                    "Mês": m,
                    "Ano": round(m / 12, 1),
                    "Total Aportado": round(total_invested, 2),
                    "Carteira Ações": round(stock_equity, 2),
                    "Cofrinho CDI": round(cdi_equity, 2),
                    "Dividendo Mensal": round(div_month, 2),
                    "Dividendos Acumulados": round(accumulated_dividends, 2),
                })

        return pd.DataFrame(records)

    def calculate_stress_test(
        self,
        capital: float,
        allocations: List[Dict[str, Any]],
        total_patrimony: float = 100_000.00
    ) -> Dict[str, Any]:
        """
        Simula o cenário de estresse (Pior caso):
        O que acontece se o mercado entrar em queda abrupta e os Stops forem disparados?
        Calcula a perda máxima controlada em R$ e o impacto no patrimônio total de R$ 100k.
        """
        total_invested = sum(a["invested_amount"] for a in allocations)
        total_stop_value = sum(
            a["shares_count"] * a["stop_loss_price"] for a in allocations
        )
        max_loss_brl = round(total_invested - total_stop_value, 2)
        max_loss_pct_stocks = round((max_loss_brl / total_invested) * 100, 2) if total_invested > 0 else 0.0
        impact_on_total_patrimony_pct = round((max_loss_brl / total_patrimony) * 100, 2)

        # Reserva de R$ 80.000 rendendo no cofrinho
        safe_reserve = total_patrimony - capital
        cdi_annual_gain_reserve = round(safe_reserve * (13.75 * 0.85 / 100.0), 2)

        net_patrimony_worst_case = round(
            (total_patrimony - max_loss_brl) + cdi_annual_gain_reserve, 2
        )

        return {
            "total_invested_stocks": total_invested,
            "max_loss_brl": max_loss_brl,
            "max_loss_pct_stocks": max_loss_pct_stocks,
            "impact_on_total_patrimony_pct": impact_on_total_patrimony_pct,
            "capital_preserved_stocks": round(total_stop_value, 2),
            "reserve_capital": safe_reserve,
            "reserve_annual_gain": cdi_annual_gain_reserve,
            "net_annual_patrimony_worst_case": net_patrimony_worst_case,
            "reserve_covers_loss": cdi_annual_gain_reserve > max_loss_brl,
        }
