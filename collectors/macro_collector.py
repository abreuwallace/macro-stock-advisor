"""
Coletor de Dados Macroeconômicos para o Mercado Brasileiro.
Fontes: Banco Central do Brasil (BACEN SGS) e Yahoo Finance.
"""
import logging
import warnings
from typing import Dict, Any, Optional
import requests
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

class MacroCollector:
    """Coleta e consolida as principais variáveis macroeconômicas que balizam a Bolsa (B3)."""

    BACEN_SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados/ultimos/{n}?formato=json"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "MacroAdvisor/1.0"})

    def _fetch_bacen_series(self, code: int, n: int = 1) -> Optional[float]:
        """Recupera o último valor de uma série temporal do BACEN SGS."""
        try:
            url = self.BACEN_SGS_URL.format(code=code, n=n)
            res = self.session.get(url, timeout=6)
            if res.status_code == 200:
                data = res.json()
                if data and isinstance(data, list):
                    val_str = data[-1].get("valor", "").replace(",", ".")
                    return float(val_str)
        except Exception as e:
            logger.warning(f"Erro ao obter série BACEN {code}: {e}")
        return None

    def get_macro_snapshot(self) -> Dict[str, Any]:
        """
        Retorna um panorama consolidado dos indicadores macroeconômicos do Brasil
        e do cenário global (Selic, IPCA, Juro Real, Dólar, Brent, Ibovespa).
        """
        # 1. Indicadores Oficiais BACEN
        selic = self._fetch_bacen_series(432) or 10.50  # Selic Meta % a.a.
        ipca_12m = self._fetch_bacen_series(13522) or 4.20  # IPCA acumulado 12m %
        real_interest_rate = round(selic - ipca_12m, 2)  # Juro Real Ex-Post

        # 2. Indicadores de Mercado Financeiro (Yahoo Finance)
        market_tickers = ["USDBRL=X", "BZ=F", "^BVSP", "^TNX"]
        market_data: Dict[str, float] = {
            "usd_brl": 5.40,
            "brent_usd": 80.0,
            "ibov_points": 130000.0,
            "us_10y_yield": 4.20,
            "usd_change_pct": 0.0,
            "brent_change_pct": 0.0,
            "ibov_change_pct": 0.0
        }

        try:
            df = yf.download(market_tickers, period="5d", progress=False)
            if not df.empty and "Close" in df:
                close = df["Close"]
                if "USDBRL=X" in close and not close["USDBRL=X"].dropna().empty:
                    series = close["USDBRL=X"].dropna()
                    market_data["usd_brl"] = float(series.iloc[-1])
                    if len(series) >= 2:
                        market_data["usd_change_pct"] = round(float((series.iloc[-1] / series.iloc[-2] - 1) * 100), 2)

                if "BZ=F" in close and not close["BZ=F"].dropna().empty:
                    series = close["BZ=F"].dropna()
                    market_data["brent_usd"] = float(series.iloc[-1])
                    if len(series) >= 2:
                        market_data["brent_change_pct"] = round(float((series.iloc[-1] / series.iloc[-2] - 1) * 100), 2)

                if "^BVSP" in close and not close["^BVSP"].dropna().empty:
                    series = close["^BVSP"].dropna()
                    market_data["ibov_points"] = float(series.iloc[-1])
                    if len(series) >= 2:
                        market_data["ibov_change_pct"] = round(float((series.iloc[-1] / series.iloc[-2] - 1) * 100), 2)

                if "^TNX" in close and not close["^TNX"].dropna().empty:
                    series = close["^TNX"].dropna()
                    market_data["us_10y_yield"] = float(series.iloc[-1])
        except Exception as e:
            logger.warning(f"Erro ao obter dados de mercado via yfinance: {e}")

        # Sintetizar tudo em um dicionário claro e tipado
        snapshot = {
            "selic_rate": round(selic, 2),
            "ipca_12m": round(ipca_12m, 2),
            "real_rate": real_interest_rate,
            "usd_brl": round(market_data["usd_brl"], 3),
            "usd_change_pct": market_data["usd_change_pct"],
            "brent_usd": round(market_data["brent_usd"], 2),
            "brent_change_pct": market_data["brent_change_pct"],
            "ibov_points": round(market_data["ibov_points"], 0),
            "ibov_change_pct": market_data["ibov_change_pct"],
            "us_10y_yield": round(market_data["us_10y_yield"], 2),
        }

        return snapshot

if __name__ == "__main__":
    collector = MacroCollector()
    data = collector.get_macro_snapshot()
    print("Snapshot Macroeconômico:", data)

