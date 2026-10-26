"""
Coletor de Dados de Mercado e Indicadores Técnicos da B3.
Calcula médias móveis, RSI, volatilidade ATR e suportes em tempo real.
"""
import logging
import warnings
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

class MarketCollector:
    """Coleta cotações em tempo real e calcula indicadores técnicos e de volatilidade."""

    def __init__(self, period: str = "6mo"):
        self.period = period

    def get_stock_technical_metrics(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Recupera o histórico recente de um ativo da B3 e calcula:
        Preço Atual, RSI (14), EMA 21, SMA 50, ATR (14), Suportes e Resistências.
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=self.period)
            if hist.empty or len(hist) < 25:
                logger.warning(f"Histórico insuficiente para {symbol}")
                return None

            close = hist["Close"]
            high = hist["High"]
            low = hist["Low"]
            volume = hist["Volume"]

            current_price = float(close.iloc[-1])
            prev_close = float(close.iloc[-2]) if len(close) >= 2 else current_price
            daily_change_pct = round(((current_price / prev_close) - 1) * 100, 2)

            # Médias Móveis
            ema_21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])
            sma_50 = float(close.rolling(window=min(50, len(close))).mean().iloc[-1])
            sma_200 = float(close.rolling(window=min(200, len(close))).mean().iloc[-1]) if len(close) >= 50 else sma_50

            # RSI 14 (Índice de Força Relativa)
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss.replace(0, np.nan)
            rsi_series = 100.0 - (100.0 / (1.0 + rs))
            rsi_14 = float(rsi_series.dropna().iloc[-1]) if not rsi_series.dropna().empty else 50.0

            # ATR 14 (Average True Range) - Medida de volatilidade real em R$
            tr1 = high - low
            tr2 = (high - close.shift()).abs()
            tr3 = (low - close.shift()).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr_14 = float(tr.rolling(window=14).mean().dropna().iloc[-1]) if not tr.dropna().empty else (current_price * 0.025)

            # 52 Semanas (Mínimo e Máximo)
            high_52w = float(high.max())
            low_52w = float(low.min())

            # Suporte e Resistência recentes (últimos 30 pregões)
            recent_lows = low.tail(30)
            recent_highs = high.tail(30)
            support_price = float(recent_lows.min())
            resistance_price = float(recent_highs.max())

            # Volume financeiro médio diário estimado (R$)
            avg_volume_shares = float(volume.tail(20).mean())
            avg_financial_volume = avg_volume_shares * current_price

            return {
                "symbol": symbol,
                "current_price": round(current_price, 2),
                "daily_change_pct": daily_change_pct,
                "ema_21": round(ema_21, 2),
                "sma_50": round(sma_50, 2),
                "sma_200": round(sma_200, 2),
                "rsi_14": round(rsi_14, 1),
                "atr_14": round(atr_14, 2),
                "high_52w": round(high_52w, 2),
                "low_52w": round(low_52w, 2),
                "support_price": round(support_price, 2),
                "resistance_price": round(resistance_price, 2),
                "avg_financial_volume": avg_financial_volume,
                "is_near_support": current_price <= (support_price * 1.05),
                "is_oversold": rsi_14 < 40.0,
            }

        except Exception as e:
            logger.error(f"Erro ao processar métricas técnicas de {symbol}: {e}")
            return None

if __name__ == "__main__":
    collector = MarketCollector()
    metrics = collector.get_stock_technical_metrics("ITUB4.SA")
    print("Métricas Técnicas ITUB4:", metrics)

