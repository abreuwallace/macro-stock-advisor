"""
Motor de Simulação de Monte Carlo para Análise de Média, Variância e Risco Estocástico.
Calcula quantis de probabilidade (P5 a P95), VaR 95%, probabilidade de lucro e
trajetórias estocásticas para o Cone de Incerteza da Carteira de R$ 20.000.
"""
import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

class MonteCarloEngine:
    """Executa simulações estocásticas de Monte Carlo para a carteira de ações."""

    def __init__(self, n_simulations: int = 1000, n_days: int = 252):
        self.n_simulations = n_simulations
        self.n_days = n_days  # 252 pregões = 1 ano de mercado

    def run_simulation(
        self,
        allocations: List[Dict[str, Any]],
        initial_capital: float = 20_000.0,
        cdi_annual: float = 13.75
    ) -> Dict[str, Any]:
        """
        Executa a simulação estocástica de Monte Carlo baseada no histórico real de retornos,
        volatilidades e correlações dos ativos da carteira recomendada.
        """
        if not allocations:
            return {}

        tickers_yf = [f"{a['ticker']}.SA" if not a['ticker'].endswith(".SA") else a['ticker'] for a in allocations]
        weights = np.array([a["invested_amount"] for a in allocations])
        total_inv = weights.sum()
        if total_inv > 0:
            weights = weights / total_inv
        else:
            weights = np.ones(len(allocations)) / len(allocations)

        # 1. Download de histórico de 1 ano para calcular retornos e covariância
        try:
            df = yf.download(tickers_yf, period="1y", progress=False)["Close"]
            df_returns = df.pct_change().dropna()
            
            # Alinhar ordem das colunas com os pesos
            aligned_returns = df_returns[[t for t in tickers_yf if t in df_returns.columns]]
            if aligned_returns.empty or aligned_returns.shape[1] < len(tickers_yf):
                # Fallback: aproximação pelos betas e volatilidade típica defensiva
                port_daily_ret = np.random.normal(0.0006, 0.011, 252)
                mean_daily = 0.0006
                std_daily = 0.011
            else:
                port_daily_ret = aligned_returns.dot(weights[:aligned_returns.shape[1]])
                mean_daily = port_daily_ret.mean()
                std_daily = port_daily_ret.std()

        except Exception as e:
            logger.warning(f"Erro ao calcular covariância empírica para Monte Carlo: {e}")
            mean_daily = 0.0006  # ~16% a.a.
            std_daily = 0.012   # ~19% a.a.

        # Anualização
        mu_annual = mean_daily * 252
        sigma_annual = std_daily * np.sqrt(252)

        # 2. Simulação Estocástica de Trajetórias (Geometric Brownian Motion)
        np.random.seed(42)  # Reprodutibilidade
        dt = 1.0 / 252.0
        drift = (mu_annual - 0.5 * (sigma_annual ** 2)) * dt
        shock = sigma_annual * np.sqrt(dt)

        paths = np.zeros((self.n_days + 1, self.n_simulations))
        paths[0] = initial_capital

        for t in range(1, self.n_days + 1):
            z = np.random.normal(0, 1, self.n_simulations)
            paths[t] = paths[t - 1] * np.exp(drift + shock * z)

        # 3. Estatísticas e Métricas da Distribuição Final
        end_values = paths[-1]
        returns_pct = ((end_values / initial_capital) - 1.0) * 100.0

        mean_val = float(np.mean(end_values))
        median_val = float(np.median(end_values))
        std_val = float(np.std(end_values))
        var_val = float(np.var(end_values))

        p5_val = float(np.percentile(end_values, 5))    # Pior 5% (VaR 95%)
        p25_val = float(np.percentile(end_values, 25))  # Cenário Conservador
        p50_val = median_val                            # Cenário Central
        p75_val = float(np.percentile(end_values, 75))  # Cenário Favorável
        p95_val = float(np.percentile(end_values, 95))  # Cenário Otimista

        # Value at Risk (VaR 95%) e Conditional VaR (Expected Shortfall)
        var_95_brl = round(initial_capital - p5_val, 2)
        var_95_pct = round((var_95_brl / initial_capital) * 100.0, 2)
        worst_5_pct = end_values[end_values <= p5_val]
        cvar_95_brl = round(initial_capital - np.mean(worst_5_pct), 2) if len(worst_5_pct) > 0 else var_95_brl

        # Probabilidades
        prob_profit = round(float((end_values > initial_capital).mean()) * 100.0, 1)
        cdi_target = initial_capital * (1 + (cdi_annual * 0.825 / 100.0))
        prob_beat_cdi = round(float((end_values > cdi_target).mean()) * 100.0, 1)

        # Curvas percentuais ao longo do tempo para o Fan Chart (Cone de Incerteza)
        percentiles_over_time = {
            "Day": list(range(0, self.n_days + 1, 10)) + [self.n_days],
            "P5": [float(np.percentile(paths[d], 5)) for d in (list(range(0, self.n_days + 1, 10)) + [self.n_days])],
            "P25": [float(np.percentile(paths[d], 25)) for d in (list(range(0, self.n_days + 1, 10)) + [self.n_days])],
            "P50": [float(np.percentile(paths[d], 50)) for d in (list(range(0, self.n_days + 1, 10)) + [self.n_days])],
            "P75": [float(np.percentile(paths[d], 75)) for d in (list(range(0, self.n_days + 1, 10)) + [self.n_days])],
            "P95": [float(np.percentile(paths[d], 95)) for d in (list(range(0, self.n_days + 1, 10)) + [self.n_days])],
        }

        return {
            "initial_capital": initial_capital,
            "n_simulations": self.n_simulations,
            "n_days": self.n_days,
            "mean_final_value": round(mean_val, 2),
            "median_final_value": round(median_val, 2),
            "variance": round(var_val, 2),
            "std_deviation_brl": round(std_val, 2),
            "volatility_annual_pct": round(sigma_annual * 100.0, 2),
            "expected_return_pct": round(((mean_val / initial_capital) - 1.0) * 100.0, 2),
            "p5_pessimistic": round(p5_val, 2),
            "p25_conservative": round(p25_val, 2),
            "p50_median": round(p50_val, 2),
            "p75_favorable": round(p75_val, 2),
            "p95_optimistic": round(p95_val, 2),
            "var_95_brl": var_95_brl,
            "var_95_pct": var_95_pct,
            "cvar_95_brl": cvar_95_brl,
            "prob_profit_pct": prob_profit,
            "prob_beat_cdi_pct": prob_beat_cdi,
            "percentiles_over_time": percentiles_over_time,
            "end_values_sample": end_values[:500].tolist()
        }

