"""
Motor de Backtesting Histórico e Validação Empírica (B3).
Avalia o desempenho real da estratégia recomendada em múltiplos cenários históricos
(1 Ano, 2 Anos, 3 Anos e 5 Anos) utilizando cotações oficiais ajustadas por dividendos.
Calcula métricas generalizadas: CAGR, Alpha, Sharpe, Sortino, Calmar, Max Drawdown,
Beta Realizado, Win Rate Mensal e Profit Factor.
"""
import logging
import warnings
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


class BacktestEngine:
    """Executa backtesting histórico multi-cenário sem viés comercial sobre dados reais da B3."""

    SCENARIOS = {
        "1 Ano (252 pregões — Ciclo Atual de Juros Altos)": 252,
        "2 Anos (504 pregões — Transição Monetária e Fiscal)": 504,
        "3 Anos (756 pregões — Ciclo de Aperto e Desinflação)": 756,
        "5 Anos (1.248 pregões — Ciclo Completo Multi-Regime)": 1248,
    }

    def __init__(self, initial_capital: float = 20_000.0):
        self.initial_capital = initial_capital

    def _compute_scenario_metrics(
        self,
        df_sub: pd.DataFrame,
        tickers_yf: List[str],
        weights: np.ndarray,
        cdi_annual_avg: float = 11.5
    ) -> Dict[str, Any]:
        """Calcula todas as métricas institucionais de backtest para uma janela temporal."""
        available_tickers = [t for t in tickers_yf if t in df_sub.columns]
        if not available_tickers or "^BVSP" not in df_sub.columns:
            return {}

        w = weights[:len(available_tickers)]
        w = w / w.sum() if w.sum() > 0 else np.ones(len(available_tickers)) / len(available_tickers)

        ret_stocks = df_sub[available_tickers].pct_change().dropna()
        ret_ibov = df_sub["^BVSP"].pct_change().dropna()

        # Alinhar índices
        common_idx = ret_stocks.index.intersection(ret_ibov.index)
        ret_stocks = ret_stocks.loc[common_idx]
        ret_ibov = ret_ibov.loc[common_idx]

        if len(common_idx) < 20:
            return {}

        port_daily_ret = ret_stocks.dot(w)
        n_days = len(port_daily_ret)

        # Curva diária do CDI (taxa livre de risco líquida aproximada)
        cdi_daily = ((1.0 + (cdi_annual_avg * 0.85 / 100.0)) ** (1.0 / 252.0)) - 1.0
        cdi_series = pd.Series(cdi_daily, index=common_idx)

        # Curvas acumuladas (base = 1.0)
        cum_port = (1.0 + port_daily_ret).cumprod()
        cum_ibov = (1.0 + ret_ibov).cumprod()
        cum_cdi = (1.0 + cdi_series).cumprod()

        # Evolução em R$ (partindo de R$ 20.000)
        equity_port = cum_port * self.initial_capital
        equity_ibov = cum_ibov * self.initial_capital
        equity_cdi = cum_cdi * self.initial_capital

        # Retornos totais (%)
        total_return_port_pct = round(float((cum_port.iloc[-1] - 1.0) * 100.0), 2)
        total_return_ibov_pct = round(float((cum_ibov.iloc[-1] - 1.0) * 100.0), 2)
        total_return_cdi_pct = round(float((cum_cdi.iloc[-1] - 1.0) * 100.0), 2)

        final_capital_port = round(float(equity_port.iloc[-1]), 2)
        final_capital_ibov = round(float(equity_ibov.iloc[-1]), 2)
        final_capital_cdi = round(float(equity_cdi.iloc[-1]), 2)

        alpha_vs_ibov_pct = round(total_return_port_pct - total_return_ibov_pct, 2)
        alpha_vs_cdi_pct = round(total_return_port_pct - total_return_cdi_pct, 2)

        # CAGR (Retorno Anualizado Composto)
        years_frac = max(n_days / 252.0, 0.1)
        cagr_port_pct = round(float(((cum_port.iloc[-1]) ** (1.0 / years_frac) - 1.0) * 100.0), 2)
        cagr_ibov_pct = round(float(((cum_ibov.iloc[-1]) ** (1.0 / years_frac) - 1.0) * 100.0), 2)

        # Volatilidade Anualizada
        vol_port_pct = round(float(port_daily_ret.std() * np.sqrt(252) * 100.0), 2)
        vol_ibov_pct = round(float(ret_ibov.std() * np.sqrt(252) * 100.0), 2)

        # Drawdown (Queda do topo)
        dd_series_port = ((cum_port / cum_port.cummax()) - 1.0) * 100.0
        dd_series_ibov = ((cum_ibov / cum_ibov.cummax()) - 1.0) * 100.0
        max_dd_port_pct = round(float(dd_series_port.min()), 2)
        max_dd_ibov_pct = round(float(dd_series_ibov.min()), 2)

        # Sharpe Ratio, Sortino Ratio e Calmar Ratio
        rf_annual = cdi_annual_avg * 0.85
        sharpe = round((cagr_port_pct - rf_annual) / vol_port_pct, 2) if vol_port_pct > 0 else 0.0

        downside_ret = port_daily_ret[port_daily_ret < 0]
        downside_vol_pct = float(downside_ret.std() * np.sqrt(252) * 100.0) if len(downside_ret) > 2 else vol_port_pct
        sortino = round((cagr_port_pct - rf_annual) / downside_vol_pct, 2) if downside_vol_pct > 0 else 0.0

        calmar = round(cagr_port_pct / abs(max_dd_port_pct), 2) if max_dd_port_pct != 0 else 0.0

        # Beta Realizado vs Ibovespa
        cov_matrix = np.cov(port_daily_ret, ret_ibov)
        var_ibov = np.var(ret_ibov)
        realized_beta = round(float(cov_matrix[0, 1] / var_ibov), 2) if var_ibov > 0 else 0.55

        # Métricas Mensais (Win Rate e Profit Factor)
        monthly_ret = port_daily_ret.resample("ME").apply(lambda x: (1.0 + x).prod() - 1.0)
        if len(monthly_ret) == 0:
            monthly_ret = port_daily_ret
        win_months = (monthly_ret > 0).sum()
        win_rate_monthly_pct = round(float((win_months / len(monthly_ret)) * 100.0), 1) if len(monthly_ret) > 0 else 60.0

        gross_gains = float(monthly_ret[monthly_ret > 0].sum())
        gross_losses = abs(float(monthly_ret[monthly_ret < 0].sum()))
        profit_factor = round(gross_gains / gross_losses, 2) if gross_losses > 0 else 2.50

        # Desempenho individual por ativo na janela
        asset_breakdown = []
        for idx, t_yf in enumerate(available_tickers):
            s_ret = (df_sub[t_yf].iloc[-1] / df_sub[t_yf].iloc[0] - 1.0) * 100.0
            s_vol = ret_stocks[t_yf].std() * np.sqrt(252) * 100.0
            s_cum = (1.0 + ret_stocks[t_yf]).cumprod()
            s_dd = ((s_cum / s_cum.cummax()) - 1.0).min() * 100.0
            asset_breakdown.append({
                "ticker": t_yf.replace(".SA", ""),
                "weight_pct": round(float(w[idx] * 100.0), 1),
                "total_return_pct": round(float(s_ret), 1),
                "volatility_pct": round(float(s_vol), 1),
                "max_drawdown_pct": round(float(s_dd), 1),
            })

        # Séries temporais para gráficos
        curves_df = pd.DataFrame({
            "Data": common_idx,
            "Carteira Recomendada (R$)": equity_port.values,
            "Ibovespa (R$)": equity_ibov.values,
            "CDI Líquido (R$)": equity_cdi.values,
            "Drawdown Carteira (%)": dd_series_port.values,
            "Drawdown Ibovespa (%)": dd_series_ibov.values,
        })

        return {
            "n_days": n_days,
            "initial_capital": self.initial_capital,
            "final_capital_port": final_capital_port,
            "final_capital_ibov": final_capital_ibov,
            "final_capital_cdi": final_capital_cdi,
            "total_return_port_pct": total_return_port_pct,
            "total_return_ibov_pct": total_return_ibov_pct,
            "total_return_cdi_pct": total_return_cdi_pct,
            "alpha_vs_ibov_pct": alpha_vs_ibov_pct,
            "alpha_vs_cdi_pct": alpha_vs_cdi_pct,
            "cagr_port_pct": cagr_port_pct,
            "cagr_ibov_pct": cagr_ibov_pct,
            "vol_port_pct": vol_port_pct,
            "vol_ibov_pct": vol_ibov_pct,
            "max_dd_port_pct": max_dd_port_pct,
            "max_dd_ibov_pct": max_dd_ibov_pct,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "calmar_ratio": calmar,
            "realized_beta": realized_beta,
            "win_rate_monthly_pct": win_rate_monthly_pct,
            "profit_factor": profit_factor,
            "asset_breakdown": asset_breakdown,
            "curves_df": curves_df,
        }

    def run_multi_scenario_backtest(
        self,
        allocations: List[Dict[str, Any]],
        cdi_annual_avg: float = 11.5
    ) -> Dict[str, Any]:
        """
        Executa o backtesting completo em todos os 4 cenários históricos (1A, 2A, 3A e 5A)
        e gera um diagnóstico generalizado do método.
        """
        if not allocations:
            return {}

        tickers_yf = [
            f"{a['ticker']}.SA" if not a["ticker"].endswith(".SA") else a["ticker"]
            for a in allocations
        ]
        weights = np.array([a["invested_amount"] for a in allocations], dtype=float)

        try:
            df_all = yf.download(tickers_yf + ["^BVSP"], period="5y", progress=False)["Close"]
            df_all = df_all.dropna(how="all").ffill().dropna()
        except Exception as e:
            logger.error(f"Erro ao baixar histórico de 5 anos para backtest: {e}")
            return {}

        if df_all.empty:
            return {}

        scenarios_results: Dict[str, Dict[str, Any]] = {}
        summary_rows: List[Dict[str, Any]] = []

        for label, days in self.SCENARIOS.items():
            df_sub = df_all.tail(min(days, len(df_all)))
            metrics = self._compute_scenario_metrics(df_sub, tickers_yf, weights, cdi_annual_avg)
            if metrics:
                scenarios_results[label] = metrics
                summary_rows.append({
                    "Cenário Histórico": label,
                    "Saldo Final (R$ 20k)": f"R$ {metrics['final_capital_port']:,.2f}",
                    "Retorno Carteira": f"{metrics['total_return_port_pct']:+.1f}%",
                    "Retorno Ibovespa": f"{metrics['total_return_ibov_pct']:+.1f}%",
                    "Alpha vs Ibov": f"{metrics['alpha_vs_ibov_pct']:+.1f}% p.p.",
                    "CAGR (% a.a.)": f"{metrics['cagr_port_pct']:.1f}%",
                    "Volatilidade": f"{metrics['vol_port_pct']:.1f}%",
                    "Max Drawdown": f"{metrics['max_dd_port_pct']:.1f}%",
                    "Drawdown Ibov": f"{metrics['max_dd_ibov_pct']:.1f}%",
                    "Sharpe": f"{metrics['sharpe_ratio']:.2f}",
                    "Sortino": f"{metrics['sortino_ratio']:.2f}",
                    "Win Rate Mensal": f"{metrics['win_rate_monthly_pct']:.0f}%",
                })

        if not scenarios_results:
            return {}

        # Métricas Generalizadas (Média/Consolidação de todos os cenários)
        all_Filter = list(scenarios_results.values())
        avg_cagr = round(float(np.mean([m["cagr_port_pct"] for m in all_Filter])), 2)
        avg_vol = round(float(np.mean([m["vol_port_pct"] for m in all_Filter])), 2)
        avg_sharpe = round(float(np.mean([m["sharpe_ratio"] for m in all_Filter])), 2)
        avg_sortino = round(float(np.mean([m["sortino_ratio"] for m in all_Filter])), 2)
        avg_win_rate = round(float(np.mean([m["win_rate_monthly_pct"] for m in all_Filter])), 1)
        avg_profit_factor = round(float(np.mean([m["profit_factor"] for m in all_Filter])), 2)
        avg_beta = round(float(np.mean([m["realized_beta"] for m in all_Filter])), 2)
        worst_dd_port = round(float(min(m["max_dd_port_pct"] for m in all_Filter)), 2)
        worst_dd_ibov = round(float(min(m["max_dd_ibov_pct"] for m in all_Filter)), 2)

        # Resultado de longo prazo (5 Anos)
        long_term_key = list(scenarios_results.keys())[-1]
        lt_metrics = scenarios_results[long_term_key]

        generalized_summary = {
            "avg_cagr_pct": avg_cagr,
            "avg_volatility_pct": avg_vol,
            "avg_sharpe_ratio": avg_sharpe,
            "avg_sortino_ratio": avg_sortino,
            "avg_win_rate_monthly_pct": avg_win_rate,
            "avg_profit_factor": avg_profit_factor,
            "avg_realized_beta": avg_beta,
            "worst_drawdown_port_pct": worst_dd_port,
            "worst_drawdown_ibov_pct": worst_dd_ibov,
            "five_year_return_pct": lt_metrics["total_return_port_pct"],
            "five_year_final_brl": lt_metrics["final_capital_port"],
            "five_year_alpha_ibov_pct": lt_metrics["alpha_vs_ibov_pct"],
        }

        return {
            "scenarios": scenarios_results,
            "summary_table": summary_rows,
            "generalized": generalized_summary,
        }


if __name__ == "__main__":
    mock_alloc = [
        {"ticker": "CXSE3", "invested_amount": 4000.0},
        {"ticker": "TAEE11", "invested_amount": 4000.0},
        {"ticker": "ISAE4", "invested_amount": 4000.0},
        {"ticker": "BBSE3", "invested_amount": 4000.0},
        {"ticker": "BBAS3", "invested_amount": 4000.0},
    ]
    bt = BacktestEngine(initial_capital=20_000.0)
    res = bt.run_multi_scenario_backtest(mock_alloc)
    print("Generalized Metrics:", res["generalized"])
    for row in res["summary_table"]:
        print(row)
