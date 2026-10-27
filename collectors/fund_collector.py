"""
Coletor de Dados Fundamentalistas para Ações da B3.
Múltiplos de Valuation, Retorno sobre Patrimônio (ROE), Endividamento e Dividendos.
"""
import logging
import warnings
from typing import Dict, Any, Optional
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

class FundamentalCollector:
    """Coleta e normaliza múltiplos fundamentalistas de empresas da B3."""

    def get_stock_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Recupera indicadores fundamentalistas confiáveis:
        P/L, P/VP, ROE, Dividend Yield, Endividamento e Preço-Alvo de Consenso.
        """
        data: Dict[str, Any] = {
            "symbol": symbol,
            "pe_ratio": None,
            "pb_ratio": None,
            "dividend_yield": 0.0,
            "roe": None,
            "debt_to_equity": None,
            "analyst_target_price": None,
            "market_cap": None,
            "has_good_dividend": False,
            "is_financially_healthy": True,
        }

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}

            # Preço / Lucro (P/L)
            pe = info.get("trailingPE") or info.get("forwardPE")
            if pe and pe > 0:
                data["pe_ratio"] = round(float(pe), 2)

            # Preço / Valor Patrimonial (P/VP)
            pb = info.get("priceToBook")
            if pb and pb > 0:
                data["pb_ratio"] = round(float(pb), 2)

            # Retorno sobre Patrimônio Líquido (ROE)
            roe = info.get("returnOnEquity")
            if roe is not None:
                data["roe"] = round(float(roe) * 100, 2)  # Em %

            # Dividend Yield (%)
            # Calcula preferencialmente a soma dos proventos dos últimos 12 meses sobre o preço atual
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            try:
                dividends = ticker.dividends
                if not dividends.empty and current_price and current_price > 0:
                    # Soma proventos estritamente dos últimos 365 dias corridos
                    cutoff_date = dividends.index[-1] - pd.Timedelta(days=365)
                    last_1y_divs = float(dividends[dividends.index >= cutoff_date].sum())
                    dy_calc = (last_1y_divs / current_price) * 100.0
                    data["dividend_yield"] = round(min(22.0, dy_calc), 2)
            except Exception:
                pass

            # Fallback para dividendRate ou dividendYield do info
            if data["dividend_yield"] <= 0.5:
                dy_info = info.get("dividendYield")
                if dy_info is not None:
                    # yfinance às vezes reporta 0.08 para 8% ou 8.0
                    dy_val = float(dy_info)
                    data["dividend_yield"] = round(dy_val * 100 if dy_val < 1.0 else dy_val, 2)

            # Endividamento (Dívida / PL em %)
            debt_eq = info.get("debtToEquity")
            if debt_eq is not None:
                data["debt_to_equity"] = round(float(debt_eq), 1)

            # Consenso de Preço-Alvo dos analistas (Target Mean Price)
            target = info.get("targetMeanPrice")
            if target and target > 0:
                data["analyst_target_price"] = round(float(target), 2)

            # Valor de Mercado
            data["market_cap"] = info.get("marketCap")

            # Flags de Saúde para Perfil Conservador/Seguro:
            # Bom dividend yield: >= 5.0% ao ano
            data["has_good_dividend"] = data["dividend_yield"] >= 5.0
            # Alavancagem controlada (Dívida/PL < 200% ou nula para bancos)
            if data["debt_to_equity"] and data["debt_to_equity"] > 250:
                data["is_financially_healthy"] = False

        except Exception as e:
            logger.warning(f"Erro ao obter dados fundamentalistas de {symbol}: {e}")

        return data

if __name__ == "__main__":
    collector = FundamentalCollector()
    fund = collector.get_stock_fundamentals("EGIE3.SA")
    print("Múltiplos EGIE3:", fund)

