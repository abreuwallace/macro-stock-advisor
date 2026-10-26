"""
Motor de Filtragem e Scoring Quantamental de Ações da B3.
Combina filtros fundamentalistas de segurança (ROE, P/L, DY, Balanço),
indicadores técnicos de timing (RSI, Suportes) e o regime macroeconômico.
"""
from typing import Dict, Any, List
import pandas as pd

class StockScreener:
    """Filtra e pontua as melhores ações da B3 priorizando segurança e assimetria positiva."""

    def score_stock(
        self,
        meta: Dict[str, Any],
        tech: Dict[str, Any],
        fund: Dict[str, Any],
        sector_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calcula uma pontuação composta (0 a 100) para cada ação."""
        score = 50.0  # Base score
        breakdown: Dict[str, float] = {}

        # 1. Bônus por Perfil Defensivo & Baixo Beta (Segurança de Capital)
        beta = meta.get("beta", 1.0)
        if beta <= 0.60:
            score += 15.0
            breakdown["Baixa Volatilidade (Beta baixo)"] = +15.0
        elif beta <= 0.85:
            score += 8.0
            breakdown["Volatilidade Moderada"] = +8.0
        else:
            score -= 5.0
            breakdown["Sensibilidade Cíclica Alta"] = -5.0

        if meta.get("is_defensive", False):
            score += 10.0
            breakdown["Setor Essencial / Defensivo"] = +10.0

        # 2. Retorno sobre Patrimônio Líquido (ROE)
        roe = fund.get("roe")
        if roe is not None:
            if roe >= 20.0:
                score += 12.0
                breakdown["Rentabilidade Excelente (ROE >= 20%)"] = +12.0
            elif roe >= 14.0:
                score += 7.0
                breakdown["Rentabilidade Sólida (ROE >= 14%)"] = +7.0
            elif roe < 8.0:
                score -= 10.0
                breakdown["Rentabilidade Baixa (ROE < 8%)"] = -10.0

        # 3. Dividend Yield (Segurança de Proventos)
        dy = fund.get("dividend_yield", 0.0)
        if dy >= 8.0:
            score += 14.0
            breakdown["Dividend Yield Alto (>= 8%)"] = +14.0
        elif dy >= 5.5:
            score += 9.0
            breakdown["Dividend Yield Atrativo (>= 5.5%)"] = +9.0
        elif dy >= 3.0:
            score += 4.0
            breakdown["Dividend Yield Moderado"] = +4.0

        # 4. Valuation (P/L)
        pe = fund.get("pe_ratio")
        if pe is not None and pe > 0:
            if pe <= 8.5:
                score += 10.0
                breakdown["Valuation com Desconto (P/L <= 8.5x)"] = +10.0
            elif pe <= 13.0:
                score += 5.0
                breakdown["Valuation Justo (P/L <= 13x)"] = +5.0
            elif pe > 25.0:
                score -= 8.0
                breakdown["Múltiplo Esticado (P/L > 25x)"] = -8.0

        # 5. Timing Técnico (RSI / IFR 14)
        rsi = tech.get("rsi_14", 50.0)
        if rsi <= 35.0:
            score += 10.0
            breakdown["Sobrevendido / Zona de Suporte Técnico"] = +10.0
        elif rsi <= 50.0:
            score += 5.0
            breakdown["Faixa Técnica Confortável para Entrada"] = +5.0
        elif rsi >= 70.0:
            score -= 10.0
            breakdown["Sobrecomprado (Risco de Correção Curto Prazo)"] = -10.0

        # 6. Alinhamento com o Regime Macroeconômico
        sector = meta.get("sector", "")
        multiplier = sector_weights.get(sector, 1.0)
        raw_score = score
        final_score = round(min(100.0, max(10.0, raw_score * multiplier)), 1)
        breakdown[f"Multiplicador Macro Setorial ({sector})"] = round((multiplier - 1.0) * raw_score, 1)

        # Nível de confiança correspondente (60% a 95%)
        confidence_pct = round(min(95, max(60, int(final_score * 0.95))), 0)

        return {
            "score": final_score,
            "confidence_pct": confidence_pct,
            "breakdown": breakdown,
            "is_recommended": final_score >= 68.0,
        }

    def rank_stocks(
        self,
        stocks_data: List[Dict[str, Any]],
        sector_weights: Dict[str, float],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """Processa a lista completa e retorna as top N ações recomendadas com pontuação."""
        scored_list = []
        for item in stocks_data:
            meta = item["meta"]
            tech = item["tech"]
            fund = item["fund"]
            score_res = self.score_stock(meta, tech, fund, sector_weights)

            combined = {
                **item,
                "score": score_res["score"],
                "confidence_pct": score_res["confidence_pct"],
                "score_breakdown": score_res["breakdown"],
                "is_recommended": score_res["is_recommended"]
            }
            scored_list.append(combined)

        # Ordena pela maior pontuação (maior segurança e potencial)
        ranked = sorted(scored_list, key=lambda x: x["score"], reverse=True)
        return ranked[:top_n]

